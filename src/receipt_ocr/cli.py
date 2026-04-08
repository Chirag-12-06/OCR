from __future__ import annotations

import argparse
import json

from .cord import export_cord_crops
from .fields import extract_receipt_fields
from .ocr_engine import ReceiptOCR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Receipt OCR tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Run OCR on a receipt image")
    scan_parser.add_argument("--image", required=True, help="Path to receipt image")
    scan_parser.add_argument("--gpu", action="store_true", help="Enable GPU in EasyOCR")
    scan_parser.add_argument(
        "--lang",
        action="append",
        default=None,
        help="Language code for EasyOCR, repeatable",
    )

    cord_parser = subparsers.add_parser("prepare-cord", help="Export CORD text crops and labels")
    cord_parser.add_argument("--images", required=True, help="CORD images directory")
    cord_parser.add_argument("--annotations", required=True, help="CORD annotation directory")
    cord_parser.add_argument("--output", required=True, help="Output directory")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        engine = ReceiptOCR(languages=args.lang, gpu=args.gpu)
        tokens = engine.read(args.image)
        fields = extract_receipt_fields(tokens)
        payload = fields.to_dict()
        payload["tokens"] = engine.to_dict(tokens)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if args.command == "prepare-cord":
        exported, skipped = export_cord_crops(args.images, args.annotations, args.output)
        print(json.dumps({"exported": exported, "skipped": skipped}, indent=2))
        return

    raise ValueError(f"Unsupported command: {args.command}")
