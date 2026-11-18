from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app import main
from backend.app.database.connection import engine
from backend.app.routes import health, models, predictions, sales
from backend.app.services import sales as sales_service


@pytest.fixture
def client():
    with TestClient(main.app) as api:
        yield api


@pytest.fixture
def client_without_mlflow_startup(monkeypatch):
    monkeypatch.setattr(main, "preload_production_model", lambda: None)
    with TestClient(main.app) as api:
        yield api


def test_prediction_rejects_invalid_month(client_without_mlflow_startup):
    response = client_without_mlflow_startup.post(
        "/api/predictions", json={"month": 13}
    )

    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "month"]
        for error in response.json()["detail"]
    )


def test_startup_fails_when_production_model_is_missing(monkeypatch):
    class ClientWithoutProductionModel:
        def get_model_version_by_alias(self, name, alias):
            raise LookupError("Alias production introuvable")

    monkeypatch.setattr(main, "MlflowClient", ClientWithoutProductionModel)

    with pytest.raises(RuntimeError, match="Impossible de charger sales-model@production"):
        with TestClient(main.app):
            pass


def test_health_reports_database_connected_and_model_loaded(client):
    response = client.get("/health")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "ok",
        "database": "connected",
        "model": "loaded",
    }


def test_health_returns_503_when_database_is_unavailable(client, monkeypatch):
    unavailable_engine = MagicMock()
    unavailable_engine.connect.side_effect = OSError("PostgreSQL indisponible")
    monkeypatch.setattr(health, "engine", unavailable_engine)

    response = client.get("/health")

    assert response.status_code == 503, response.text
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "unavailable"


def test_sales_and_summary_are_consistent(client):
    response = client.get("/api/sales")
    assert response.status_code == 200, response.text
    records = response.json()["data"]

    assert len(records) >= 3
    months = [record["month"] for record in records]
    assert months == sorted(set(months))

    response = client.get("/api/sales/summary")
    assert response.status_code == 200, response.text
    summary = response.json()

    assert summary["last_month"] == records[-1]["month"]
    assert summary["last_month_revenue"] == records[-1]["revenue"]
    assert summary["total_revenue"] == pytest.approx(
        sum(record["revenue"] for record in records)
    )

    previous = records[-2]["revenue"]
    if previous:
        expected = (records[-1]["revenue"] - previous) / previous * 100
        assert summary["evolution_pct"] == pytest.approx(expected)
    else:
        assert summary["evolution_pct"] is None


def test_empty_database(client_without_mlflow_startup, monkeypatch):
    empty_engine = MagicMock()
    conn = empty_engine.connect.return_value.__enter__.return_value
    rows = conn.exec_driver_sql.return_value.mappings.return_value
    rows.all.return_value = []
    rows.fetchone.return_value = None

    monkeypatch.setattr(sales, "engine", empty_engine)
    monkeypatch.setattr(sales_service, "engine", empty_engine)
    monkeypatch.setattr(predictions, "list_predictions", lambda: [])

    api = client_without_mlflow_startup
    sales_response = api.get("/api/sales")
    assert sales_response.status_code == 200
    assert sales_response.json() == {"data": []}

    assert api.get("/api/sales/summary").status_code == 404
    assert api.post("/api/predictions", json={}).status_code == 422

    history = api.get("/api/predictions/history")
    assert history.status_code == 200
    assert history.json() == {"data": []}


def test_models_compare_returns_three_algorithms(client):
    response = client.get("/api/models/compare")

    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["runs"]) == 3
    assert {run["algorithm"] for run in result["runs"]} == {
        "Linear Regression",
        "Random Forest",
        "XGBoost",
    }
    assert sum(run["is_production"] for run in result["runs"]) == 1
    assert result["production_version"]


def test_models_compare_returns_404_when_experiment_is_missing(
    client_without_mlflow_startup, monkeypatch
):
    mlflow_client = MagicMock()
    mlflow_client.get_experiment_by_name.return_value = None
    monkeypatch.setattr(models, "MlflowClient", lambda: mlflow_client)

    response = client_without_mlflow_startup.get("/api/models/compare")

    assert response.status_code == 404


def test_prediction_is_saved_visible_in_history_and_counted(client):
    prediction_id = None

    try:
        response = client.post("/api/predictions", json={})
        assert response.status_code == 200, response.text
        prediction = response.json()
        prediction_id = prediction["id"]
        assert isinstance(prediction["predicted_revenue"], (int, float))

        history = client.get("/api/predictions/history")
        assert history.status_code == 200, history.text
        assert prediction in history.json()["data"]

        metrics = client.get("/metrics")
        assert metrics.status_code == 200, metrics.text
        version = prediction["model_version"]
        assert f'safedeploy_predictions_total{{model_version="{version}"}}' in metrics.text
        assert "safedeploy_prediction_value_count " in metrics.text
        assert "safedeploy_model_info{" in metrics.text
    finally:
        if prediction_id is not None:
            with engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM predictions WHERE id = :id"),
                    {"id": prediction_id},
                )