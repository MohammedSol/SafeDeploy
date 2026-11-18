import pandas as pd

from backend.ml.features import build_features


def sample_sales():
    return pd.DataFrame({
        "month": pd.date_range("2023-01-01", periods=5, freq="MS"),
        "revenue": [100, 200, 300, 400, 500],
    })


def test_features_use_only_previous_months():
    sales = sample_sales()
    sales.loc[3, "revenue"] = 9999  # On change les ventes d’avril.

    april = build_features(sales).iloc[0]

    assert april["month"] == 4
    assert april["revenue"] == 9999
    assert april["lag_1"] == 300
    assert april["rolling_mean_3"] == 200


def test_features_drop_first_three_months_without_leaving_missing_values():
    result = build_features(sample_sales())

    assert result["month"].tolist() == [4, 5]
    assert result.notna().all().all()