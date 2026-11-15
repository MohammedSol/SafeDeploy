"""
Package schemas — contrat d'API SafeDeploy (figé en S0).
Importer depuis ici dans les routes (S2) :
    from app.schemas import PredictionRequest, PredictionResponse, ...
"""

from .prediction import (
    HealthResponse,
    ModelRunMetrics,
    ModelsCompareResponse,
    PredictionHistoryResponse,
    PredictionRequest,
    PredictionResponse,
    SaleRecord,
    SalesResponse,
    SalesSummaryResponse,
)

__all__ = [
    "HealthResponse",
    "ModelRunMetrics",
    "ModelsCompareResponse",
    "PredictionHistoryResponse",
    "PredictionRequest",
    "PredictionResponse",
    "SaleRecord",
    "SalesResponse",
    "SalesSummaryResponse",
]
