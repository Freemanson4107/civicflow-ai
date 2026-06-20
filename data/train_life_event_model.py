"""
Trains a TF-IDF + Logistic Regression classifier for Life Event Detection.
(Lightweight, trains in <1s, no internet/GPU needed. Swap-in path to
DistilBERT/MiniLM documented in README — same predict() interface.)
"""
import os
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

df = pd.read_csv(os.path.join(BASE_DIR, "life_events.csv"))

X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["category"], test_size=0.2, random_state=42, stratify=df["category"]
)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
    ("clf", LogisticRegression(max_iter=1000, C=5.0)),
])

pipeline.fit(X_train, y_train)
preds = pipeline.predict(X_test)

print("Accuracy:", accuracy_score(y_test, preds))
print(classification_report(y_test, preds))

OUT_PATH = os.path.join(ROOT_DIR, "backend", "app", "ml", "life_event_model.joblib")
joblib.dump(pipeline, OUT_PATH)
print(f"Saved model to {OUT_PATH}")
