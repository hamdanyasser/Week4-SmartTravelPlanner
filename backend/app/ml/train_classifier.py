"""Train the travel-style classifier.

What this script does, in beginner-friendly terms:

  1. Loads the hand-labeled dataset from `data/destinations.csv`.
  2. Builds three scikit-learn Pipelines (StandardScaler -> classifier):
       - Logistic Regression
       - Random Forest
       - Gradient Boosting
  3. Evaluates each with 5-fold *stratified* cross-validation, reporting
     accuracy and macro-F1 (mean +/- standard deviation).
  4. Tunes Random Forest with GridSearchCV (justified in the README).
  5. Prints a per-class classification report on cross-validated
     predictions of the tuned model — so we are honest about rare classes.
  6. Saves the tuned model to `backend/app/ml/model.joblib` with joblib.
  7. Appends every experiment to `backend/app/ml/results.csv`.

Run from the repo root with:

    backend/.venv/Scripts/python -m backend.app.ml.train_classifier

or from the backend folder:

    .venv/Scripts/python -m app.ml.train_classifier
"""

from __future__ import annotations

import csv
import datetime
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    cross_val_predict,
    cross_validate,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# --- Paths ---------------------------------------------------------------
# We resolve paths from this file so the script works whether you run it
# from the repo root, from `backend/`, or from anywhere else.
ML_DIR = Path(__file__).resolve().parent  # backend/app/ml
PROJECT_ROOT = ML_DIR.parents[2]  # repo root
DATA_PATH = PROJECT_ROOT / "data" / "destinations.csv"
RESULTS_PATH = ML_DIR / "results.csv"
MODEL_PATH = ML_DIR / "model.joblib"

# --- Constants -----------------------------------------------------------
RANDOM_STATE = 42  # Fixed seed everywhere for reproducibility.

