from datetime import date

from psycopg.types.json import Jsonb

from backend.app.database.connection import engine


def save_prediction(
    target_month: date,
    predicted_revenue: float,
    model_name: str,
    model_version: str,
    input_features: dict[str, float | int],
) -> dict:
    with engine.begin() as conn:
        row = conn.exec_driver_sql(
            """
            INSERT INTO predictions (
                target_month, predicted_revenue, model_name, model_version, input
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at, target_month, predicted_revenue,
                      model_name, model_version, input AS input_features
            """,
            (
                target_month,
                predicted_revenue,
                model_name,
                model_version,
                Jsonb(input_features),
            ),
        ).mappings().one()

    return dict(row)


def list_predictions() -> list[dict]:
    with engine.connect() as conn:
        rows = conn.exec_driver_sql(
            """
            SELECT id, created_at, target_month, predicted_revenue,
                   model_name, model_version, input AS input_features
            FROM predictions
            ORDER BY created_at DESC, id DESC
            """
        ).mappings().all()

    return [dict(row) for row in rows]