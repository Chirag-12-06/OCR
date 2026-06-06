import os
import re
from pathlib import Path

import cv2
import pytesseract


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FOLDER = PROJECT_ROOT / "inputs" / "cleaned"

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def clean_ocr_text(text):

    # Z499, %499, $499 → INR 499
    text = re.sub(
        r'(?<!\w)[Z%$£€](?=\d)',
        'INR ',
        text
    )

    # 2499 → INR 499 (only for 4+ digit amounts)
    text = re.sub(
        r'(?<!\d)2(\d{3,})(?!\d)',
        r'INR \1',
        text
    )

    return text

def calculate_confidence(data: dict) -> float:
    """
    Calculate average OCR confidence.
    """

    confidences = []

    for conf in data["conf"]:
        try:
            conf = float(conf)

            if conf > 0:
                confidences.append(conf)

        except ValueError:
            pass

    if not confidences:
        return 0.0

    return round(
        sum(confidences) / len(confidences),
        2
    )

def extract_text(image_path: Path) -> dict:
    """
    OCR a single image and return text + confidence.
    """

    img = cv2.imread(str(image_path))

    if img is None:
        raise ValueError(
            f"Failed to load image: {image_path}"
        )

    config = (
        '--oem 3 '
        '--psm 4 '
        '-c tessedit_char_whitelist='
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        'abcdefghijklmnopqrstuvwxyz'
        '0123456789'
        '.,:/%-#()% '
    )
    text = pytesseract.image_to_string(
        img,
        config=config
    )

    text = clean_ocr_text(text)
    
    text = re.sub(r'[-_=]{3,}', '', text)

    text = re.sub(r'\n\s*\n+', '\n\n', text)

    data = pytesseract.image_to_data(
        img,
        config=config,
        output_type=pytesseract.Output.DICT
    )

    confidence = calculate_confidence(data)

    return {
        "text": text,
        "confidence": confidence
    }

def ocr(input_folder: Path, output_file: Path):
    """
    OCR all images in a folder and save extracted text.
    """

    results = []

    valid_extensions = (
        ".jpg",
        ".jpeg",
        ".png"
    )

    extracted_text = ""

    for filename in os.listdir(input_folder):

        if not filename.lower().endswith(valid_extensions):
            continue

        image_path = input_folder / filename

        try:

            result = extract_text(image_path)

            results.append({
                "filename": filename,
                "text": result["text"],
                "confidence": result["confidence"]
            })

            print(
                f"{filename} | Confidence: "
                f"{result['confidence']}%"
            )

            extracted_text += (
                f"Extracted text from {filename}:\n"
                f"{result['text'].strip()}\n\n"
            )

        except Exception as e:

            print(
                f"Problem processing "
                f"{filename}: {e}"
            )

    # Create parent directory if needed
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save OCR text
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(extracted_text)

    print(f"OCR text written to {output_file}")

    return results