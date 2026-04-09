from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re

from .types import OCRToken

AMOUNT_RE = re.compile(r"(?<!\d)(\d{1,6}(?:[.,]\d{2})?)(?!\d)")
DATE_PATTERNS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%d/%m/%y",
    "%d-%m-%y",
]
TIME_RE = re.compile(r"\b(\d{1,2}:\d{2})(?::\d{2})?\b")


@dataclass(slots=True)
class LineItem:
    name: str
    quantity: float | None
    unit_price: float | None
    total_price: float | None


@dataclass(slots=True)
class ReceiptFields:
    merchant_name: str | None
    invoice_date: str | None
    tax: float | None
    total: float | None
    line_items: list[LineItem]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["line_items"] = [asdict(item) for item in self.line_items]
        return payload


def extract_receipt_fields(tokens: list[OCRToken]) -> ReceiptFields:
    lines = [token.text for token in tokens]
    lowered = [line.lower() for line in lines]

    merchant_name = lines[0] if lines else None
    invoice_date = _extract_date(lines)
    tax = _extract_labeled_amount(lowered, lines, ["tax", "gst", "vat", "cgst", "sgst"])
    total = _extract_labeled_amount(lowered, lines, ["grand total", "net total", "total"])
    line_items = _extract_line_items(lines)

    return ReceiptFields(
        merchant_name=merchant_name,
        invoice_date=invoice_date,
        tax=tax,
        total=total,
        line_items=line_items,
    )


def _extract_labeled_amount(lowered_lines: list[str], original_lines: list[str], labels: list[str]) -> float | None:
    for lower, original in zip(lowered_lines, original_lines, strict=False):
        if any(label in lower for label in labels):
            amounts = _extract_amounts(original)
            if amounts:
                return max(amounts)
    return None


def _extract_amounts(text: str) -> list[float]:
    values: list[float] = []
    for match in AMOUNT_RE.findall(text):
        normalized = match.replace(",", ".")
        try:
            values.append(float(normalized))
        except ValueError:
            continue
    return values


def _extract_date(lines: list[str]) -> str | None:
    for line in lines:
        for chunk in re.split(r"\s+", line):
            cleaned = chunk.strip(" ,:")
            for pattern in DATE_PATTERNS:
                try:
                    return datetime.strptime(cleaned, pattern).date().isoformat()
                except ValueError:
                    continue
    return None


def _extract_line_items(lines: list[str]) -> list[LineItem]:
    items: list[LineItem] = []
    stop_markers = (
        "bill",
        "invoice",
        "receipt",
        "subtotal",
        "tax",
        "total",
        "cash",
        "card",
        "payment",
        "change",
        "table",
        "order",
        "kot",
        "date",
        "time",
        "server",
        "waiter",
        "guest",
        "covers",
    )
    for line in lines[1:]:
        lower = line.lower()
        if any(marker in lower for marker in stop_markers):
            continue
        amounts = _extract_amounts(line)
        if not amounts:
            continue
        name = _clean_item_name(line)
        if len(name) < 2:
            continue
        quantity = None
        quantity_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:x|qty|kg|g|l|ml|pcs|pc|plate|plates)\b", lower)
        if quantity_match:
            quantity = float(quantity_match.group(1))
        elif len(amounts) >= 3:
            quantity = amounts[0]
        unit_price = amounts[-2] if len(amounts) >= 2 else None
        total_price = amounts[-1]
        items.append(
            LineItem(
                name=name.strip(),
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
        )
    return items


def _clean_item_name(line: str) -> str:
    name = AMOUNT_RE.sub(" ", line)
    name = re.sub(r"\b\d+(?:\.\d+)?\s*x\b", " ", name, flags=re.IGNORECASE)
    name = re.sub(r"\b(?:qty|pcs|pc|plate|plates)\b", " ", name, flags=re.IGNORECASE)
    name = re.sub(r"[^A-Za-z&()'/+\- ]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" -xX:/")
    return name
