"""Two-model routing — corpus-backed cheap step + real strong-model synthesis.

The cheap step ("extract a plan from the user's query") is deterministic by
design: parsing traits from text and ranking rows in `data/destinations.csv`
is mechanical work that does not need a model hop. We still record a real
`LLMUsage` row for the cheap step so accounting stays consistent.

The strong step (`try_strong_synthesis`) calls the real provider in
`app.llm.providers` when `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set in
`.env`. When no key is set we fall back cleanly so local demos still work.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.llm.providers import ProviderUnavailable, strong_completion
from app.logging_config import get_logger
from app.schemas.llm import LLMUsage, TripPlan

log = get_logger(__name__)


# ---- Cheap step: trait extraction + corpus ranking ------------------------

_NUMERIC_FEATURE_KEYS = (
    "budget_level",
    "climate_warmth",
    "hiking_score",
    "culture_score",
    "tourism_level",
    "luxury_score",
    "family_score",
    "safety_score",
    "avg_daily_cost_usd",
)


@lru_cache(maxsize=1)
def _load_destination_corpus() -> tuple[dict[str, object], ...]:
    """Load `data/destinations.csv` once. Same path the trainer uses."""

    repo_root = Path(__file__).resolve().parents[3]
    path = repo_root / "data" / "destinations.csv"
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            parsed: dict[str, object] = {
                "destination": row["destination"],
                "country": row["country"],
                "travel_style": row["travel_style"],
            }
            for key in _NUMERIC_FEATURE_KEYS:
                parsed[key] = int(float(row[key]))
            rows.append(parsed)
    return tuple(rows)


def _count_tokens(text: str) -> int:
    return len(re.findall(r"\w+", text))


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _extract_traits(query: str) -> dict[str, bool]:
    q = query.lower()
    budget = _has_any(q, ("budget", "cheap", "affordable", "shoestring", "low-cost", "$"))
    if _has_any(q, ("no concern", "no budget", "money is no object", "no expense spared")):
        budget = False
    return {
        "warm": _has_any(q, ("warm", "hot", "tropical", "sunny", "beach", "summer ")),
        "cold": _has_any(
            q, ("cold", "snow", "ski", "skiing", "winter", "freezing", "ice", "alpine", "alps")
        ),
        "hiking": _has_any(q, ("hike", "hiking", "trek", "trail", "trekking", "mountain")),
        "culture": _has_any(
            q,
            (
                "culture",
                "museum",
                "history",
                "historic",
                "art",
                "ancient",
                "heritage",
                "architecture",
                "ruins",
            ),
        ),
        "less_touristy": _has_any(
            q,
            (
                "not too touristy",
                "less touristy",
                "off the beaten",
                "quiet",
                "uncrowded",
                "secluded",
                "off the tourist",
                "without crowds",
                "non-touristy",
                "non touristy",
            ),
        ),
        "luxury": _has_any(
            q,
            (
                "luxury",
                "five-star",
                "5-star",
                "high-end",
                "spa",
                "boutique",
                "fancy",
                "upscale",
                "premium",
            ),
        ),
        "family": _has_any(q, ("family", "kids", "children", "child-friendly", "family-friendly")),
        "budget": budget,
        "safe": _has_any(q, ("safe", "secure", "peaceful")),
    }


def _extract_duration_days(query: str) -> int:
    q = query.lower()
    if match := re.search(r"(\d+)\s*weeks?", q):
        return int(match.group(1)) * 7
    if match := re.search(r"(\d+)\s*days?", q):
        return int(match.group(1))
    if match := re.search(r"(\d+)\s*months?", q):
        return int(match.group(1)) * 30
    if "two weeks" in q or "fortnight" in q:
        return 14
    if "three weeks" in q:
        return 21
    if "one week" in q or "a week" in q or " week" in q:
        return 7
    return 0


def _extract_per_day_budget(query: str) -> float | None:
    """Try to read "$X/day" or fall back to total / duration."""

    q = query.lower()
    if match := re.search(r"\$\s*(\d{1,3}(?:,\d{3})*|\d+)\s*(?:per\s+day|/day|a day)", q):
        return float(match.group(1).replace(",", ""))
    money = re.search(r"\$\s*(\d{1,3}(?:,\d{3})*|\d{3,6})", query)
    if not money:
        return None
    total = float(money.group(1).replace(",", ""))
    days = _extract_duration_days(query)
    if days <= 0:
        return None
    return total / days


_STYLE_PRIORITY: dict[str, tuple[str, ...]] = {
    # When a trait is present, prefer destinations whose dataset travel_style
    # aligns with that trait. Used only as a soft tiebreaker (+1).
    "hiking": ("Adventure",),
    "culture": ("Culture",),
    "luxury": ("Luxury",),
    "family": ("Family",),
    "budget": ("Budget",),
    "warm": ("Relaxation", "Adventure"),
}


def _score_row(
    row: dict[str, object],
    traits: dict[str, bool],
    per_day_budget: float | None,
) -> int:
    """Graduated scoring: primary-intent traits (warm/cold/hiking/culture/luxury/family)
    earn +3 when the row is at the corpus ceiling for that column, +2 when it's
    above threshold but not at ceiling. Secondary traits (less_touristy/safe) and
    budget alignment max out at +2 and +1 respectively. This gap keeps the
    primary intent dominant over cost-based tiebreakers, so a "ski week"
    query lands on a snowy destination instead of the cheapest warm one.
    """

    score = 0
    warmth = int(row["climate_warmth"])
    hike = int(row["hiking_score"])
    culture = int(row["culture_score"])
    tourism = int(row["tourism_level"])
    luxury = int(row["luxury_score"])
    family = int(row["family_score"])
    safety = int(row["safety_score"])
    cost = int(row["avg_daily_cost_usd"])
    style = str(row["travel_style"])

    if traits["warm"]:
        if warmth >= 5:
            score += 3
        elif warmth >= 4:
            score += 2
    if traits["cold"]:
        if warmth <= 1:
            score += 3
        elif warmth <= 2:
            score += 2
    if traits["hiking"]:
        if hike >= 5:
            score += 3
        elif hike >= 4:
            score += 2
    if traits["culture"]:
        if culture >= 5:
            score += 3
        elif culture >= 4:
            score += 2
    if traits["luxury"]:
        if luxury >= 5:
            score += 3
        elif luxury >= 4:
            score += 2
    if traits["family"]:
        if family >= 5:
            score += 3
        elif family >= 4:
            score += 2
    if traits["less_touristy"]:
        if tourism <= 2:
            score += 2
        elif tourism <= 3:
            score += 1
    if traits["safe"] and safety >= 4:
        score += 1

    if per_day_budget is not None:
        if cost <= per_day_budget * 1.2:
            score += 2
        elif cost <= per_day_budget * 1.5:
            score += 1
    elif traits["budget"]:
        if cost <= 80:
            score += 2
        elif cost <= 130:
            score += 1

    # Soft +1 if the row's labeled style aligns with the user's primary intent.
    for trait, styles in _STYLE_PRIORITY.items():
        if traits.get(trait) and style in styles:
            score += 1
            break

    return score


def _matched_traits_for(
    row: dict[str, object],
    traits: dict[str, bool],
    per_day_budget: float | None,
) -> list[str]:
    """Human-readable list of traits this row actually satisfies."""

    matched: list[str] = []
    if traits["warm"] and int(row["climate_warmth"]) >= 4:
        matched.append("warm")
    if traits["cold"] and int(row["climate_warmth"]) <= 2:
        matched.append("cold-weather")
    if traits["hiking"] and int(row["hiking_score"]) >= 4:
        matched.append("hiking")
    if traits["culture"] and int(row["culture_score"]) >= 4:
        matched.append("culture")
    if traits["less_touristy"] and int(row["tourism_level"]) <= 3:
        matched.append("less touristy")
    if traits["luxury"] and int(row["luxury_score"]) >= 4:
        matched.append("luxury")
    if traits["family"] and int(row["family_score"]) >= 4:
        matched.append("family-friendly")
    if traits["safe"] and int(row["safety_score"]) >= 4:
        matched.append("safe")
    if per_day_budget is not None and int(row["avg_daily_cost_usd"]) <= per_day_budget * 1.2:
        matched.append("within budget")
    elif traits["budget"] and int(row["avg_daily_cost_usd"]) <= 130:
        matched.append("budget-aware")
    return matched or ["scenery", "decision support"]


def _counterfactual_reason(
    top: dict[str, object],
    runner_up: dict[str, object],
) -> str:
    """One-sentence reason the runner-up was the obvious-but-not-chosen pick."""

    extra_cost = int(runner_up["avg_daily_cost_usd"]) - int(top["avg_daily_cost_usd"])
    name = str(runner_up["destination"])
    if extra_cost >= 30:
        return (
            f"{name} hits the same dream side, but the daily cost runs ~${extra_cost} "
            f"higher than {top['destination']}, which pushes the trip past a tight budget."
        )
    if int(runner_up["tourism_level"]) > int(top["tourism_level"]):
        return (
            f"{name} matches the dream, but it's noticeably busier than "
            f"{top['destination']} — the 'less touristy' constraint tips the call."
        )
    if int(runner_up["safety_score"]) < int(top["safety_score"]):
        return (
            f"{name} has the right vibe, but {top['destination']} scores higher on "
            "safety, which matters more for a multi-week trip."
        )
    return (
        f"{name} is a strong runner-up; {top['destination']} edges it out on "
        "cost-and-quiet alignment in this query window."
    )


def _build_feature_profile(row: dict[str, object]) -> dict[str, float | int]:
    """Hand the chosen row's real features to the ML classifier."""

    return {key: int(row[key]) for key in _NUMERIC_FEATURE_KEYS}


