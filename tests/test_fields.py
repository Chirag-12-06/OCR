from receipt_ocr.fields import extract_receipt_fields
from receipt_ocr.types import OCRToken


def test_extract_receipt_fields_basic_totals() -> None:
    tokens = [
        OCRToken(bbox=[[0, 0], [1, 0], [1, 1], [0, 1]], text="Spice Route Bistro", confidence=0.99),
        OCRToken(bbox=[[0, 1], [1, 1], [1, 2], [0, 2]], text="Bill No: 1042", confidence=0.98),
        OCRToken(bbox=[[0, 2], [1, 2], [1, 3], [0, 3]], text="Table: A12", confidence=0.98),
        OCRToken(bbox=[[0, 3], [1, 3], [1, 4], [0, 4]], text="01/04/2026 13:44", confidence=0.98),
        OCRToken(bbox=[[0, 4], [1, 4], [1, 5], [0, 5]], text="2 x Masala Dosa 180.00 360.00", confidence=0.97),
        OCRToken(bbox=[[0, 5], [1, 5], [1, 6], [0, 6]], text="Service Charge 20.00", confidence=0.95),
        OCRToken(bbox=[[0, 6], [1, 6], [1, 7], [0, 7]], text="Tax 21.00", confidence=0.95),
        OCRToken(bbox=[[0, 7], [1, 7], [1, 8], [0, 8]], text="Grand Total 401.00", confidence=0.96),
        OCRToken(bbox=[[0, 8], [1, 8], [1, 9], [0, 9]], text="Paid by UPI", confidence=0.94),
    ]

    fields = extract_receipt_fields(tokens)

    assert fields.merchant_name == "Spice Route Bistro"
    assert fields.invoice_date == "2026-04-01"
    assert fields.tax == 21.0
    assert fields.total == 401.0
    assert fields.line_items[0].name == "Masala Dosa"
    assert fields.line_items[0].quantity == 2.0
    assert fields.line_items[0].unit_price == 180.0
