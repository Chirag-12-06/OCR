from preprocess import image_cleaning
from ocr import ocr
from extractor import extract
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# INPUTS
INPUT_FOLDER = PROJECT_ROOT / "inputs"
RAW_FOLDER = INPUT_FOLDER / "raw"
CLEANED_FOLDER = INPUT_FOLDER / "cleaned"
DEBUG_FOLDER = INPUT_FOLDER / "debug"
OCR_TEXT_FILE = INPUT_FOLDER / "bills_cleaned.txt"

# OUTPUTS
OUTPUT_FOLDER = PROJECT_ROOT / "outputs"
CSV_FOLDER = OUTPUT_FOLDER / "csv"
JSON_FOLDER = OUTPUT_FOLDER / "json"

CSV_FILE = CSV_FOLDER / "expenses_table.csv"
JSON_FILE = JSON_FOLDER / "expenses_table.json"


def main():

    image_cleaning(PROJECT_ROOT, RAW_FOLDER, CLEANED_FOLDER)

    ocr(CLEANED_FOLDER, OCR_TEXT_FILE)

    extract(OCR_TEXT_FILE, OUTPUT_FOLDER, CSV_FILE, JSON_FILE)

if __name__ == "__main__":
    main()