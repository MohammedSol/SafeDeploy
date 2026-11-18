from fastapi import APIRouter, HTTPException
from mlflow import MlflowClient

from backend.app.schemas.prediction import ModelRunMetrics, ModelsCompareResponse
from backend.app.services.forecast import MODEL_ALIAS, MODEL_NAME

router = APIRouter(prefix="/api", tags=["Models"])


@router.get("/models/compare", response_model=ModelsCompareResponse)
def compare_models() -> ModelsCompareResponse:
    client = MlflowClient()
    experiment = client.get_experiment_by_name("sales-forecast")

    if experiment is None:
        raise HTTPException(status_code=404, detail="Expérience sales-forecast introuvable.")

    production = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["attributes.start_time DESC"],
    )
    required_metrics = {"cv_mae", "cv_rmse", "cv_r2"}
    selected_runs = {}

    for run in runs:
        if not required_metrics.issubset(run.data.metrics):
            continue

        algorithm = run.info.run_name
        if algorithm not in selected_runs or run.info.run_id == production.run_id:
            selected_runs[algorithm] = run
    results = []
    for run in selected_runs.values():
        metrics = run.data.metrics

        results.append(
            ModelRunMetrics(
                run_id=run.info.run_id,
                algorithm=run.info.run_name,
                mae_cv=metrics["cv_mae"],
                rmse_cv=metrics["cv_rmse"],
                r2_cv=metrics["cv_r2"],
                mae_test=metrics.get("test_mae"),
                rmse_test=metrics.get("test_rmse"),
                r2_test=metrics.get("test_r2"),
                is_production=run.info.run_id == production.run_id,
            )
        )

    return ModelsCompareResponse(
        production_model=MODEL_ALIAS,
        production_version=str(production.version),
        runs=results,
    )