"""Unit tests for sales.py — standard library only.

Usage:
    python3 -m unittest test_sales -v
"""

import os
import tempfile
import unittest
from decimal import Decimal

import sales


def _write_temp_csv(content):
    """Write content to a temp file, return path. Caller must os.unlink after."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return tmp.name


class ReadSalesTests(unittest.TestCase):
    """Tests for read_sales()."""

    def test_basic_csv(self):
        path = _write_temp_csv(
            "category,quantity,unit_price\n"
            "widget,2,9.99\n"
            "gadget,1,14.50\n"
        )
        try:
            rows = sales.read_sales(path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["category"], "widget")
            self.assertEqual(rows[0]["quantity"], "2")
            self.assertEqual(rows[0]["unit_price"], "9.99")
            self.assertEqual(rows[1]["category"], "gadget")
        finally:
            os.unlink(path)

    def test_header_whitespace_stripped(self):
        path = _write_temp_csv(
            " category , quantity , unit_price \n"
            "widget,2,9.99\n"
        )
        try:
            rows = sales.read_sales(path)
            self.assertIn("category", rows[0])
            self.assertNotIn(" category ", rows[0])
        finally:
            os.unlink(path)

    def test_empty_file_returns_empty_list(self):
        path = _write_temp_csv("category,quantity,unit_price\n")
        try:
            rows = sales.read_sales(path)
            self.assertEqual(rows, [])
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            sales.read_sales("/nonexistent/path.csv")


class RevenueByCategoryTests(unittest.TestCase):
    """Tests for revenue_by_category()."""

    def test_single_category(self):
        rows = [{"category": "widget", "quantity": "3", "unit_price": "10.00"}]
        result = sales.revenue_by_category(rows)
        self.assertEqual(result, {"widget": Decimal("30.00")})

    def test_multiple_rows_same_category_aggregated(self):
        rows = [
            {"category": "widget", "quantity": "2", "unit_price": "5.00"},
            {"category": "widget", "quantity": "3", "unit_price": "5.00"},
        ]
        result = sales.revenue_by_category(rows)
        self.assertEqual(result, {"widget": Decimal("25.00")})

    def test_multiple_categories(self):
        rows = [
            {"category": "widget", "quantity": "2", "unit_price": "9.99"},
            {"category": "gadget", "quantity": "1", "unit_price": "14.50"},
            {"category": "widget", "quantity": "1", "unit_price": "9.99"},
        ]
        result = sales.revenue_by_category(rows)
        expected = {
            "widget": Decimal("29.97"),
            "gadget": Decimal("14.50"),
        }
        self.assertEqual(result, expected)

    def test_rounds_to_two_decimals(self):
        rows = [
            {"category": "widget", "quantity": "1", "unit_price": "0.33"},
            {"category": "widget", "quantity": "1", "unit_price": "0.33"},
            {"category": "widget", "quantity": "1", "unit_price": "0.33"},
        ]
        result = sales.revenue_by_category(rows)
        self.assertEqual(result["widget"], Decimal("0.99"))

    def test_zero_quantity(self):
        rows = [{"category": "widget", "quantity": "0", "unit_price": "99.99"}]
        result = sales.revenue_by_category(rows)
        self.assertEqual(result, {"widget": Decimal("0.00")})

    def test_fractional_quantity_raises(self):
        rows = [{"category": "widget", "quantity": "1.5", "unit_price": "10.00"}]
        with self.assertRaises(ValueError):
            sales.revenue_by_category(rows)

    def test_missing_column_raises_key_error(self):
        rows = [{"category": "widget", "quantity": "2"}]
        with self.assertRaises(KeyError):
            sales.revenue_by_category(rows)


class FormatReportTests(unittest.TestCase):
    """Tests for format_report()."""

    def test_single_category_output(self):
        revenue = {"widget": Decimal("29.97")}
        output = sales.format_report(revenue)
        self.assertEqual(output, "Category,Revenue\nwidget,29.97")

    def test_sorted_output(self):
        revenue = {"zebra": Decimal("1.00"), "alpha": Decimal("2.00")}
        output = sales.format_report(revenue)
        lines = output.split("\n")
        self.assertEqual(lines[0], "Category,Revenue")
        self.assertEqual(lines[1], "alpha,2.00")
        self.assertEqual(lines[2], "zebra,1.00")

    def test_empty_revenue(self):
        output = sales.format_report({})
        self.assertEqual(output, "Category,Revenue")


class IntegrationTests(unittest.TestCase):
    """End-to-end: CSV file -> report."""

    def test_full_pipeline(self):
        path = _write_temp_csv(
            "category,quantity,unit_price\n"
            "widget,2,9.99\n"
            "gadget,1,14.50\n"
            "widget,1,9.99\n"
            "gizmo,3,1.25\n"
        )
        try:
            rows = sales.read_sales(path)
            revenue = sales.revenue_by_category(rows)
            report = sales.format_report(revenue)

            expected = [
                "Category,Revenue",
                "gadget,14.50",
                "gizmo,3.75",
                "widget,29.97",
            ]
            self.assertEqual(report.split("\n"), expected)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
