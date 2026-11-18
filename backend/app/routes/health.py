import logging

from fastapi import APIRouter, Response
from mlflow import MlflowClient

from backend.app.database.connection import engine
from backend.app.schemas.prediction import HealthResponse
from backend.app.services.forecast import MODEL_ALIAS, MODEL_NAME, load_model

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
def get_health(response: Response) -> HealthResponse:
    database_status = "connected"
    model_status = "loaded"

    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1").scalar_one()
    except Exception:
        logger.exception("Échec du contrôle PostgreSQL")
        database_status = "unavailable"

    try:
        version = MlflowClient().get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
        load_model(str(version.version))
    except Exception:
        logger.exception("Échec du contrôle MLflow")
        model_status = "unavailable"

    healthy = database_status == "connected" and model_status == "loaded"
    if not healthy:
        response.status_code = 503

    return HealthResponse(
        status="ok" if healthy else "degraded",
        database=database_status,
        model=model_status,
    )