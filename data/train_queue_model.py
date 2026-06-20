"""
Trains queue/wait-time forecasting models:
 - RandomForestRegressor -> predicted wait time (minutes)
 - GradientBoostingClassifier -> crowd level (low/moderate/high)
(XGBoost/LightGBM unavailable offline in this sandbox; RandomForest/
GradientBoosting are explicitly listed as acceptable alternatives in
the spec and are drop-in compatible -- swap import to xgboost.XGBRegressor
later with zero feature-engineering changes.)
"""
import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

df = pd.read_csv(os.path.join(BASE_DIR, "queue_history.csv"))

# Encode categoricals
le_office = LabelEncoder()
le_type = LabelEncoder()
le_weather = LabelEncoder()
le_region = LabelEncoder()

df["office_id_enc"] = le_office.fit_transform(df["office_id"])
df["office_type_enc"] = le_type.fit_transform(df["office_type"])
df["weather_enc"] = le_weather.fit_transform(df["weather"])
df["region_enc"] = le_region.fit_transform(df["region"])

FEATURES = ["region_enc","office_id_enc","office_type_enc","day_of_week","hour",
            "is_holiday","weather_enc","seasonal_factor"]

X = df[FEATURES]
y_wait = df["actual_wait_time_minutes"]
y_crowd = df["crowd_level"]

X_train, X_test, ywait_train, ywait_test, ycrowd_train, ycrowd_test = train_test_split(
    X, y_wait, y_crowd, test_size=0.2, random_state=42
)

# --- Wait time regressor ---
reg = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
reg.fit(X_train, ywait_train)
pred_wait = reg.predict(X_test)
print("Wait-time MAE (minutes):", round(mean_absolute_error(ywait_test, pred_wait), 2))

# --- Crowd level classifier ---
clf = GradientBoostingClassifier(n_estimators=120, max_depth=3, random_state=42)
clf.fit(X_train, ycrowd_train)
pred_crowd = clf.predict(X_test)
print("Crowd-level accuracy:", round(accuracy_score(ycrowd_test, pred_crowd), 3))
print(classification_report(ycrowd_test, pred_crowd))

# Feature importance (for "service efficiency score" explainability)
importances = dict(zip(FEATURES, reg.feature_importances_.round(3)))
print("Feature importances (wait-time model):", importances)

bundle = {
    "regressor": reg,
    "classifier": clf,
    "le_office": le_office,
    "le_type": le_type,
    "le_weather": le_weather,
    "le_region": le_region,
    "features": FEATURES,
}
OUT_PATH = os.path.join(ROOT_DIR, "backend", "app", "ml", "queue_model.joblib")
joblib.dump(bundle, OUT_PATH)
print(f"Saved bundle to {OUT_PATH}")
