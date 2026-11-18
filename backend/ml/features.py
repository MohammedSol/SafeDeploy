import pandas as pd


def build_features(sales: pd.DataFrame) -> pd.DataFrame:
    data = sales.rename(columns={"month": "date"}).copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values("date").reset_index(drop=True)

    months = pd.PeriodIndex(data["date"], freq="M")
    expected = pd.period_range(months.min(), months.max(), freq="M")
    if not months.equals(expected):
        raise ValueError("Le CSV doit contenir exactement une ligne par mois, sans interruption.")

    previous_revenue = data["revenue"].shift(1)
    data["lag_1"] = previous_revenue
    data["rolling_mean_3"] = previous_revenue.rolling(3).mean()
    data["month"] = data["date"].dt.month

    return data.dropna(subset=["lag_1", "rolling_mean_3"]).reset_index(drop=True)