#!/usr/bin/env python3
"""Import the newest BirdNET Live ZIP into BirdCanvas' canonical JSON format."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLD = 0.70
DEFAULT_IMPORTS_DIR = Path("imports")
DEFAULT_OUTPUT = Path("data/today.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import detections from a BirdNET Live ZIP export."
    )
    parser.add_argument(
        "zip_file",
        nargs="?",
        type=Path,
        help="BirdNET ZIP to import. If omitted, the newest ZIP in imports/ is used.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum confidence to retain (default: {DEFAULT_THRESHOLD:.2f}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT}).",
    )
    return parser.parse_args()


def newest_zip(imports_dir: Path) -> Path:
    zip_files = [path for path in imports_dir.glob("*.zip") if path.is_file()]
    if not zip_files:
        raise FileNotFoundError(
            f"No ZIP files found in {imports_dir.resolve()}. "
            "Upload a BirdNET export ZIP there first."
        )
    return max(zip_files, key=lambda path: path.stat().st_mtime)


def read_zip_member(archive: zipfile.ZipFile, suffix: str) -> tuple[str, bytes]:
    matches = [name for name in archive.namelist() if name.lower().endswith(suffix)]
    if not matches:
        raise ValueError(f"The ZIP does not contain a {suffix} file.")
    if len(matches) > 1:
        raise ValueError(f"The ZIP contains more than one {suffix} file: {matches}")
    name = matches[0]
    return name, archive.read(name)


def session_date(metadata: dict[str, Any], zip_path: Path) -> str:
    possible_keys = (
        "startDate",
        "start_date",
        "startTime",
        "start_time",
        "date",
        "createdAt",
    )
    for key in possible_keys:
        value = metadata.get(key)
        if isinstance(value, str):
            match = re.search(r"\d{4}-\d{2}-\d{2}", value)
            if match:
                return match.group(0)

    match = re.search(r"\d{4}-\d{2}-\d{2}", zip_path.name)
    if match:
        return match.group(0)

    return date.today().isoformat()


def parse_detections(tsv_bytes: bytes, threshold: float) -> tuple[list[dict[str, Any]], int]:
    text = tsv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")

    required = {"Common Name", "Scientific Name", "Confidence"}
    headers = set(reader.fieldnames or [])
    missing = required - headers
    if missing:
        raise ValueError(
            "BirdNET selections file is missing required columns: "
            + ", ".join(sorted(missing))
        )

    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"detections": 0, "highest_confidence": 0.0}
    )
    total_rows = 0

    for row in reader:
        total_rows += 1
        common_name = (row.get("Common Name") or "").strip()
        scientific_name = (row.get("Scientific Name") or "").strip()
        confidence_text = (row.get("Confidence") or "").strip()

        if not common_name or not confidence_text:
            continue

        try:
            confidence = float(confidence_text)
        except ValueError:
            continue

        if confidence < threshold:
            continue

        key = (common_name, scientific_name)
        grouped[key]["detections"] += 1
        grouped[key]["highest_confidence"] = max(
            grouped[key]["highest_confidence"], confidence
        )

    observations = []
    for (common_name, scientific_name), values in grouped.items():
        observations.append(
            {
                "species": common_name,
                "scientific_name": scientific_name,
                "confidence": round(values["highest_confidence"], 4),
                "detections": values["detections"],
            }
        )

    observations.sort(key=lambda item: (-item["confidence"], item["species"]))
    return observations, total_rows


def import_zip(zip_path: Path, output_path: Path, threshold: float) -> dict[str, Any]:
    if not 0 <= threshold <= 1:
        raise ValueError("Confidence threshold must be between 0 and 1.")
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    with zipfile.ZipFile(zip_path) as archive:
        selections_name, selections_bytes = read_zip_member(
            archive, ".selections.txt"
        )

        metadata: dict[str, Any] = {}
        metadata_matches = [
            name for name in archive.namelist() if name.lower().endswith(".metadata.json")
        ]
        if metadata_matches:
            try:
                metadata = json.loads(archive.read(metadata_matches[0]).decode("utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                metadata = {}

    observations, total_rows = parse_detections(selections_bytes, threshold)
    if not observations:
        raise ValueError(
            f"No detections met the confidence threshold of {threshold:.2f}."
        )

    result = {
        "schema_version": 1,
        "date": session_date(metadata, zip_path),
        "source": "birdnet_live_phone",
        "source_file": zip_path.name,
        "confidence_threshold": threshold,
        "birds": [item["species"] for item in observations],
        "observations": observations,
        "import_summary": {
            "rows_read": total_rows,
            "species_retained": len(observations),
            "selections_file": selections_name,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    args = parse_args()

    try:
        zip_path = args.zip_file or newest_zip(DEFAULT_IMPORTS_DIR)
        result = import_zip(zip_path, args.output, args.threshold)
    except (FileNotFoundError, ValueError, zipfile.BadZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Imported {len(result['observations'])} species from {zip_path.name}")
    for observation in result["observations"]:
        print(
            f"  - {observation['species']}: "
            f"{observation['confidence']:.4f} "
            f"({observation['detections']} detection"
            f"{'s' if observation['detections'] != 1 else ''})"
        )
    print(f"Saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())