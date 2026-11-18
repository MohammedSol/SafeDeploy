from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from mlflow import MlflowClient
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes.health import router as health_router
from backend.app.routes.models import router as models_router
from backend.app.routes.predictions import router as predictions_router
from backend.app.routes.sales import router as sales_router
from backend.app.services.forecast import MODEL_ALIAS, MODEL_NAME, load_model
from prometheus_fastapi_instrumentator import Instrumentator

from backend.app.services.metrics import MODEL_INFO

def preload_production_model() -> None:
    try:
        client = MlflowClient()
        model_version = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
        version = str(model_version.version)
        load_model(version)

        run = client.get_run(model_version.run_id)
        MODEL_INFO.labels(algorithm=run.info.run_name, version=version).set(1)
    except Exception as exc:
        raise RuntimeError(
            f"Impossible de charger {MODEL_NAME}@{MODEL_ALIAS} depuis MLflow. "
            "Vérifie que MLflow est accessible et que l’alias pointe vers une version valide."
        ) from exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(preload_production_model)
    yield


app = FastAPI(title="SafeDeploy API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(predictions_router)
app.include_router(sales_router)
app.include_router(health_router)
app.include_router(models_router)


Instrumentator().instrument(app).expose(app)