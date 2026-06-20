"""
Trains a Gradient Boosting Regressor for the Benefit Priority Model.

Scope: this model ONLY ranks/scores benefits a citizen has already passed the
deterministic eligibility gate for (age range, income cap, employment match,
family-size minimum — enforced in app/routers/benefits.py). It never decides
pass/fail itself. See data/generate_benefit_priority.py for label methodology
and the disclosed synthetic-data tradeoff.

Features: income_ratio, age_centrality, family_margin, category_match,
employment_match_any, region_density (see generator docstring for definitions).
Target: priority_label (0-1 continuous).
"""
import os
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

df = pd.read_csv(os.path.join(BASE_DIR, "benefit_priority_training.csv"))

FEATURES = [
    "income_ratio", "age_centrality", "family_margin",
    "category_match", "employment_match_any", "region_density",
]
X = df[FEATURES]
y = df["priority_label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("reg", GradientBoostingRegressor(
        n_estimators=150, max_depth=3, learning_rate=0.08, random_state=42
    )),
])

pipeline.fit(X_train, y_train)
preds = pipeline.predict(X_test)

print("MAE:", round(mean_absolute_error(y_test, preds), 4))
print("R2:", round(r2_score(y_test, preds), 4))

# Sanity check: feature importances (post-scaling, from the underlying regressor)
importances = pipeline.named_steps["reg"].feature_importances_
for feat, imp in sorted(zip(FEATURES, importances), key=lambda x: -x[1]):
    print(f"  {feat}: {imp:.3f}")

OUT_PATH = os.path.join(ROOT_DIR, "backend", "app", "ml", "benefit_priority_model.joblib")
joblib.dump({"pipeline": pipeline, "features": FEATURES}, OUT_PATH)
print(f"Saved model to {OUT_PATH}")
