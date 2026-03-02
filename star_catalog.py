from __future__ import annotations

from dataclasses import dataclass
import csv
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class CatalogStar:
    name: str
    ra_deg: float
    dec_deg: float
    mag: float


def load_bright_star_catalog(path: str = "data/bright_stars.csv") -> List[CatalogStar]:
    rows: List[CatalogStar] = []
    with Path(path).open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                CatalogStar(
                    name=r["name"],
                    ra_deg=float(r["ra_deg"]),
                    dec_deg=float(r["dec_deg"]),
                    mag=float(r["mag"]),
                )
            )
    rows.sort(key=lambda s: s.mag)
    return rows
