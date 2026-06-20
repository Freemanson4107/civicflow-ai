"""
Trains a TF-IDF + Logistic Regression classifier for Document Type Detection,
replacing the previous exact-keyword-substring matcher in
app/routers/documents.py.

Same lightweight pattern as train_life_event_model.py (trains in <2s, no
internet/GPU needed). See data/generate_document_ocr.py for the synthetic
training data and the rationale for using synthetic OCR text.
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

df = pd.read_csv(os.path.join(BASE_DIR, "document_ocr_training.csv"))

X_train, X_test, y_train, y_test = train_test_split(
    df["ocr_text"], df["document_type"], test_size=0.2, random_state=42,
    stratify=df["document_type"]
)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
    ("clf", LogisticRegression(max_iter=1000, C=5.0)),
])

pipeline.fit(X_train, y_train)
preds = pipeline.predict(X_test)

print("Accuracy:", accuracy_score(y_test, preds))
print(classification_report(y_test, preds))

OUT_PATH = os.path.join(ROOT_DIR, "backend", "app", "ml", "document_type_model.joblib")
joblib.dump(pipeline, OUT_PATH)
print(f"Saved model to {OUT_PATH}")
