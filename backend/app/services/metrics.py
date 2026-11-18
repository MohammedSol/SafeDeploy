from prometheus_client import Counter, Gauge, Histogram

PREDICTIONS_TOTAL = Counter(
    "safedeploy_predictions_total",
    "Nombre de prévisions enregistrées",
    ["model_version"],
)

PREDICTION_VALUE = Histogram(
    "safedeploy_prediction_value",
    "Distribution du chiffre d'affaires prédit en USD",
    buckets=(5000, 10000, 20000, 40000, 80000, 160000),
)

MODEL_INFO = Gauge(
    "safedeploy_model_info",
    "Modèle chargé au démarrage de l'API",
    ["algorithm", "version"],
)