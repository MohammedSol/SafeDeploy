"""
Schémas Pydantic du contrat d'API SafeDeploy.
Figé en S0 — ne pas modifier sans accord de l'équipe.

Endpoints couverts :
  GET  /health
  GET  /api/sales
  GET  /api/sales/summary
  POST /api/predictions
  GET  /api/predictions/history
  GET  /api/models/compare
  GET  /metrics   (réponse texte Prometheus, pas de schéma Pydantic)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ----------------------------------------------------------------
# /health
# ----------------------------------------------------------------

class HealthResponse(BaseModel):
    """Réponse de GET /health."""

    status: str = Field(
        ...,
        description="'ok' si le backend est opérationnel",
        examples=["ok"],
    )
    database: str = Field(
        ...,
        description="'connected' ou message d'erreur",
        examples=["connected"],
    )
    model: str = Field(
        ...,
        description="'loaded' ou message d'erreur",
        examples=["loaded"],
    )


# ----------------------------------------------------------------
# /api/sales
# ----------------------------------------------------------------

class SaleRecord(BaseModel):
    """Un point de vente mensuel."""

    month: date = Field(..., description="Premier jour du mois concerné")
    revenue: float = Field(..., description="Chiffre d'affaires en USD", ge=0)


class SalesResponse(BaseModel):
    """Réponse de GET /api/sales."""

    data: list[SaleRecord]


# ----------------------------------------------------------------
# /api/sales/summary
# ----------------------------------------------------------------

class SalesSummaryResponse(BaseModel):
    """Réponse de GET /api/sales/summary."""

    total_revenue: float = Field(..., description="CA cumulé sur toute la période", ge=0)
    last_month_revenue: float = Field(..., description="CA du dernier mois disponible", ge=0)
    last_month: date = Field(..., description="Date du dernier mois disponible")
    evolution_pct: Optional[float] = Field(
        None,
        description="Évolution du CA en % par rapport au mois précédent (None si donnée insuffisante)",
    )


# ----------------------------------------------------------------
# /api/predictions  (POST)
# ----------------------------------------------------------------

class PredictionRequest(BaseModel):
    """
    Corps optionnel de POST /api/predictions.
    Si omis, le backend calcule les features depuis la base.
    """

    lag_1: Optional[float] = Field(
        None,
        description="CA du mois précédent (feature lag_1). Calculé depuis la base si absent.",
        ge=0,
    )
    rolling_mean_3: Optional[float] = Field(
        None,
        description="Moyenne glissante des 3 mois précédents. Calculée depuis la base si absente.",
        ge=0,
    )
    month: Optional[int] = Field(
        None,
        description="Numéro du mois cible (1-12). Calculé depuis la base si absent.",
        ge=1,
        le=12,
    )


class PredictionResponse(BaseModel):
    """Réponse de POST /api/predictions."""

    id: int = Field(..., description="Identifiant de la prédiction en base")
    created_at: datetime = Field(..., description="Horodatage de la création")
    target_month: date = Field(..., description="Mois prédit")
    predicted_revenue: float = Field(..., description="Chiffre d'affaires prédit en USD", ge=0)
    model_name: str = Field(..., description="Nom du modèle MLflow utilisé")
    model_version: Optional[str] = Field(None, description="Version du modèle MLflow")
    input_features: dict[str, Any] = Field(
        ...,
        description="Features réellement utilisées pour la prédiction",
    )


# ----------------------------------------------------------------
# /api/predictions/history
# ----------------------------------------------------------------

class PredictionHistoryResponse(BaseModel):
    """Réponse de GET /api/predictions/history."""

    data: list[PredictionResponse]


# ----------------------------------------------------------------
# /api/models/compare
# ----------------------------------------------------------------

class ModelRunMetrics(BaseModel):
    """Métriques d'un run MLflow pour un modèle donné."""

    run_id: str = Field(..., description="Identifiant du run MLflow")
    algorithm: str = Field(
        ...,
        description="Nom de l'algorithme",
        examples=["LinearRegression", "RandomForest", "XGBoost"],
    )
    mae_cv: float = Field(..., description="MAE moyenne de validation croisée")
    rmse_cv: float = Field(..., description="RMSE moyenne de validation croisée")
    r2_cv: float = Field(..., description="R² moyen de validation croisée")
    mae_test: Optional[float] = Field(None, description="MAE sur le jeu de test final")
    rmse_test: Optional[float] = Field(None, description="RMSE sur le jeu de test final")
    r2_test: Optional[float] = Field(None, description="R² sur le jeu de test final")
    is_production: bool = Field(
        ...,
        description="True si ce run correspond au modèle portant l'alias 'production'",
    )


class ModelsCompareResponse(BaseModel):
    """Réponse de GET /api/models/compare."""

    production_model: str = Field(..., description="Alias du modèle en production")
    production_version: Optional[str] = Field(None, description="Version du modèle en production")
    runs: list[ModelRunMetrics]
