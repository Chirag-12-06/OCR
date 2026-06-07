import os
import cv2
from pathlib import Path

def resize_receipt(img):
    return cv2.resize(
        img,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

def enhance_receipt(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Remove lighting variations
    blur = cv2.GaussianBlur(gray, (51, 51), 0)

    normalized = cv2.divide(
        gray,
        blur,
        scale=255
    )

    return normalized

def image_cleaning(project_root,input_folder, output_folder):
    validate_Extensions = (".jpg", ".jpeg", ".png")

    for filename in os.listdir(input_folder):

        if filename.lower().endswith(validate_Extensions):

            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            try:
                img = cv2.imread(input_path)

                if img is None:
                    print(f"Failed to load {filename}")
                    continue

                debug_path = project_root / "inputs" / "debug"

                # Step 1
                resized = resize_receipt(img)

                # Step 2
                enhanced = enhance_receipt(resized)

                # Step 3
                thresh = cv2.adaptiveThreshold(
                    enhanced,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    31,
                    15
                )

                # Save debug images
                stem = Path(filename).stem

                cv2.imwrite(
                    str(debug_path / f"{stem}_resized.jpg"),
                    resized
                )

                cv2.imwrite(
                    str(debug_path / f"{stem}_enhanced.jpg"),
                    enhanced
                )

                cv2.imwrite(
                    str(debug_path / f"{stem}_threshold.jpg"),
                    thresh
                )

                # Final image used by OCR
                cv2.imwrite(output_path, thresh)

                print(f"Processed: {filename}")

            except Exception as e:
                print(f"Problem processing {filename}: {e}")

