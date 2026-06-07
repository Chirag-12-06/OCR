# OCR Expense Extractor

This project converts receipt images into structured restaurant expense data.
It first preprocesses receipt images, runs OCR with Tesseract, then uses the
OpenAI API to correct noisy OCR text and produce CSV/JSON expense tables.

## Project Structure

- `src/main.py` - full pipeline entrypoint
- `src/preprocess.py` - receipt resizing, enhancement, thresholding, and debug image output
- `src/ocr.py` - Tesseract OCR plus OCR text cleanup and confidence reporting
- `src/extractor.py` - OpenAI-based receipt parsing, normalization, deduplication, and export
- `inputs/raw/` - put raw receipt images here
- `inputs/cleaned/` - preprocessed images used for OCR
- `inputs/debug/` - intermediate preprocessing images for inspection
- `inputs/bills_cleaned.txt` - OCR text generated from cleaned images
- `outputs/csv/expenses_table.csv` - generated flat expense table
- `outputs/json/expenses_table.json` - generated structured expense data

## What It Does

1. Reads `.jpg`, `.jpeg`, and `.png` images from `inputs/raw/`.
2. Resizes, enhances, and thresholds each receipt image.
3. Saves cleaned images to `inputs/cleaned/` and debug images to `inputs/debug/`.
4. Runs Tesseract OCR on cleaned images and writes text to `inputs/bills_cleaned.txt`.
5. Sends the OCR text to OpenAI for receipt parsing and OCR word correction.
6. Normalizes tax data so each item gets:
   - `tax_percentage`
   - `taxes_and_charges_allocated`
   - `final_item_amount`
7. Deduplicates repeated bills when OCR splits one receipt into multiple merchant names.
8. Writes the final outputs to `outputs/csv/` and `outputs/json/`.

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install Tesseract OCR and make sure this path exists, or update
`pytesseract.pytesseract.tesseract_cmd` in `src/ocr.py`:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

Set your OpenAI API key:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

You can optionally set a model name:

```powershell
$env:OPENAI_MODEL="gpt-4o-mini"
```

## Usage

Put receipt images in:

```text
inputs/raw/
```

Run the full pipeline:

```bash
python src/main.py
```

Optional extractor arguments can also be passed through the main script:

```bash
python src/main.py --input inputs/bills_cleaned.txt --csv outputs/csv/expenses_table.csv --json outputs/json/expenses_table.json --model gpt-4o-mini --max-retries 3
```

## Outputs

CSV rows include:

- `source_file`
- `restaurant_name`
- `date`
- `currency`
- `item_name`
- `quantity`
- `unit_price`
- `base_amount`
- `tax_percentage`
- `taxes_and_charges_allocated`
- `final_item_amount`
- `confidence`
- `warnings`

The JSON output contains bill-level metadata, item details, taxes and charges,
subtotal, confidence, and warnings. The extractor does not write a bill-level
final amount field.

## Notes

- OCR text can be noisy, so the OpenAI prompt asks the model to autocorrect
  obvious letter errors when the surrounding context makes the intended word clear.
- Duplicate bills are collapsed when the extractor sees the same receipt content
  under different merchant names.
- OpenAI rate limits are retried automatically. Quota and billing errors are
  reported with a clearer message.
