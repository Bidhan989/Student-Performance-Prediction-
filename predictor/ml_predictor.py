from pathlib import Path
import json
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "ml_models"

ENCODERS = [
    "gender",
    "race/ethnicity",
    "parental level of education",
    "lunch",
    "test preparation course",
]


def _load():
    path = MODEL_DIR / "model_bundle.joblib"
    if not path.exists():
        raise FileNotFoundError(path)
    return joblib.load(path)


def load_metrics():
    path = MODEL_DIR / "model_metrics.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def categorize(score):
    if score >= 80:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 60:
        return "Average"
    return "Below Average"


def predict(data):
    bundle = _load()
    values = []

    for col in ENCODERS:
        try:
            values.append(int(bundle["encoders"][col].transform([data[col]])[0]))
        except ValueError:
            raise ValueError(f"Unknown value for {col}: {data[col]}")

    values += [float(data["reading score"]), float(data["writing score"])]
    X = pd.DataFrame([values], columns=[
        "gender_encoded", "race/ethnicity_encoded",
        "parental level of education_encoded", "lunch_encoded",
        "test preparation course_encoded", "reading score", "writing score"
    ])

    ridge_math = float(
        bundle["ridge"].predict(bundle["scaler_reg"].transform(X))[0]
    )
    xgb_math = float(bundle["xgb_reg"].predict(X)[0])
    predicted_math = (ridge_math + xgb_math) / 2

    svm_proba = bundle["svm"].predict_proba(
        bundle["scaler_clf"].transform(X)
    )[0]
    xgb_proba = bundle["xgb_clf"].predict_proba(X)[0]

    svm_prediction = "Pass" if svm_proba[1] >= svm_proba[0] else "Fail"
    xgb_prediction = "Pass" if xgb_proba[1] >= xgb_proba[0] else "Fail"

    # The XGBoost classifier is the final pass/fail model.
    pass_probability = float(xgb_proba[1])
    fail_probability = float(xgb_proba[0])

    average = (
        predicted_math
        + float(data["reading score"])
        + float(data["writing score"])
    ) / 3

    return {
        "ridge_math": ridge_math,
        "xgb_math": xgb_math,
        "predicted_math": predicted_math,
        "svm_prediction": svm_prediction,
        "xgb_prediction": xgb_prediction,
        "pass_probability": pass_probability,
        "fail_probability": fail_probability,
        "estimated_average": average,
        "performance_category": categorize(average),
        "pass_fail": xgb_prediction,
    }
