from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "DataCoSupplyChainDataset.csv"
MODEL_DIR = ROOT / "models"
OUTPUT_DIR = ROOT / "outputs"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}\n"
        "Place DataCoSupplyChainDataset.csv in data/raw/."
    )

print("Loading dataset...")
df = pd.read_csv(DATA_PATH, encoding="latin-1", low_memory=False)

# Normalize column names for consistent access.
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(r"[^a-z0-9]+", "_", regex=True)
    .str.strip("_")
)

target = "late_delivery_risk"
group_col = "order_id"
date_col = "order_date_dateorders"

for required in [target, group_col, date_col]:
    if required not in df.columns:
        raise ValueError(
            f"Required column '{required}' missing. "
            f"Available columns: {df.columns.tolist()}"
        )

df[target] = pd.to_numeric(df[target], errors="coerce")
df = df.dropna(subset=[target, group_col]).copy()
df = df[df[target].isin([0, 1])].copy()
df[target] = df[target].astype(int)

# Build features available at order time.
dates = pd.to_datetime(df[date_col], errors="coerce")
df["order_month"] = dates.dt.month
df["order_day_of_week"] = dates.dt.day_of_week if hasattr(dates.dt, "day_of_week") else dates.dt.dayofweek
df["order_hour"] = dates.dt.hour

# Only use fields that could reasonably be known when an order is placed.
numeric_candidates = [
    "order_item_discount",
    "order_item_discount_rate",
    "order_item_product_price",
    "order_item_quantity",
    "product_price",
    "order_month",
    "order_day_of_week",
    "order_hour",
]

categorical_candidates = [
    "type",
    "category_name",
    "customer_segment",
    "department_name",
    "market",
    "order_region",
    "order_country",
    "shipping_mode",
]

numeric_features = [
    c for c in numeric_candidates if c in df.columns
]
categorical_features = [
    c for c in categorical_candidates if c in df.columns
]

features = numeric_features + categorical_features
if not features:
    raise ValueError("No usable input features were found.")

# Exclude actual delivery outcomes, post-delivery fields, identifiers,
# and personal information to prevent leakage and unnecessary exposure.
X = df[features].copy()
y = df[target].copy()
groups = df[group_col].copy()

for col in numeric_features:
    X[col] = pd.to_numeric(X[col], errors="coerce")
    X[col] = X[col].replace([np.inf, -np.inf], np.nan)

for col in categorical_features:
    X[col] = X[col].astype("string").fillna(np.nan)

print(f"Rows: {len(df):,}")
print(f"Features: {features}")
print("Target distribution:")
print(y.value_counts(normalize=True).sort_index().round(4))

# Keep all line items from one order in the same partition.
splitter = GroupShuffleSplit(
    n_splits=1, test_size=0.20, random_state=42
)
train_idx, test_idx = next(splitter.split(X, y, groups=groups))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

if y_train.nunique() < 2 or y_test.nunique() < 2:
    raise ValueError(
        "The train or test partition contains only one target class. "
        "Inspect the target and group split."
    )

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(
        handle_unknown="ignore",
        min_frequency=20,
    )),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )),
])

print("\nTraining Logistic Regression...")
model.fit(X_train, y_train)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]

metrics = {
    "model": "Logistic Regression",
    "target": target,
    "split_method": "GroupShuffleSplit by Order Id",
    "random_state": 42,
    "train_rows": int(len(train_idx)),
    "test_rows": int(len(test_idx)),
    "feature_columns": features,
    "accuracy": float(accuracy_score(y_test, predictions)),
    "precision": float(precision_score(
        y_test, predictions, zero_division=0
    )),
    "recall": float(recall_score(
        y_test, predictions, zero_division=0
    )),
    "f1_score": float(f1_score(
        y_test, predictions, zero_division=0
    )),
    "roc_auc": float(roc_auc_score(y_test, probabilities)),
    "confusion_matrix": confusion_matrix(
        y_test, predictions, labels=[0, 1]
    ).tolist(),
}

model_path = MODEL_DIR / "late_delivery_risk_model.joblib"
joblib.dump(model, model_path)

with open(OUTPUT_DIR / "metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

with open(OUTPUT_DIR / "classification_report.txt", "w") as f:
    f.write(classification_report(
        y_test, predictions, zero_division=0
    ))

results = pd.DataFrame({
    "actual_late_delivery_risk": y_test.to_numpy(),
    "predicted_late_delivery_risk": predictions,
    "predicted_risk_probability": probabilities,
})
results.to_csv(OUTPUT_DIR / "test_predictions.csv", index=False)

print("\n--- Evaluation Results ---")
for name in [
    "accuracy", "precision", "recall", "f1_score", "roc_auc"
]:
    print(f"{name}: {metrics[name]:.4f}")

print("\nConfusion matrix [[TN, FP], [FN, TP]]:")
print(np.array(metrics["confusion_matrix"]))
print(f"\nModel saved: {model_path}")
print(f"Metrics saved: {OUTPUT_DIR / 'metrics.json'}")
print("Training complete.")
