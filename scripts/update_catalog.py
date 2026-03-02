#!/usr/bin/env python3
"""Download and freeze bright-star catalog from a remote source.

Usage:
  python3 scripts/update_catalog.py

This script downloads HYG v3 dataset, extracts bright named stars,
and writes:
- data/bright_stars.csv
- data/bright_stars.source.json
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
from typing import Iterable, List
from urllib.request import urlopen

SOURCE_URL = "https://raw.githubusercontent.com/astronexus/HYG-Database/master/hygdata_v3.csv"
OUT_CSV = Path("data/bright_stars.csv")
OUT_META = Path("data/bright_stars.source.json")


@dataclass(frozen=True)
class CatalogRow:
    name: str
    ra_deg: float
    dec_deg: float
    mag: float


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().split())


def build_rows_from_hyg_csv(hyg_csv_text: str, mag_limit: float = 1.7, max_rows: int = 80) -> List[CatalogRow]:
    rows: List[CatalogRow] = []
    reader = csv.DictReader(io.StringIO(hyg_csv_text))

    for r in reader:
        proper = _normalize_name(r.get("proper", ""))
        if not proper:
            continue

        mag_str = (r.get("mag", "") or "").strip()
        ra_hours_str = (r.get("ra", "") or "").strip()
        dec_str = (r.get("dec", "") or "").strip()
        if not mag_str or not ra_hours_str or not dec_str:
            continue

        try:
            mag = float(mag_str)
            ra_deg = float(ra_hours_str) * 15.0
            dec_deg = float(dec_str)
        except ValueError:
            continue

        if mag > mag_limit:
            continue

        rows.append(CatalogRow(name=proper, ra_deg=ra_deg, dec_deg=dec_deg, mag=mag))

    # keep unique by name, brightest first
    rows.sort(key=lambda x: x.mag)
    uniq: List[CatalogRow] = []
    seen = set()
    for r in rows:
        key = r.name.lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
        if len(uniq) >= max_rows:
            break

    return uniq


def write_catalog(rows: Iterable[CatalogRow], out_csv: Path) -> int:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "ra_deg", "dec_deg", "mag"])
        for r in rows:
            w.writerow([r.name, f"{r.ra_deg:.6f}", f"{r.dec_deg:.6f}", f"{r.mag:.2f}"])
            count += 1
    return count


def main() -> None:
    raw = urlopen(SOURCE_URL, timeout=30).read()
    source_sha256 = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8", errors="replace")

    rows = build_rows_from_hyg_csv(text)
    count = write_catalog(rows, OUT_CSV)

    meta = {
        "source_url": SOURCE_URL,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": source_sha256,
        "row_count": count,
        "format": "name,ra_deg,dec_deg,mag",
        "generator": "scripts/update_catalog.py",
    }
    OUT_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {count} rows -> {OUT_CSV}")
    print(f"Wrote metadata -> {OUT_META}")


if __name__ == "__main__":
    main()
