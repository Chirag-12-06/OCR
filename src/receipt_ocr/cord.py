from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np


@dataclass(slots=True)
class CordSample:
    image_path: Path
    annotation_path: Path


def iter_cord_samples(images_dir: str | Path, annotations_dir: str | Path) -> Iterable[CordSample]:
    images_root = Path(images_dir)
    annotations_root = Path(annotations_dir)
    for annotation_path in sorted(annotations_root.glob("*.json")):
        stem = annotation_path.stem
        image_path = _find_image(images_root, stem)
        if image_path is None:
            continue
        yield CordSample(image_path=image_path, annotation_path=annotation_path)


def export_cord_crops(images_dir: str | Path, annotations_dir: str | Path, output_dir: str | Path) -> tuple[int, int]:
    output_root = Path(output_dir)
    crop_dir = output_root / "images"
    crop_dir.mkdir(parents=True, exist_ok=True)
    labels_path = output_root / "labels.tsv"

    exported = 0
    skipped = 0
    label_lines: list[str] = []

    for sample in iter_cord_samples(images_dir, annotations_dir):
        image = cv2.imread(str(sample.image_path))
        if image is None:
            skipped += 1
            continue

        payload = json.loads(sample.annotation_path.read_text(encoding="utf-8"))
        regions = _collect_text_regions(payload)

        for index, region in enumerate(regions):
            text = str(region.get("text", "")).strip()
            vertices = _extract_vertices(region)
            if not text or len(vertices) < 4:
                skipped += 1
                continue

            crop = _crop_polygon(image, vertices)
            if crop.size == 0:
                skipped += 1
                continue

            filename = f"{sample.annotation_path.stem}_{index:04d}.png"
            relative_path = Path("images") / filename
            cv2.imwrite(str(crop_dir / filename), crop)
            label_lines.append(f"{relative_path.as_posix()}\t{text}")
            exported += 1

    labels_path.write_text("\n".join(label_lines), encoding="utf-8")
    return exported, skipped


def _find_image(images_root: Path, stem: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg"):
        candidate = images_root / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def _collect_text_regions(node: Any) -> list[dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if "text" in node and any(key in node for key in ("quad", "box", "boundingBox", "vertices", "polygon")):
            regions.append(node)
        for value in node.values():
            regions.extend(_collect_text_regions(value))
    elif isinstance(node, list):
        for item in node:
            regions.extend(_collect_text_regions(item))
    return regions


def _extract_vertices(region: dict[str, Any]) -> np.ndarray:
    if "quad" in region:
        return _to_vertices(region["quad"])
    if "polygon" in region:
        return _to_vertices(region["polygon"])
    if "vertices" in region:
        return _to_vertices(region["vertices"])
    if "boundingBox" in region:
        return _to_vertices(region["boundingBox"])
    if "box" in region:
        return _to_vertices(region["box"])
    return np.empty((0, 2), dtype=np.float32)


def _to_vertices(raw: Any) -> np.ndarray:
    points: list[list[float]] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and {"x", "y"} <= set(item):
                points.append([float(item["x"]), float(item["y"])])
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                points.append([float(item[0]), float(item[1])])
    return np.array(points, dtype=np.float32)


def _crop_polygon(image: np.ndarray, vertices: np.ndarray) -> np.ndarray:
    x, y, w, h = cv2.boundingRect(vertices.astype(np.int32))
    if w <= 0 or h <= 0:
        return np.empty((0, 0, 3), dtype=np.uint8)
    cropped = image[y : y + h, x : x + w]
    return cropped
