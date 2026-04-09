from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class OCRToken:
    bbox: list[list[float]]
    text: str
    confidence: float
