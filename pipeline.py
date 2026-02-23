"""Fotoğraf + tarih girdisinden basitleştirilmiş konum tahmini akışı."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from astronomy import parse_utc
from star_catalog import load_bright_star_catalog
from star_matcher import MatchedStar, match_stars_from_points
from vision import StarPoint, detect_star_points
from location_solver import solve_location_from_matches

MAX_ACCEPTABLE_RMS_DEG = 12.0
SOFT_RMS_DEG = 6.0


@dataclass
class PhotoEstimate:
    latitude_deg: float | None
    longitude_deg: float | None
    location_confidence: float
    match_confidence: float
    note: str
    matched_stars: list[MatchedStar]


def estimate_from_detected_stars(width: int, height: int, stars: Sequence[StarPoint], utc_dt: datetime) -> PhotoEstimate:
    if not stars:
        raise ValueError("Yıldız noktası bulunamadı.")

    catalog = load_bright_star_catalog()
    matched = match_stars_from_points(stars, catalog)

    if len(matched) < 3:
        return PhotoEstimate(
            latitude_deg=None,
            longitude_deg=None,
            location_confidence=0.0,
            match_confidence=0.0,
            note=(
                "Yıldız kimliği güvenilir çıkarılamadı. Daha net Stellarium görüntüsü yükleyin "
                "veya daha fazla parlak yıldız içeren fotoğraf kullanın."
            ),
            matched_stars=[],
        )

    avg_score = sum(m.score for m in matched) / len(matched)
    solved = solve_location_from_matches(utc_dt, width, height, matched)

    if solved is None:
        return PhotoEstimate(
            latitude_deg=None,
            longitude_deg=None,
            location_confidence=0.0,
            match_confidence=round(avg_score, 2),
            note="Yıldız eşleşmesi bulundu ama konum çözücü başarısız oldu.",
            matched_stars=matched,
        )

    # Güvenlik filtresi: RMS çok yüksekse koordinatı yayımlama.
    if solved.rms_alt_error_deg > MAX_ACCEPTABLE_RMS_DEG:
        return PhotoEstimate(
            latitude_deg=None,
            longitude_deg=None,
            location_confidence=0.0,
            match_confidence=round(avg_score, 2),
            note=(
                f"Ön eşleşme var ama çözüm kalitesi düşük (RMS: {solved.rms_alt_error_deg:.2f}°). "
                "Koordinat güvenilir olmadığı için gösterilmiyor."
            ),
            matched_stars=matched,
        )

    loc_conf = max(0.0, min(1.0, 1.0 - (solved.rms_alt_error_deg / SOFT_RMS_DEG)))
    return PhotoEstimate(
        latitude_deg=solved.latitude_deg,
        longitude_deg=solved.longitude_deg,
        location_confidence=round(loc_conf, 2),
        match_confidence=round(avg_score, 2),
        note=f"Konum çözüldü (RMS yükseklik hatası: {solved.rms_alt_error_deg:.2f}°).",
        matched_stars=matched,
    )


def estimate_from_image_and_utc(image_path: str, utc_str: str) -> tuple[datetime, PhotoEstimate]:
    utc_dt = parse_utc(utc_str)
    width, height, stars = detect_star_points(image_path)
    return utc_dt, estimate_from_detected_stars(width, height, stars, utc_dt)
