"""Entraîne trois modèles de prévision mensuelle et publie le meilleur dans MLflow."""

import os
from pathlib import Path

import mlflow
import mlflow.sklearn
import mlflow.xgboost
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from xgboost import XGBRegressor

from backend.ml.features import build_features

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sales.csv"
FEATURES = ["lag_1", "rolling_mean_3", "month"]
TEST_MONTHS = 12
CV_SPLITS = 3
RANDOM_SEED = 42
EXPERIMENT_NAME = "sales-forecast"
MODEL_NAME = "sales-model"
MODEL_ALIAS = "production"


def load_train_test():
    """Réserve les 12 derniers mois au test chronologique."""
    data = build_features(pd.read_csv(DATA_PATH))
    # Chaque pli de validation doit contenir au moins deux mois pour le R².
    if len(data) < TEST_MONTHS + 2 * (CV_SPLITS + 1):
        raise ValueError("Historique insuffisant pour la validation et le test final.")

    return data.iloc[:-TEST_MONTHS].copy(), data.iloc[-TEST_MONTHS:].copy()


def main():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(EXPERIMENT_NAME)

    train, test = load_train_test()
    x_train, y_train = train[FEATURES], train["revenue"]
    x_test, y_test = test[FEATURES], test["revenue"]

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=1),
        "XGBoost": XGBRegressor(random_state=RANDOM_SEED, n_jobs=1),
    }
    cv = TimeSeriesSplit(n_splits=CV_SPLITS)
    scoring = {
        "mae": "neg_mean_absolute_error",
        "rmse": "neg_root_mean_squared_error",
        "r2": "r2",
    }

    cv_metrics = {}
    for name, model in models.items():
        scores = cross_validate(
            model, x_train, y_train, cv=cv, scoring=scoring, error_score="raise"
        )
        cv_metrics[name] = {
            "cv_mae": float(-scores["test_mae"].mean()),
            "cv_rmse": float(-scores["test_rmse"].mean()),
            "cv_r2": float(scores["test_r2"].mean()),
        }

    best_name = min(cv_metrics, key=lambda name: cv_metrics[name]["cv_mae"])
    run_ids = {}
    example = x_train.head(3)

    for name, model in models.items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        metrics = {
            **cv_metrics[name],
            "test_mae": float(mean_absolute_error(y_test, predictions)),
            "test_rmse": float(mean_squared_error(y_test, predictions) ** 0.5),
            "test_r2": float(r2_score(y_test, predictions)),
        }

        with mlflow.start_run(run_name=name) as run:
            mlflow.log_params({
                **model.get_params(),
                "cv_splits": CV_SPLITS,
                "train_months": len(train),
                "test_months": len(test),
            })
            mlflow.log_metrics(metrics)

            flavor = mlflow.xgboost if isinstance(model, XGBRegressor) else mlflow.sklearn
            flavor.log_model(
                model,
                artifact_path="model",
                signature=infer_signature(example, model.predict(example)),
                input_example=example,
            )
            run_ids[name] = run.info.run_id

        print(
            f"{name} | MAE validation={metrics['cv_mae']:.2f} "
            f"| MAE test={metrics['test_mae']:.2f}"
        )

    version = mlflow.register_model(f"runs:/{run_ids[best_name]}/model", MODEL_NAME)
    client = MlflowClient()
    client.set_registered_model_alias(MODEL_NAME, MODEL_ALIAS, version.version)
    print(f"Modèle retenu : {best_name} → {MODEL_NAME} v{version.version} @{MODEL_ALIAS}")


if __name__ == "__main__":
    main()
