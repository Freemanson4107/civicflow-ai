"""
Generates synthetic (text -> life_event_category) dataset.
Categories: child_support, healthcare_support, unemployment,
            housing_assistance, food_assistance, disability_support, elderly_care
"""
import csv
import os
import random

random.seed(42)

TEMPLATES = {
    "unemployment": [
        "I lost my job last week and don't know what to do.",
        "I was laid off from my company.",
        "My employer shut down the factory and I'm out of work.",
        "I got fired and need help paying bills.",
        "I've been unemployed for three months now.",
        "The company downsized and I lost my position.",
        "I quit my job because of unsafe conditions and need support.",
        "My contract ended and I haven't found new work.",
        "I'm jobless and looking for unemployment benefits.",
        "My business closed during the slowdown and I have no income.",
    ],
    "child_support": [
        "I recently had a baby and need childcare help.",
        "My daughter just started school and I need support with supplies.",
        "I am a single mother raising two kids alone.",
        "We just adopted a child and need financial assistance.",
        "I need help paying for daycare for my toddler.",
        "My son needs a new pair of shoes for school and we can't afford it.",
        "I'm pregnant and need prenatal support services.",
        "I'm a single father struggling to support my children.",
        "We have triplets and need extra family support.",
        "My child needs school supplies and I have no income this month.",
    ],
    "healthcare_support": [
        "My father needs medical assistance and we can't afford it.",
        "I need help paying for my surgery.",
        "My mother was diagnosed with cancer and needs treatment support.",
        "I don't have health insurance and need to see a doctor.",
        "My child needs vaccinations but we can't afford the clinic visit.",
        "I need financial help for my hospital bill.",
        "My husband had a heart attack and we need medical support.",
        "I require ongoing dialysis treatment and need assistance.",
        "I broke my leg and have no way to pay for the hospital.",
        "My wife is pregnant and we need maternal healthcare support.",
    ],
    "housing_assistance": [
        "I'm about to be evicted and need housing help.",
        "We can't afford rent this month.",
        "I am homeless and need shelter assistance.",
        "My landlord raised the rent and I can't keep up.",
        "Our house was damaged in a flood and we need housing support.",
        "I need help finding affordable housing for my family.",
        "We are living in our car and need emergency shelter.",
        "I'm behind on my mortgage payments and may lose my home.",
        "My apartment building was condemned and we need new housing.",
        "I need a rental subsidy to keep my apartment.",
    ],
    "food_assistance": [
        "I don't have enough money to buy groceries this week.",
        "My family is struggling to put food on the table.",
        "I need help getting food stamps.",
        "We ran out of food and have no money until next payday.",
        "My kids are going to school hungry and I need food support.",
        "I lost my job and now can't afford to feed my family.",
        "We need access to a local food bank.",
        "I am elderly and can't afford groceries on my pension.",
        "My income dropped and I can't buy enough food for my children.",
        "I need nutritional assistance for my newborn.",
    ],
    "disability_support": [
        "I have a permanent disability and need financial support.",
        "My son has autism and needs special education support.",
        "I lost my leg in an accident and need disability benefits.",
        "My daughter is in a wheelchair and needs accessibility support.",
        "I am visually impaired and need assistive devices.",
        "I have a chronic illness that prevents me from working.",
        "My brother has Down syndrome and needs care services.",
        "I need a disability pension after my workplace injury.",
        "My child has a learning disability and needs special services.",
        "I have severe arthritis and can no longer work full time.",
    ],
    "elderly_care": [
        "My grandmother is 80 and needs in-home care.",
        "I need help finding a nursing home for my father.",
        "My elderly parents need assistance with daily activities.",
        "I am a senior citizen living alone and need support services.",
        "My grandfather has dementia and needs full time care.",
        "We need a caregiver for my aging mother.",
        "I am 70 years old and need help with my pension application.",
        "My parents are too old to live independently anymore.",
        "I need senior meal delivery services for my mother.",
        "My elderly aunt needs help with mobility and daily tasks.",
    ],
}

PREFIXES = ["", "Hi, ", "Hello, ", "Please help, ", "Urgent: ", "I need advice. ", "Hi there, "]
SUFFIXES = ["", " What should I do?", " Please advise.", " Can you help me?", " I don't know where to start."]

def augment(sentence):
    return random.choice(PREFIXES) + sentence + random.choice(SUFFIXES)

rows = []
for category, sentences in TEMPLATES.items():
    for s in sentences:
        for _ in range(8):  # augment to ~80 rows/category = 560 total
            rows.append((augment(s), category))

random.shuffle(rows)

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life_events.csv")
with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["text", "category"])
    writer.writerows(rows)

print(f"Generated {len(rows)} rows across {len(TEMPLATES)} categories.")