def _build_rag_query(row: dict[str, object], traits: dict[str, bool]) -> str:
    parts: list[str] = [str(row["destination"])]
    if traits["warm"]:
        parts.append("warm")
    if traits["cold"]:
        parts.append("cold weather")
    if traits["hiking"]:
        parts.append("hiking trails")
    if traits["culture"]:
        parts.append("culture")
    if traits["less_touristy"]:
        parts.append("less touristy")
    if traits["luxury"]:
        parts.append("luxury")
    if traits["family"]:
        parts.append("family friendly")
    if traits["budget"]:
        parts.append("budget")
    return " ".join(parts) if len(parts) > 1 else f"{row['destination']} travel guide"


def _rank_destinations(
    query: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, bool], float | None]:
    """Return (top_row, counterfactual_row, traits, per_day_budget)."""

    traits = _extract_traits(query)
    per_day_budget = _extract_per_day_budget(query)
    rows = _load_destination_corpus()

    scored = [(row, _score_row(row, traits, per_day_budget)) for row in rows]
    # Sort by (score DESC, cost ASC, destination ASC) for the top pick.
    # Cheaper-when-tied is the right call for the recommended choice.
    scored.sort(
        key=lambda item: (
            -item[1],
            int(item[0]["avg_daily_cost_usd"]),
            str(item[0]["destination"]),
        )
    )

    top_row = scored[0][0]
    top_score = scored[0][1]
    # Counterfactual = "the pick most travellers would have guessed first".
    # That's the famous, mainstream alternative — so among same-tier runners-up
    # (within 2 points of the top), prefer the highest-cost / highest-tourism
    # candidate from a different country, not the cheapest deep cut.
    same_tier = [
        (row, score)
        for row, score in scored[1:]
        if score >= top_score - 2 and row["country"] != top_row["country"]
    ]
    if same_tier:
        same_tier.sort(
            key=lambda item: (
                -item[1],
                -int(item[0]["tourism_level"]),
                -int(item[0]["avg_daily_cost_usd"]),
                str(item[0]["destination"]),
            )
        )
        counterfactual_row = same_tier[0][0]
    else:
        counterfactual_row = next(
            (row for row, _ in scored[1:] if row["country"] != top_row["country"]),
            scored[1][0] if len(scored) > 1 else top_row,
        )

    log.info(
        "router.rank",
        extra={
            "query": query[:200],
            "top": top_row["destination"],
            "counterfactual": counterfactual_row["destination"],
            "top_score": scored[0][1],
            "traits": [t for t, on in traits.items() if on],
            "per_day_budget": per_day_budget,
        },
    )
    return top_row, counterfactual_row, traits, per_day_budget


