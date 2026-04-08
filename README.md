# Receipt OCR Starter

This project is a starter pipeline for extracting structured details from restaurant and food-service bills.

It includes:

- EasyOCR-based text detection and recognition
- restaurant bill parsing for bill number, table, order references, totals, taxes, service charge, payment method, and line items
- CORD dataset preparation utilities for training or evaluation

## 1. Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## 2. Run OCR on a receipt image

```powershell
receipt-ocr scan --image path\to\receipt.jpg
```

Example output:

```json
{
  "merchant_name": "Spice Route Bistro",
  "bill_number": "1042",
  "table_number": "A12",
  "order_number": null,
  "invoice_date": "2026-04-01",
  "invoice_time": "13:44",
  "subtotal": 420.0,
  "tax": 21.0,
  "service_charge": 20.0,
  "total": 441.0,
  "currency": "INR",
  "payment_method": "UPI",
  "line_items": [
    {
      "name": "Masala Dosa",
      "quantity": 2.0,
      "unit_price": 180.0,
      "total_price": 360.0
    }
  ],
  "raw_text": "..."
}
```

## 3. Prepare CORD data for recognizer training

The command below reads CORD-style JSON annotations and exports cropped text regions and labels.

```powershell
python -m receipt_ocr.cli prepare-cord `
  --images data\cord\image `
  --annotations data\cord\json `
  --output data\prepared\cord_easyocr
```

This produces:

- `images/`: cropped text samples
- `labels.tsv`: `relative_image_path<TAB>text`

That output is useful for training or benchmarking a recognizer on receipt text.

## 4. Project layout

- `src/receipt_ocr/ocr_engine.py`: EasyOCR wrapper
- `src/receipt_ocr/fields.py`: receipt field extraction
- `src/receipt_ocr/cord.py`: dataset preparation helpers
- `src/receipt_ocr/cli.py`: command line entrypoint

## 5. Notes

- This starter focuses on printed restaurant receipts, not handwriting.
- CORD is helpful for receipt-domain adaptation, but you will likely want to add your own restaurant bill samples later.
- For best restaurant performance, add dine-in bills, takeaway receipts, cafe invoices, and POS printouts from your target vendors.
- EasyOCR training usually works best after creating clean text crops and labels first, which is why the CORD export step is included now.
