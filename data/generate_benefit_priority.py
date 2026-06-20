"""
Generates synthetic (applicant_features -> priority_label) training data for the
Benefit Priority Model.

IMPORTANT — what this model is and is not:
- Hard eligibility (age range, income cap, employment match, family-size minimum)
  is decided by deterministic rules in app/routers/benefits.py, BEFORE this model
  ever sees a case. This generator only produces profiles that already pass that
  gate, because the model's job is to rank/prioritize among eligible applicants,
  never to decide eligibility itself.
- The label is a synthetic "case priority" score (0-1) meant to approximate how
  urgently/strongly a case should be surfaced first among several eligible
  benefits — e.g. someone deep under the income cap with a matching life-event
  category and a large family is a stronger priority than someone who barely
  qualifies with no contextual signal. This is a reasonable proxy built from
  domain heuristics with injected noise, NOT real casework outcome data (no such
  dataset exists for a civic demo). That tradeoff is intentional and disclosed
  in README — same spirit as life_events.csv / queue_history.csv being synthetic.

Features (all computed relative to the specific benefit being scored):
  income_ratio       — income / max_income_monthly (0 = no income, 1 = at cap)
  age_centrality      — how centered applicant age is in [min_age, max_age], 0-1
  family_margin       — family_size - family_size_min (>=0 since gate already passed)
  category_match      — 1 if life-event category hint matches benefit category
  employment_match_any — 1 if benefit accepts "any" employment status
  region_density      — number of benefits available in-region (context signal)
"""
import csv
import json
import os
import random

random.seed(11)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(f"{BASE_DIR}/data/benefits.json", encoding="utf-8") as f:
    BENEFITS = json.load(f)

REGION_COUNTS = {}
for b in BENEFITS:
    REGION_COUNTS[b["region"]] = REGION_COUNTS.get(b["region"], 0) + 1

EMPLOYMENT_OPTIONS = ["employed", "unemployed", "self-employed"]

rows = []
N_PER_BENEFIT = 250

for b in BENEFITS:
    min_age, max_age = b["min_age"], b["max_age"]
    max_income = b["max_income_monthly"]
    fam_min = b["family_size_min"]
    allowed_emp = b["employment_status"]
    category = b["category"]
    region = b["region"]

    for _ in range(N_PER_BENEFIT):
        # Sample an ELIGIBLE applicant (gate already satisfied) -----------------
        age = random.randint(min_age, max_age)

        # income: skew toward being under the cap by varying margins
        income_ratio_raw = random.betavariate(2, 3)  # skews low-ish, occasionally near cap
        income = round(income_ratio_raw * max_income, 2) if max_income < 999999 else round(
            random.uniform(0, 5000), 2
        )

        family_size = fam_min + random.choice([0, 0, 1, 1, 2, 3])

        if "any" in allowed_emp:
            employment_status = random.choice(EMPLOYMENT_OPTIONS)
        else:
            employment_status = random.choice(allowed_emp)

        # category hint: sometimes matches (life-event detector fired this category),
        # sometimes is a different category (or missing -> None), sometimes absent
        roll = random.random()
        if roll < 0.4:
            category_hint = category
        elif roll < 0.7:
            category_hint = random.choice(
                [c for c in {x["category"] for x in BENEFITS} if c != category]
            )
        else:
            category_hint = None

        # ---- Derived features ----
        income_ratio = min(1.0, income / max_income) if max_income < 999999 else 0.0
        span = max(1, max_age - min_age)
        age_centrality = 1.0 - abs((age - min_age) / span - 0.5) * 2  # 1.0 = dead center
        family_margin = family_size - fam_min
        category_match = 1 if (category_hint == category) else 0
        employment_match_any = 1 if "any" in allowed_emp else 0
        region_density = REGION_COUNTS[region]

        # ---- Synthetic priority label ----
        # Heuristic ground truth with intentional noise, representing "how urgently
        # this case should be surfaced" — deeper need (low income_ratio = far under
        # cap = lower income relative to threshold => more need), matching life
        # context, and larger family pulls priority up.
        need_intensity = 1.0 - income_ratio  # further under the cap = more financial need
        priority = (
            0.45 * need_intensity
            + 0.20 * category_match
            + 0.15 * min(1.0, family_margin / 3.0)
            + 0.10 * age_centrality
            + 0.10 * random.random()  # irreducible noise — no proxy is perfect
        )
        priority = max(0.0, min(1.0, priority))

        rows.append({
            "benefit_id": b["id"],
            "region": region,
            "category": category,
            "income_ratio": round(income_ratio, 4),
            "age_centrality": round(age_centrality, 4),
            "family_margin": family_margin,
            "category_match": category_match,
            "employment_match_any": employment_match_any,
            "region_density": region_density,
            "priority_label": round(priority, 4),
        })

random.shuffle(rows)

OUT_PATH = f"{BASE_DIR}/data/benefit_priority_training.csv"
with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows across {len(BENEFITS)} benefits -> {OUT_PATH}")
