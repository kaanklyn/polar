"""Fotoğraf + tarih girdisinden basitleştirilmiş konum tahmini akışı."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from astronomy import parse_utc
from star_catalog import load_bright_star_catalog
from star_matcher import MatchedStar, match_stars_from_points
from vision import StarPoint, detect_star_points


@dataclass
class PhotoEstimate:
    latitude_deg: float | None
    longitude_deg: float | None
    confidence: float
    note: str
    matched_stars: list[MatchedStar]


def estimate_from_detected_stars(width: int, height: int, stars: Sequence[StarPoint]) -> PhotoEstimate:
    if not stars:
        raise ValueError("Yıldız noktası bulunamadı.")

    catalog = load_bright_star_catalog()
    matched = match_stars_from_points(stars, catalog)

    if len(matched) < 3:
        return PhotoEstimate(
            latitude_deg=None,
            longitude_deg=None,
            confidence=0.0,
            note=(
                "Yıldız kimliği güvenilir çıkarılamadı. Daha net Stellarium görüntüsü yükleyin "
                "veya daha fazla parlak yıldız içeren fotoğraf kullanın."
            ),
            matched_stars=[],
        )

    # Hızlı MVP: yıldız tanıma var; konum solver bir sonraki adım.
    avg_score = sum(m.score for m in matched) / len(matched)
    return PhotoEstimate(
        latitude_deg=None,
        longitude_deg=None,
        confidence=round(avg_score, 2),
        note="Yıldız tanıma başarılı. Sonraki adım: bu eşleşmelerle lat/lon solver entegrasyonu.",
        matched_stars=matched,
    )


def estimate_from_image_and_utc(image_path: str, utc_str: str) -> tuple[datetime, PhotoEstimate]:
    utc_dt = parse_utc(utc_str)
    width, height, stars = detect_star_points(image_path)
    return utc_dt, estimate_from_detected_stars(width, height, stars)
