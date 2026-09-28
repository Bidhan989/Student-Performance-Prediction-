"""Train, evaluate and save the ML models used by the Django application.

Run:
    python train_models.py

The script is the single training source for the web application. It saves:
- ml_models/model_bundle.joblib
- ml_models/model_metrics.json
"""
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import Ridge
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
)
from xgboost import XGBRegressor, XGBClassifier

BASE_DIR = Path(__file__).resolve().parent
DATA = BASE_DIR / "dataset" / "StudentsPerformance.csv"
OUT = BASE_DIR / "ml_models"
OUT.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
df["average_score"] = df[["math score", "reading score", "writing score"]].mean(axis=1)
df["pass_fail"] = df["average_score"].apply(lambda x: "Pass" if x >= 60 else "Fail")

categorical = [
    "gender", "race/ethnicity", "parental level of education",
    "lunch", "test preparation course"
]
encoders = {}
for col in categorical:
    le = LabelEncoder()
    df[col + "_encoded"] = le.fit_transform(df[col])
    encoders[col] = le

features = [
    "gender_encoded", "race/ethnicity_encoded",
    "parental level of education_encoded", "lunch_encoded",
    "test preparation course_encoded", "reading score", "writing score"
]
X = df[features]
y_reg = df["math score"]
y_clf = df["pass_fail"].map({"Fail": 0, "Pass": 1})

Xr_train, Xr_test, yr_train, yr_test = train_test_split(
    X, y_reg, test_size=0.2, random_state=42
)
Xc_train, Xc_test, yc_train, yc_test = train_test_split(
    X, y_clf, test_size=0.2, random_state=42
)

scaler_reg = StandardScaler().fit(Xr_train)
scaler_clf = StandardScaler().fit(Xc_train)

ridge = Ridge(alpha=1.0).fit(scaler_reg.transform(Xr_train), yr_train)
svm = SVC(
    kernel="rbf", C=1.0, gamma="scale",
    class_weight="balanced", probability=True, random_state=42
).fit(scaler_clf.transform(Xc_train), yc_train)

xgb_reg = XGBRegressor(
    n_estimators=100, learning_rate=0.1, max_depth=6,
    random_state=42, n_jobs=-1
).fit(Xr_train, yr_train)

xgb_clf = XGBClassifier(
    n_estimators=100, learning_rate=0.1, max_depth=6,
    scale_pos_weight=2.51, random_state=42, n_jobs=-1,
    eval_metric="logloss"
).fit(Xc_train, yc_train)

# ---- Test-set evaluation ----
ridge_pred = ridge.predict(scaler_reg.transform(Xr_test))
xgb_reg_pred = xgb_reg.predict(Xr_test)
svm_pred = svm.predict(scaler_clf.transform(Xc_test))
xgb_clf_pred = xgb_clf.predict(Xc_test)

def regression_metrics(y_true, pred):
    mse = mean_squared_error(y_true, pred)
    return {
        "mae": round(float(mean_absolute_error(y_true, pred)), 4),
        "rmse": round(float(mse ** 0.5), 4),
        "r2": round(float(r2_score(y_true, pred)), 4),
    }

def classification_metrics(y_true, pred):
    return {
        "accuracy": round(float(accuracy_score(y_true, pred)), 4),
        "precision": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, pred, zero_division=0)), 4),
    }

metrics = {
    "dataset": {
        "rows": int(len(df)),
        "features_used": len(features),
        "test_size": 0.20,
        "random_state": 42,
        "pass_threshold": 60,
    },
    "regression": {
        "Ridge Regression": regression_metrics(yr_test, ridge_pred),
        "XGBoost Regression": regression_metrics(yr_test, xgb_reg_pred),
    },
    "classification": {
        "SVM Classifier": classification_metrics(yc_test, svm_pred),
        "XGBoost Classifier": classification_metrics(yc_test, xgb_clf_pred),
    },
}

bundle = {
    "encoders": encoders,
    "scaler_reg": scaler_reg,
    "scaler_clf": scaler_clf,
    "ridge": ridge,
    "svm": svm,
    "xgb_reg": xgb_reg,
    "xgb_clf": xgb_clf,
}

joblib.dump(bundle, OUT / "model_bundle.joblib")
(OUT / "model_metrics.json").write_text(json.dumps(metrics, indent=2))

print("Training complete.")
print("Saved:", OUT / "model_bundle.joblib")
print("Saved:", OUT / "model_metrics.json")
print("\nRegression:")
for name, m in metrics["regression"].items():
    print(f"  {name}: R2={m['r2']:.4f}, MAE={m['mae']:.4f}, RMSE={m['rmse']:.4f}")
print("\nClassification:")
for name, m in metrics["classification"].items():
    print(f"  {name}: Accuracy={m['accuracy']:.4f}, F1={m['f1']:.4f}")
