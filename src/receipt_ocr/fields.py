from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re

from .ocr_engine import OCRToken

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
    bill_number: str | None
    table_number: str | None
    order_number: str | None
    invoice_date: str | None
    invoice_time: str | None
    subtotal: float | None
    tax: float | None
    service_charge: float | None
    total: float | None
    currency: str | None
    payment_method: str | None
    line_items: list[LineItem]
    raw_text: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["line_items"] = [asdict(item) for item in self.line_items]
        return payload


def extract_receipt_fields(tokens: list[OCRToken]) -> ReceiptFields:
    lines = [token.text for token in tokens]
    raw_text = "\n".join(lines)
    lowered = [line.lower() for line in lines]

    merchant_name = lines[0] if lines else None
    bill_number = _extract_labeled_text(lines, ["bill no", "bill #", "invoice no", "check no", "receipt no"])
    table_number = _extract_labeled_text(lines, ["table", "tbl"])
    order_number = _extract_labeled_text(lines, ["order no", "order #", "token no", "kot"])
    invoice_date = _extract_date(lines)
    invoice_time = _extract_time(lines)
    subtotal = _extract_labeled_amount(lowered, lines, ["subtotal", "sub total", "food total", "amount"])
    tax = _extract_labeled_amount(lowered, lines, ["tax", "gst", "vat", "cgst", "sgst"])
    service_charge = _extract_labeled_amount(lowered, lines, ["service charge", "service tax", "svc"])
    total = _extract_labeled_amount(lowered, lines, ["grand total", "net total", "total"])
    currency = _detect_currency(raw_text)
    payment_method = _extract_payment_method(lowered)
    line_items = _extract_line_items(lines)

    return ReceiptFields(
        merchant_name=merchant_name,
        bill_number=bill_number,
        table_number=table_number,
        order_number=order_number,
        invoice_date=invoice_date,
        invoice_time=invoice_time,
        subtotal=subtotal,
        tax=tax,
        service_charge=service_charge,
        total=total,
        currency=currency,
        payment_method=payment_method,
        line_items=line_items,
        raw_text=raw_text,
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


def _extract_labeled_text(lines: list[str], labels: list[str]) -> str | None:
    for line in lines:
        lower = line.lower()
        if not any(label in lower for label in labels):
            continue

        parts = re.split(r"\s*[:#-]\s*", line, maxsplit=1)
        if len(parts) == 2 and parts[1].strip():
            return parts[1].strip()

        for label in labels:
            cleaned = re.sub(re.escape(label), "", line, flags=re.IGNORECASE).strip(" :#-")
            if cleaned:
                return cleaned
    return None


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


def _extract_time(lines: list[str]) -> str | None:
    for line in lines:
        match = TIME_RE.search(line)
        if match:
            return match.group(1)
    return None


def _detect_currency(text: str) -> str | None:
    markers = {
        "INR": ["rs", "inr", "₹"],
        "USD": ["usd", "$"],
        "EUR": ["eur", "€"],
        "GBP": ["gbp", "£"],
    }
    lowered = text.lower()
    for currency, hints in markers.items():
        if any(hint in lowered for hint in hints):
            return currency
    return None


def _extract_payment_method(lowered_lines: list[str]) -> str | None:
    payment_markers = {
        "upi": "UPI",
        "gpay": "UPI",
        "phonepe": "UPI",
        "paytm": "UPI",
        "visa": "CARD",
        "mastercard": "CARD",
        "card": "CARD",
        "cash": "CASH",
        "wallet": "WALLET",
    }
    for line in lowered_lines:
        for marker, value in payment_markers.items():
            if marker in line:
                return value
    return None


def _extract_line_items(lines: list[str]) -> list[LineItem]:
    items: list[LineItem] = []
    stop_markers = (
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
        name = AMOUNT_RE.sub("", line).strip(" -xX")
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
