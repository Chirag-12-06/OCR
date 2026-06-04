import os
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FOLDER = PROJECT_ROOT / "inputs" / "bills"
OUTPUT_FOLDER = PROJECT_ROOT / "inputs" / "bills_cleaned"


def image_cleaning(input_folder, output_folder):
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

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # Determine if image is a digital screenshot/scan or a camera photo
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                max_peak = np.max(hist)
                total_pixels = gray.size
                peak_val = np.argmax(hist)
                neighborhood_sum = np.sum(hist[max(0, peak_val-2):min(256, peak_val+3)])
                neighborhood_ratio = neighborhood_sum / total_pixels

                is_screenshot = neighborhood_ratio > 0.5

                if is_screenshot:
                    # Digital screenshot: Resize 2.5x, very mild denoise (h=3)
                    gray_resized = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
                    denoised = cv2.fastNlMeansDenoising(gray_resized, None, 3, 7, 21)
                else:
                    # Camera photo: Resize 2.0x, mild denoise (h=5)
                    gray_resized = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                    denoised = cv2.fastNlMeansDenoising(gray_resized, None, 5, 7, 21)

                # Sharpening
                kernel = np.array([
                    [-1,-1,-1],
                    [-1, 9,-1],
                    [-1,-1,-1]
                ])
                sharp = cv2.filter2D(denoised, -1, kernel)

                # Global Otsu Thresholding works perfectly after sharpening and proper scaling
                _, thresh = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                black_pixels = np.sum(thresh == 0)
                white_pixels = np.sum(thresh == 255)

                if black_pixels > white_pixels:
                    thresh = cv2.bitwise_not(thresh)

                cv2.imwrite(output_path, thresh)
                print(f"Processed: {filename}")

            except Exception as e:
                print(f"Problem processing {filename}: {e}")


if __name__ == "__main__":
    image_cleaning(INPUT_FOLDER, OUTPUT_FOLDER)
