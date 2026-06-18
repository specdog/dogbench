"""CSV sales data: read, group by category, calculate revenue.

Usage:
    python3 sales.py sample.csv
    python3 -m unittest test_sales -v
"""

import csv
import sys
from collections import defaultdict
from decimal import Decimal


def read_sales(path):
    """Read a CSV file and return rows as list of dicts.

    Expected columns: category, quantity, unit_price
    Header row required. Whitespace in headers and values is stripped.
    """
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {k.strip(): v.strip() for k, v in row.items()}
            rows.append(cleaned)
    return rows


def revenue_by_category(rows):
    """Group rows by category, summing quantity * unit_price.

    Args:
        rows: List of dicts with keys 'category', 'quantity', 'unit_price'.

    Returns:
        Dict mapping category -> Decimal revenue (rounded to 2 decimal places).
    """
    revenue = defaultdict(Decimal)
    for row in rows:
        cat = row["category"]
        qty = int(row["quantity"])
        price = Decimal(row["unit_price"])
        revenue[cat] += qty * price
    return {cat: total.quantize(Decimal("0.01")) for cat, total in revenue.items()}


def format_report(revenue):
    """Format revenue dict as a plain-text CSV summary, sorted by category."""
    lines = ["Category,Revenue"]
    for cat, total in sorted(revenue.items()):
        lines.append(f"{cat},{total}")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 sales.py <csv_file>", file=sys.stderr)
        sys.exit(1)

    rows = read_sales(sys.argv[1])
    revenue = revenue_by_category(rows)
    print(format_report(revenue))


if __name__ == "__main__":
    main()
