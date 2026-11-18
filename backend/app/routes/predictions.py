from datetime import date

from fastapi import APIRouter, HTTPException

from backend.app.database.predictions import save_prediction,list_predictions
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse,PredictionHistoryResponse
from backend.app.services.forecast import MODEL_NAME, predict_revenue
from backend.app.services.sales import get_next_month_inputs
from backend.app.services.metrics import PREDICTIONS_TOTAL, PREDICTION_VALUE

router = APIRouter(prefix="/api", tags=["Predictions"])


@router.post("/predictions", response_model=PredictionResponse)
def create_prediction(body: PredictionRequest | None = None) -> PredictionResponse:
    try:
        target_month, defaults = get_next_month_inputs()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    request = body if body is not None else PredictionRequest()
    month = request.month if request.month is not None else target_month.month

    if month != target_month.month:
        if request.lag_1 is None or request.rolling_mean_3 is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Pour un mois autre que le prochain mois disponible, "
                    "renseigne lag_1 et rolling_mean_3."
                ),
            )
        year = target_month.year + int(month < target_month.month)
        target_month = date(year, month, 1)

    features = {
        "lag_1": request.lag_1 if request.lag_1 is not None else defaults["lag_1"],
        "rolling_mean_3": (
            request.rolling_mean_3
            if request.rolling_mean_3 is not None
            else defaults["rolling_mean_3"]
        ),
        "month": month,
    }

    predicted_revenue, version = predict_revenue(**features)
    saved = save_prediction(
        target_month=target_month,
        predicted_revenue=predicted_revenue,
        model_name=MODEL_NAME,
        model_version=version,
        input_features=features,
    )
    PREDICTIONS_TOTAL.labels(model_version=version).inc()
    PREDICTION_VALUE.observe(float(saved["predicted_revenue"]))
    return PredictionResponse(**saved)


@router.get("/predictions/history", response_model=PredictionHistoryResponse)
def get_prediction_history() -> PredictionHistoryResponse:
    return PredictionHistoryResponse(data=list_predictions())