from functools import lru_cache

import mlflow.pyfunc
import pandas as pd
from mlflow import MlflowClient

MODEL_NAME = "sales-model"
MODEL_ALIAS = "production"


@lru_cache(maxsize=1)
def load_model(version: str):
    return mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/{version}")


def predict_revenue(
    lag_1: float,
    rolling_mean_3: float,
    month: int,
) -> tuple[float, str]:
    model_version = MlflowClient().get_model_version_by_alias(
        MODEL_NAME, MODEL_ALIAS
    )
    version = str(model_version.version)

    inputs = pd.DataFrame({
        "lag_1": [float(lag_1)],
        "rolling_mean_3": [float(rolling_mean_3)],
        "month": pd.Series([month], dtype="int32"),
    })

    prediction = load_model(version).predict(inputs)[0]
    return float(prediction), version