FEATURES = [
    "budget_level",
    "climate_warmth",
    "hiking_score",
    "culture_score",
    "tourism_level",
    "luxury_score",
    "family_score",
    "safety_score",
    "avg_daily_cost_usd",
]
TARGET = "travel_style"
LABELS = ["Adventure", "Relaxation", "Culture", "Budget", "Luxury", "Family"]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Read the CSV and split into X (features) and y (label)."""
    df = pd.read_csv(DATA_PATH)
    missing = set([*FEATURES, TARGET]) - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {sorted(missing)}")
    unknown = sorted(set(df[TARGET].unique()) - set(LABELS))
    if unknown:
        raise ValueError(f"Dataset contains unknown labels: {unknown}")
    X = df[FEATURES]
    y = df[TARGET]
    return df, X, y


def build_pipelines() -> dict[str, Pipeline]:
    """Three side-by-side Pipelines.

    Each has the SAME preprocessing (StandardScaler) so the comparison is
    apples-to-apples. Putting StandardScaler inside the Pipeline is
    important: cross_validate will refit the scaler on every training
    fold, which prevents leakage from the validation fold into scaling.
    """
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("scale", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("scale", StandardScaler()),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=200,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "gradient_boosting": Pipeline(
            steps=[
                ("scale", StandardScaler()),
                (
                    "clf",
                    GradientBoostingClassifier(random_state=RANDOM_STATE),
                ),
            ]
        ),
    }


def cross_val_summary(
    pipelines: dict[str, Pipeline],
    X: pd.DataFrame,
    y: pd.Series,
) -> list[dict[str, float | str]]:
    """Run 5-fold stratified CV on each pipeline.

    StratifiedKFold preserves the class ratio in every fold, which matters
    here because our dataset is mildly imbalanced (Adventure has 25 rows,
    Budget/Luxury/Family have 20 each).
    """
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    rows: list[dict[str, float | str]] = []
    for name, pipe in pipelines.items():
        scores = cross_validate(
            pipe,
            X,
            y,
            cv=cv,
            scoring=["accuracy", "f1_macro"],
            n_jobs=1,
        )
        rows.append(
            {
                "model": name,
                "accuracy_mean": float(scores["test_accuracy"].mean()),
                "accuracy_std": float(scores["test_accuracy"].std()),
                "f1_macro_mean": float(scores["test_f1_macro"].mean()),
                "f1_macro_std": float(scores["test_f1_macro"].std()),
            }
        )
    return rows


def tune_random_forest(X: pd.DataFrame, y: pd.Series) -> GridSearchCV:
    """Search a small grid of Random Forest hyperparameters.

    We tune Random Forest because tree ensembles tend to do well on
    small-to-medium tabular data and have intuitive knobs:
      - n_estimators: more trees = more stable, slower
      - max_depth:    shallower trees = stronger regularisation
      - min_samples_split: bigger value = harder to split = more
        regularisation
    """
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    pipe = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("clf", RandomForestClassifier(random_state=RANDOM_STATE)),
        ]
    )
    grid = {
        "clf__n_estimators": [100, 200, 400],
        "clf__max_depth": [None, 5, 10],
        "clf__min_samples_split": [2, 5],
    }
    search = GridSearchCV(
        pipe,
        param_grid=grid,
        cv=cv,
        scoring="f1_macro",
        n_jobs=1,
        refit=True,
    )
    search.fit(X, y)
    return search


def per_class_report(estimator: Pipeline, X: pd.DataFrame, y: pd.Series) -> str:
    """Per-class precision/recall/F1 from cross-validated predictions.

    Using cross_val_predict here means every prediction is made on a fold
    where that row was *not* in training — so the report is honest, not
    measured on training data.
    """
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    y_pred = cross_val_predict(estimator, X, y, cv=cv, n_jobs=1)
    return classification_report(y, y_pred, labels=LABELS, digits=3)


def append_results(
    summary: list[dict[str, float | str]],
    best_params: dict,
    best_score: float,
    winner_name: str,
) -> None:
    """Append one batch of experiments to results.csv (creates if absent)."""
    is_new = not RESULTS_PATH.exists()
    timestamp = datetime.datetime.utcnow().isoformat(timespec="seconds")

    with RESULTS_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(
                [
                    "timestamp",
                    "model",
                    "accuracy_mean",
                    "accuracy_std",
                    "f1_macro_mean",
                    "f1_macro_std",
                    "tuned",
                    "params",
                    "winner",
                ]
            )
        for row in summary:
            writer.writerow(
                [
                    timestamp,
                    row["model"],
                    f"{row['accuracy_mean']:.4f}",
                    f"{row['accuracy_std']:.4f}",
                    f"{row['f1_macro_mean']:.4f}",
                    f"{row['f1_macro_std']:.4f}",
                    "no",
                    "{}",
                    "yes" if row["model"] == winner_name else "no",
                ]
            )
        writer.writerow(
            [
                timestamp,
                "random_forest_tuned",
                "",
                "",
                f"{best_score:.4f}",
                "",
                "yes",
                json.dumps(best_params, sort_keys=True),
                "yes" if winner_name == "random_forest_tuned" else "no",
            ]
        )


def main() -> None:
    print(f"Loading dataset from {DATA_PATH}")
    df, X, y = load_data()
    print(f"Rows: {len(df)} | Features: {len(FEATURES)} " f"| Classes: {sorted(y.unique())}")
    print("Class counts:")
    for label, count in y.value_counts().items():
        print(f"  {label:<11s} {count}")

    pipelines = build_pipelines()
    print("\n=== Cross-validated baselines (StratifiedKFold k=5) ===")
    summary = cross_val_summary(pipelines, X, y)
    for row in summary:
        print(
            f"  {row['model']:>22s}  "
            f"acc={row['accuracy_mean']:.3f}+/-{row['accuracy_std']:.3f}  "
            f"f1_macro={row['f1_macro_mean']:.3f}+/-{row['f1_macro_std']:.3f}"
        )

    print("\n=== GridSearchCV on Random Forest ===")
    search = tune_random_forest(X, y)
    print(f"  Best params: {search.best_params_}")
    print(f"  Best CV macro-F1: {search.best_score_:.4f}")

    # All candidates (3 baselines + 1 tuned variant) compete on mean macro-F1.
    # The actual winner is saved with joblib — we don't pre-commit to RF.
    candidates: list[tuple[str, Pipeline, float]] = [
        (row["model"], pipelines[row["model"]], float(row["f1_macro_mean"])) for row in summary
    ]
    candidates.append(("random_forest_tuned", search.best_estimator_, float(search.best_score_)))
    candidates.sort(key=lambda item: item[2], reverse=True)
    winner_name, winner_pipeline, winner_score = candidates[0]
    print(f"\n=== Winner: {winner_name} " f"(mean macro-F1 = {winner_score:.4f}) ===")

    # GridSearchCV's best_estimator_ is already fit on the full data because
    # we set refit=True. The plain baselines from build_pipelines() are not,
    # so we clone+fit before saving so the joblib artifact is ready to use.
    if winner_name == "random_forest_tuned":
        winner_fitted = winner_pipeline
    else:
        winner_fitted = clone(winner_pipeline)
        winner_fitted.fit(X, y)

    print("Per-class report (winner, cross-validated):")
    print(per_class_report(winner_fitted, X, y))

    print(f"Saving winner ({winner_name}) to {MODEL_PATH}")
    joblib.dump(winner_fitted, MODEL_PATH)

    append_results(summary, search.best_params_, search.best_score_, winner_name)
    print(f"Results appended to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
