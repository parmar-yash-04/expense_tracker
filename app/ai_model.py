import os
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

TRAINING_DATA = [
    ("pizza", "Food"),
    ("burger", "Food"),
    ("sandwich", "Food"),
    ("coffee", "Food"),
    ("tea", "Food"),
    ("restaurant", "Food"),
    ("lunch", "Food"),
    ("dinner", "Food"),
    ("breakfast", "Food"),
    ("uber", "Transport"),
    ("taxi", "Transport"),
    ("bus", "Transport"),
    ("train", "Transport"),
    ("metro", "Transport"),
    ("fuel", "Transport"),
    ("petrol", "Transport"),
    ("parking", "Transport"),
    ("movie", "Entertainment"),
    ("netflix", "Entertainment"),
    ("concert", "Entertainment"),
    ("game", "Entertainment"),
    ("shopping", "Shopping"),
    ("clothes", "Shopping"),
    ("shoes", "Shopping"),
    ("amazon", "Shopping"),
    ("medicine", "Health"),
    ("doctor", "Health"),
    ("hospital", "Health"),
    ("gym", "Health"),
    ("rent", "Utilities"),
    ("electricity", "Utilities"),
    ("water", "Utilities"),
    ("internet", "Utilities"),
    ("phone", "Utilities"),
    ("gas", "Utilities"),
    ("salary", "Income"),
    ("freelance", "Income"),
    ("investment", "Income"),
    ("gift", "Other"),
    ("miscellaneous", "Other"),
]

MODEL_PATH = "ai_model.pkl"


def train_model():
    descriptions = [item[0] for item in TRAINING_DATA]
    categories = [item[1] for item in TRAINING_DATA]

    pipeline = Pipeline([
        ("vectorizer", CountVectorizer()),
        ("classifier", LogisticRegression(max_iter=1000)),
    ])
    pipeline.fit(descriptions, categories)
    joblib.dump(pipeline, MODEL_PATH)
    return pipeline


def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return train_model()


def predict_category(description: str) -> str:
    model = load_model()
    prediction = model.predict([description])[0]
    return prediction


if __name__ == "__main__":
    train_model()
    print("Model trained successfully!")
    print(f"Test prediction: {predict_category('pizza')}")
