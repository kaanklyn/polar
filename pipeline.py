"""Fotoğraf + tarih girdisinden basitleştirilmiş konum tahmini akışı."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from astronomy import estimate_lat_from_polaris, parse_utc
from vision import StarPoint, detect_star_points, pixel_to_alt_az


@dataclass
class PhotoEstimate:
    latitude_deg: float
    longitude_deg: float | None
    confidence: float
    note: str


def estimate_from_detected_stars(width: int, height: int, stars: Sequence[StarPoint]) -> PhotoEstimate:
    if not stars:
        raise ValueError("Yıldız noktası bulunamadı.")

    # Kullanıcı isteğine göre sabit varsayım:
    # Telefon arka kamera direkt gökyüzüne bakıyor (zenith), yani camera_alt = 90.
    camera_az_deg = 0.0
    camera_alt_deg = 90.0
    hfov_deg = 60.0
    vfov_deg = 60.0

    highest = min(stars, key=lambda s: s.y)
    polaris_alt, _ = pixel_to_alt_az(
        highest.x,
        highest.y,
        width,
        height,
        camera_az_deg,
        camera_alt_deg,
        hfov_deg,
        vfov_deg,
    )
    latitude = estimate_lat_from_polaris(polaris_alt)

    # Bu MVP'de yalnız fotoğraf+tarih ile boylam güvenilir hesaplanamaz.
    return PhotoEstimate(
        latitude_deg=latitude,
        longitude_deg=None,
        confidence=0.45,
        note="Bu sürümde sadece enlem tahmini yapılır. Boylam için yıldız kimlik eşleme gerekir.",
    )


def estimate_from_image_and_utc(image_path: str, utc_str: str) -> tuple[datetime, PhotoEstimate]:
    utc_dt = parse_utc(utc_str)
    width, height, stars = detect_star_points(image_path)
    return utc_dt, estimate_from_detected_stars(width, height, stars)
