// Lightweight client-side parser for "Trip DNA".
//
// The backend doesn't return a structured intent block, but a premium UI needs
// to *show* the user that the system understood their question. So we parse a
// few high-signal slots out of the raw text — purely for display.
//
// This is a transparency surface, not a planner: if a slot can't be detected,
// we say so honestly instead of inventing values.

export interface TripDNA {
  budgetUsd: number | null;
  month: string | null;
  durationLabel: string | null;
  climate: string | null;
  activities: string[];
  dislikes: string[];
}

const MONTHS = [
  "january",
  "february",
  "march",
  "april",
  "may",
  "june",
  "july",
  "august",
  "september",
  "october",
  "november",
  "december",
];

const ACTIVITY_KEYWORDS: Record<string, string> = {
  hiking: "Hiking",
  trek: "Trekking",
  trekking: "Trekking",
  surf: "Surfing",
  surfing: "Surfing",
  beach: "Beach",
  food: "Food",
  cuisine: "Food",
  museum: "Museums",
  history: "History",
  cultur: "Culture",
  diving: "Diving",
  ski: "Skiing",
  snowboard: "Snowboarding",
  wildlife: "Wildlife",
  safari: "Safari",
  road: "Road trip",
  cycling: "Cycling",
  bike: "Cycling",
  yoga: "Yoga",
  spa: "Wellness",
  wellness: "Wellness",
};

const CLIMATE_KEYWORDS: Record<string, string> = {
  warm: "Warm",
  hot: "Hot",
  tropical: "Tropical",
  cold: "Cold",
  cool: "Cool",
  snow: "Snowy",
  mild: "Mild",
};

const DISLIKE_PATTERNS: Array<{ regex: RegExp; label: string }> = [
  { regex: /not too touristy|less touristy|off the beaten/i, label: "Less touristy" },
  { regex: /no big crowds|avoid crowds|less crowded|quiet/i, label: "Avoid crowds" },
  { regex: /not too expensive|on a budget|cheap/i, label: "Budget-conscious" },
  { regex: /no long flights|short flight/i, label: "Short flights" },
  { regex: /no driving|don't (?:want to )?drive/i, label: "No driving" },
];

export function parseTripDNA(input: string): TripDNA {
  const lower = input.toLowerCase();

  // Budget — supports "$1,500", "1500 dollars", "around $2k"
  let budgetUsd: number | null = null;
  const budgetMatch =
    input.match(/\$\s*([\d,]+)\s*k?/i) ||
    input.match(/([\d,]+)\s*(?:dollars|usd)/i);
  if (budgetMatch) {
    const raw = budgetMatch[1].replace(/,/g, "");
    let n = parseInt(raw, 10);
    if (/k/i.test(budgetMatch[0]) && n < 100) n *= 1000;
    if (!Number.isNaN(n)) budgetUsd = n;
  }

  // Month
  let month: string | null = null;
  for (const m of MONTHS) {
    if (lower.includes(m)) {
      month = m.charAt(0).toUpperCase() + m.slice(1);
      break;
    }
  }

  // Duration — "two weeks", "10 days", "3 nights"
  let durationLabel: string | null = null;
  const wordToNum: Record<string, number> = {
    one: 1,
    two: 2,
    three: 3,
    four: 4,
    five: 5,
    six: 6,
    seven: 7,
    eight: 8,
    nine: 9,
    ten: 10,
  };
  const wordWeek = lower.match(
    /\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(week|day|night)s?\b/,
  );
  const numWeek = lower.match(/\b(\d{1,2})\s*(week|day|night)s?\b/);
  if (wordWeek) {
    const n = wordToNum[wordWeek[1]];
    durationLabel = `${n} ${wordWeek[2]}${n === 1 ? "" : "s"}`;
  } else if (numWeek) {
    const n = parseInt(numWeek[1], 10);
    durationLabel = `${n} ${numWeek[2]}${n === 1 ? "" : "s"}`;
  }

  // Climate
  let climate: string | null = null;
  for (const [key, label] of Object.entries(CLIMATE_KEYWORDS)) {
    if (lower.includes(key)) {
      climate = label;
      break;
    }
  }

  // Activities
  const activities = new Set<string>();
  for (const [key, label] of Object.entries(ACTIVITY_KEYWORDS)) {
    if (lower.includes(key)) activities.add(label);
  }

  // Dislikes / constraints
  const dislikes: string[] = [];
  for (const { regex, label } of DISLIKE_PATTERNS) {
    if (regex.test(input)) dislikes.push(label);
  }

  return {
    budgetUsd,
    month,
    durationLabel,
    climate,
    activities: Array.from(activities),
    dislikes,
  };
}

export function formatBudget(value: number | null): string {
  if (value === null) return "Not specified";
  return `$${value.toLocaleString("en-US")}`;
}
