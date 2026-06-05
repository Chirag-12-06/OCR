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


def clean_ocr_text(text: str) -> str:
    """
    Fix common OCR mistakes.
    """

    text = re.sub(
        r'(?<=\s)[Z$](?=\d)',
        'INR ',
        text
    )

    text = re.sub(
        r'INR\s*2(\d{2,})',
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

    config = r'--oem 3 --psm 4'

    text = pytesseract.image_to_string(
        img,
        config=config
    )

    text = clean_ocr_text(text)

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


def ocr(input_folder: Path):
    """
    OCR all images in a folder.
    """

    results = []

    valid_extensions = (
        ".jpg",
        ".jpeg",
        ".png"
    )

    for filename in os.listdir(input_folder):

        if not filename.lower().endswith(valid_extensions):
            continue

        image_path = Path(input_folder) / filename

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

        except Exception as e:

            print(
                f"Problem processing "
                f"{filename}: {e}"
            )

    return results


if __name__ == "__main__":

    results = ocr(INPUT_FOLDER)

    for result in results:

        print("\n" + "=" * 60)

        print(
            f"File: {result['filename']}"
        )

        print(
            f"Confidence: "
            f"{result['confidence']}%"
        )

        print(result["text"])