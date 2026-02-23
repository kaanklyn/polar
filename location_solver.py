from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Iterable

from astronomy import gmst_deg, normalize_lon
from star_matcher import MatchedStar


@dataclass
class SolvedLocation:
    latitude_deg: float
    longitude_deg: float
    rms_alt_error_deg: float
    azimuth_offset_deg: float


def _alt_az_from_radec(lat_deg: float, lon_deg: float, utc_dt: datetime, ra_deg: float, dec_deg: float) -> tuple[float, float]:
    lst = (gmst_deg(utc_dt) + lon_deg) % 360.0
    h = math.radians((lst - ra_deg) % 360.0)
    if h > math.pi:
        h -= 2 * math.pi

    lat = math.radians(lat_deg)
    dec = math.radians(dec_deg)

    sin_alt = math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(h)
    sin_alt = max(-1.0, min(1.0, sin_alt))
    alt = math.asin(sin_alt)

    cos_alt = max(1e-9, math.cos(alt))
    sin_az = -math.cos(dec) * math.sin(h) / cos_alt
    cos_az = (math.sin(dec) - math.sin(alt) * math.sin(lat)) / max(1e-9, math.cos(lat) * cos_alt)
    az = math.degrees(math.atan2(sin_az, cos_az)) % 360.0

    return math.degrees(alt), az


def _observed_alt_az_from_pixel(
    x: float, y: float, width: int, height: int, fov_deg: float = 120.0
) -> tuple[float, float]:
    cx, cy = width / 2.0, height / 2.0
    dx, dy = x - cx, y - cy

    r = math.hypot(dx, dy)
    rmax = max(1.0, min(width, height) / 2.0)

    zenith_angle = (r / rmax) * (fov_deg / 2.0)
    zenith_angle = max(0.0, min(fov_deg / 2.0, zenith_angle))
    alt = 90.0 - zenith_angle

    az = math.degrees(math.atan2(dx, -dy)) % 360.0
    return alt, az


def _ang_diff_deg(a: float, b: float) -> float:
    d = (a - b + 180.0) % 360.0 - 180.0
    return abs(d)


def solve_location_from_matches(
    utc_dt: datetime,
    width: int,
    height: int,
    matches: Iterable[MatchedStar],
    fov_deg: float = 120.0,
) -> SolvedLocation | None:
    ms = list(matches)
    if len(ms) < 3:
        return None

    obs = [
        _observed_alt_az_from_pixel(m.image_x, m.image_y, width, height, fov_deg=fov_deg)
        for m in ms
    ]

    def score(lat: float, lon: float, az_offset: float) -> float:
        errs = []
        for m, (alt_obs, az_obs) in zip(ms, obs):
            alt_pred, az_pred = _alt_az_from_radec(lat, lon, utc_dt, m.ra_deg, m.dec_deg)
            alt_err = alt_pred - alt_obs
            az_err = _ang_diff_deg((az_pred + az_offset) % 360.0, az_obs)
            errs.append((alt_err / 8.0) ** 2 + (az_err / 30.0) ** 2)
        return math.sqrt(sum(errs) / len(errs))

    best_lat, best_lon, best_off, best_err = 0.0, 0.0, 0.0, 1e9

    for lat in range(-80, 81, 5):
        for lon in range(-180, 181, 5):
            for off in range(0, 360, 10):
                e = score(float(lat), float(lon), float(off))
                if e < best_err:
                    best_err = e
                    best_lat, best_lon, best_off = float(lat), float(lon), float(off)

    step_latlon = 2.0
    step_off = 5.0
    while step_latlon >= 0.25:
        improved = True
        while improved:
            improved = False
            for dlat in (-step_latlon, 0.0, step_latlon):
                for dlon in (-step_latlon, 0.0, step_latlon):
                    for doff in (-step_off, 0.0, step_off):
                        cand_lat = max(-89.0, min(89.0, best_lat + dlat))
                        cand_lon = normalize_lon(best_lon + dlon)
                        cand_off = (best_off + doff) % 360.0
                        e = score(cand_lat, cand_lon, cand_off)
                        if e + 1e-9 < best_err:
                            best_err = e
                            best_lat, best_lon, best_off = cand_lat, cand_lon, cand_off
                            improved = True
        step_latlon /= 2.0
        step_off /= 2.0

    return SolvedLocation(
        latitude_deg=round(best_lat, 4),
        longitude_deg=round(normalize_lon(best_lon), 4),
        rms_alt_error_deg=round(best_err * 8.0, 3),
        azimuth_offset_deg=round(best_off, 3),
    )