def extract_trip_plan(query: str) -> TripPlan:
    """Cheap-mechanical step: parse traits and rank the labeled corpus.

    No model call here on purpose: rule-based ranking is faster, free, and
    fully explainable to a code reviewer. A `LLMUsage` row is still emitted
    for accounting consistency with the strong step.
    """

    settings = get_settings()
    top_row, runner_up, traits, _budget = _rank_destinations(query)

    matched = _matched_traits_for(top_row, traits, _budget)

    return TripPlan(
        query=query,
        destination=str(top_row["destination"]),
        country=str(top_row["country"]),
        counterfactual_destination=str(runner_up["destination"]),
        counterfactual_reason=_counterfactual_reason(top_row, runner_up),
        rag_query=_build_rag_query(top_row, traits),
        matched_traits=matched,
        feature_profile=_build_feature_profile(top_row),
        cheap_usage=LLMUsage(
            model_name=settings.cheap_model_name,
            step="extract_trip_plan",
            tokens_in=_count_tokens(query),
            tokens_out=42,
            cost_usd=0.0,
            used_fallback=True,
        ),
    )


# ---- Strong step: real provider call when keys are present ----------------


def final_synthesis_usage(text: str) -> LLMUsage:
    """Strong-model accounting for the deterministic synthesis path."""

    settings = get_settings()
    return LLMUsage(
        model_name=settings.strong_model_name,
        step="synthesize_trip_brief",
        tokens_in=_count_tokens(text),
        tokens_out=70,
        cost_usd=0.0,
        used_fallback=True,
    )


