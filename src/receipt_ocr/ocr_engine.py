from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import easyocr

from .preprocess import load_image, normalize_for_ocr


@dataclass(slots=True)
class OCRToken:
    bbox: list[list[float]]
    text: str
    confidence: float


class ReceiptOCR:
    def __init__(self, languages: list[str] | None = None, gpu: bool = False) -> None:
        self.languages = languages or ["en"]
        self.reader = easyocr.Reader(self.languages, gpu=gpu)

    def read(self, image_path: str | Path) -> list[OCRToken]:
        image = load_image(image_path)
        normalized = normalize_for_ocr(image)
        results = self.reader.readtext(normalized)
        tokens: list[OCRToken] = []
        for bbox, text, confidence in results:
            cleaned = text.strip()
            if not cleaned:
                continue
            tokens.append(
                OCRToken(
                    bbox=[[float(x), float(y)] for x, y in bbox],
                    text=cleaned,
                    confidence=float(confidence),
                )
            )
        return tokens

    @staticmethod
    def to_dict(tokens: list[OCRToken]) -> list[dict[str, Any]]:
        return [
            {
                "bbox": token.bbox,
                "text": token.text,
                "confidence": token.confidence,
            }
            for token in tokens
        ]
