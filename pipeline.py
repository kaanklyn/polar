"""Fotoğraf + tarih girdisinden basitleştirilmiş konum tahmini akışı."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from astronomy import parse_utc
from vision import StarPoint, detect_star_points


@dataclass
class PhotoEstimate:
    latitude_deg: float | None
    longitude_deg: float | None
    confidence: float
    note: str


def estimate_from_detected_stars(width: int, height: int, stars: Sequence[StarPoint]) -> PhotoEstimate:
    if not stars:
        raise ValueError("Yıldız noktası bulunamadı.")

    # Önemli düzeltme:
    # Sadece "fotoğraf + tarih" ile ve yıldız kimliği bilinmeden,
    # güvenilir enlem/boylam üretmek fiziksel olarak mümkün değildir.
    # Önceki sürümde bu yüzden 90° gibi yanıltıcı değerler üretilebiliyordu.
    return PhotoEstimate(
        latitude_deg=None,
        longitude_deg=None,
        confidence=0.0,
        note=(
            "Bu girdi setiyle (yalnız fotoğraf+tarih) konum güvenilir hesaplanamaz. "
            "En az bir yıldız kimliği (ör. Polaris) veya IMU/yön bilgisi gerekir."
        ),
    )


def estimate_from_image_and_utc(image_path: str, utc_str: str) -> tuple[datetime, PhotoEstimate]:
    utc_dt = parse_utc(utc_str)
    width, height, stars = detect_star_points(image_path)
    return utc_dt, estimate_from_detected_stars(width, height, stars)
