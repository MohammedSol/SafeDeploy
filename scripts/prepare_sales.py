from pathlib import Path
import sys

import pandas as pd

source = Path(sys.argv[1])
project_dir = Path(__file__).resolve().parents[1]
output = project_dir / "backend" / "data" / "sales.csv"

orders = pd.read_excel(source, sheet_name="Orders", usecols=["Order Date", "Sales"])
orders["month"] = pd.to_datetime(orders["Order Date"]).dt.to_period("M").dt.to_timestamp()

sales = (
    orders.groupby("month", as_index=False)["Sales"]
    .sum()
    .rename(columns={"Sales": "revenue"})
)

output.parent.mkdir(parents=True, exist_ok=True)
sales.to_csv(output, index=False, date_format="%Y-%m-%d")

print(f"{len(sales)} mois enregistrés dans {output}")
print(sales.head().to_string(index=False))