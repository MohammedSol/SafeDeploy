from fastapi import APIRouter, HTTPException

from backend.app.database.connection import engine
from backend.app.schemas.prediction import SalesResponse, SalesSummaryResponse

router = APIRouter(prefix="/api", tags=["Sales"])


@router.get("/sales", response_model=SalesResponse)
def get_sales() -> SalesResponse:
    with engine.connect() as conn:
        rows = conn.exec_driver_sql(
            "SELECT month, revenue FROM sales_monthly ORDER BY month"
        ).mappings().all()

    return SalesResponse(data=[dict(row) for row in rows])


@router.get("/sales/summary", response_model=SalesSummaryResponse)
def get_sales_summary() -> SalesSummaryResponse:
    with engine.connect() as conn:
        row = conn.exec_driver_sql(
            """
            SELECT SUM(revenue) OVER () AS total_revenue,
                   revenue AS last_month_revenue,
                   month AS last_month,
                   LAG(revenue) OVER (ORDER BY month) AS previous_revenue
            FROM sales_monthly
            ORDER BY month DESC
            LIMIT 1
            """
        ).mappings().fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Aucune vente disponible.")

    previous = row["previous_revenue"]
    evolution_pct = (
        float((row["last_month_revenue"] - previous) / previous * 100)
        if previous
        else None
    )

    return SalesSummaryResponse(
        total_revenue=row["total_revenue"],
        last_month_revenue=row["last_month_revenue"],
        last_month=row["last_month"],
        evolution_pct=evolution_pct,
    )