import sys
import unittest
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from services.dataset_validation import validate_excel_upload


def workbook_bytes(headers: list[str], rows: list[list[object]] | None = None) -> BytesIO:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in rows or [["2W", "scooter", "Ola", 90000, 108, 2.0]]:
        worksheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    buffer.seek(0)
    return buffer


class DatasetValidationTests(unittest.TestCase):
    def test_valid_dataset_upload_returns_profile(self):
        file_obj = workbook_bytes(
            ["Category", "Vehicle_Type", "Brand", "Approx_Price_INR", "Range_km", "Battery_kWh"]
        )

        result = validate_excel_upload(
            filename="ev_dataset.xlsx",
            file_obj=file_obj,
            max_bytes=1_000_000,
        )

        self.assertEqual(result.rows, 1)
        self.assertIn("approx_price_inr", result.columns)

    def test_missing_required_columns_is_rejected(self):
        file_obj = workbook_bytes(["Category", "Brand", "Model"])

        with self.assertRaisesRegex(ValueError, "missing required columns"):
            validate_excel_upload(filename="ev_dataset.xlsx", file_obj=file_obj, max_bytes=1_000_000)

    def test_non_xlsx_extension_is_rejected(self):
        file_obj = workbook_bytes(
            ["Category", "Vehicle_Type", "Brand", "Approx_Price_INR", "Range_km", "Battery_kWh"]
        )

        with self.assertRaisesRegex(ValueError, "Only .xlsx"):
            validate_excel_upload(filename="ev_dataset.csv", file_obj=file_obj, max_bytes=1_000_000)

    def test_invalid_workbook_content_is_rejected(self):
        file_obj = BytesIO(b"not an excel workbook")

        with self.assertRaisesRegex(ValueError, "not a valid|could not be opened"):
            validate_excel_upload(filename="ev_dataset.xlsx", file_obj=file_obj, max_bytes=1_000_000)

    def test_oversized_upload_is_rejected(self):
        file_obj = workbook_bytes(
            ["Category", "Vehicle_Type", "Brand", "Approx_Price_INR", "Range_km", "Battery_kWh"]
        )

        with self.assertRaisesRegex(ValueError, "exceeds"):
            validate_excel_upload(filename="ev_dataset.xlsx", file_obj=file_obj, max_bytes=10)


if __name__ == "__main__":
    unittest.main()
