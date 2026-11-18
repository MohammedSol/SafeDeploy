from datetime import date

from backend.app.database.connection import engine


def get_next_month_inputs():
    with engine.connect() as conn:
        sales = conn.exec_driver_sql(
            """
            SELECT month, revenue
            FROM sales_monthly
            ORDER BY month DESC
            LIMIT 3
            """
        ).mappings().all()

    if len(sales) < 3:
        raise ValueError("Trois mois de ventes sont nécessaires.")

    months = [row["month"].year * 12 + row["month"].month for row in sales]
    if months != [months[0], months[0] - 1, months[0] - 2]:
        raise ValueError("Les trois derniers mois de ventes doivent être consécutifs.")

    latest_month = sales[0]["month"]
    next_year, next_month = divmod(latest_month.year * 12 + latest_month.month, 12)
    target_month = date(next_year, next_month + 1, 1)

    features = {
        "lag_1": float(sales[0]["revenue"]),
        "rolling_mean_3": float(sum(row["revenue"] for row in sales) / 3),
        "month": target_month.month,
    }

    return target_month, features