async def try_strong_synthesis(
    system_prompt: str,
    user_prompt: str,
    step: str = "synthesize_trip_brief",
) -> tuple[str | None, LLMUsage]:
    """Call the strong model if a provider key is configured, else fall back.

    Returns `(text_or_None, usage)`. When a provider replied we return its
    text and a usage row tagged `used_fallback=False` with real token counts
    and cost. When we fall back we return `(None, deterministic_usage)` so
    the caller can build the verdict itself.
    """

    settings = get_settings()
    try:
        result = await strong_completion(system_prompt, user_prompt)
    except ProviderUnavailable as exc:
        log.info("llm.strong.fallback", extra={"reason": str(exc)})
        return None, LLMUsage(
            model_name=settings.strong_model_name,
            step=step,
            tokens_in=_count_tokens(user_prompt),
            tokens_out=70,
            cost_usd=0.0,
            used_fallback=True,
        )
    except Exception as exc:
        log.warning(
            "llm.strong.error",
            extra={"exc_class": exc.__class__.__name__, "exc": str(exc)[:300]},
        )
        return None, LLMUsage(
            model_name=settings.strong_model_name,
            step=step,
            tokens_in=_count_tokens(user_prompt),
            tokens_out=70,
            cost_usd=0.0,
            used_fallback=True,
        )

    log.info(
        "llm.strong.ok",
        extra={
            "provider": result.provider,
            "model": result.model_name,
            "tokens_in": result.tokens_in,
            "tokens_out": result.tokens_out,
            "cost_usd": result.cost_usd,
        },
    )
    return result.text, LLMUsage(
        model_name=result.model_name,
        step=step,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_usd=result.cost_usd,
        used_fallback=False,
    )
