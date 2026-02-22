"""Basit yıldız tespiti (MVP): görüntüdeki parlak noktaları bulur."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class StarPoint:
    x: float
    y: float
    brightness: float


def _require_pillow():
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Fotoğraf işleme için Pillow gerekli. Kurulum: pip install pillow"
        ) from exc
    return Image


def detect_star_points(image_path: str, threshold: int = 220) -> Tuple[int, int, List[StarPoint]]:
    """Gri ton görüntüde threshold üstü pikselleri bağlı bileşenleyip yıldız merkezleri çıkarır."""
    Image = _require_pillow()
    img = Image.open(image_path).convert("L")
    width, height = img.size
    pix = img.load()

    visited = [[False] * width for _ in range(height)]
    stars: List[StarPoint] = []

    for y in range(height):
        for x in range(width):
            if visited[y][x] or pix[x, y] < threshold:
                continue

            stack = [(x, y)]
            visited[y][x] = True
            pts = []
            total_brightness = 0.0

            while stack:
                cx, cy = stack.pop()
                b = float(pix[cx, cy])
                pts.append((cx, cy, b))
                total_brightness += b

                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx] and pix[nx, ny] >= threshold:
                        visited[ny][nx] = True
                        stack.append((nx, ny))

            if len(pts) < 2:
                continue

            sx = sum(px * pb for px, _, pb in pts)
            sy = sum(py * pb for _, py, pb in pts)
            stars.append(StarPoint(x=sx / total_brightness, y=sy / total_brightness, brightness=total_brightness))

    stars.sort(key=lambda s: s.brightness, reverse=True)
    return width, height, stars


def pixel_to_alt_az(
    x: float,
    y: float,
    width: int,
    height: int,
    camera_az_deg: float,
    camera_alt_deg: float,
    hfov_deg: float,
    vfov_deg: float,
) -> Tuple[float, float]:
    """Piksel koordinatını yaklaşık alt/az değerine çevirir."""
    nx = (x - (width / 2.0)) / width
    ny = ((height / 2.0) - y) / height

    az = camera_az_deg + nx * hfov_deg
    alt = camera_alt_deg + ny * vfov_deg
    return alt, az
