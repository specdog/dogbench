#!/usr/bin/env python3
"""Sales data processor — read CSV, group by category, calculate revenue.

Usage:
  python3 sales.py <path/to/sales.csv>

CSV columns expected: date, category, product, quantity, unit_price
Output: category -> total revenue table printed to stdout.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path


def read_sales(path: str) -> list[dict]:
    """Read a sales CSV and return list of rows as dicts.

    Expected columns: date, category, product, quantity, unit_price
    """
    rows = []
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            row["quantity"] = int(row["quantity"])
            row["unit_price"] = float(row["unit_price"])
            rows.append(row)
    return rows


def revenue_by_category(rows: list[dict]) -> dict[str, float]:
    """Group sales rows by category and sum revenue (quantity * unit_price)."""
    totals: dict[str, float] = defaultdict(float)
    for r in rows:
        totals[r["category"]] += r["quantity"] * r["unit_price"]
    return dict(sorted(totals.items()))


def format_table(totals: dict[str, float]) -> str:
    """Format a category->revenue dict as an aligned text table."""
    max_cat = max((len(c) for c in totals), default=0)
    header = f"{'Category':<{max_cat}} | Revenue"
    sep = "-" * max_cat + "-+-" + "-" * 9
    lines = [header, sep]
    for cat, rev in totals.items():
        lines.append(f"{cat:<{max_cat}} | ${rev:>8,.2f}")
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <sales.csv>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).is_file():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    rows = read_sales(path)
    if not rows:
        print("No data rows found.", file=sys.stderr)
        sys.exit(1)

    totals = revenue_by_category(rows)
    print(format_table(totals))


if __name__ == "__main__":
    main()
