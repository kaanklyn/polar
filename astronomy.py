"""Astronomy utility functions and geolocation solver.

This module provides core spherical astronomy helpers and a nonlinear
least-squares solver for estimating observer location from star matches.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import acos, asin, atan2, cos, degrees, radians, sin, sqrt
from typing import List, Optional, Sequence, Tuple


RA_DEC = Tuple[float, float]
ALT_AZ = Tuple[float, float]
PIXEL = Tuple[float, float]


@dataclass
class CameraModel:
    """Simple pinhole camera model for pixel-to-angle conversion."""

    width_px: int
    height_px: int
    focal_length_px: float


@dataclass
class PhotoEstimate:
    """Output model for a single photo-based location estimate."""

    latitude_deg: float
    longitude_deg: float
    error_km: float
    matched_star_count: int
    residual_deg: float
    heading_deg: Optional[float] = None
    covariance: Optional[List[List[float]]] = None


def _to_utc(utc_time: datetime) -> datetime:
    if utc_time.tzinfo is None:
        return utc_time.replace(tzinfo=timezone.utc)
    return utc_time.astimezone(timezone.utc)


def julian_day(utc_time: datetime) -> float:
    """Convert UTC datetime to Julian day."""

    dt = _to_utc(utc_time)
    year = dt.year
    month = dt.month
    day = dt.day + (
        dt.hour + dt.minute / 60.0 + (dt.second + dt.microsecond / 1_000_000.0) / 3600.0
    ) / 24.0

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + (a // 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    return jd


def greenwich_sidereal_time_deg(utc_time: datetime) -> float:
    """Compute Greenwich mean sidereal time in degrees."""

    jd = julian_day(utc_time)
    t = (jd - 2451545.0) / 36525.0
    gmst = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * t * t
        - (t * t * t) / 38710000.0
    )
    return gmst % 360.0


def radec_to_altaz(
    ra_deg: float,
    dec_deg: float,
    utc_time: datetime,
    latitude_deg: float,
    longitude_deg: float,
) -> ALT_AZ:
    """Project celestial coordinates to local altitude/azimuth."""

    lst_deg = (greenwich_sidereal_time_deg(utc_time) + longitude_deg) % 360.0
    hour_angle_deg = (lst_deg - ra_deg + 540.0) % 360.0 - 180.0

    ha = radians(hour_angle_deg)
    dec = radians(dec_deg)
    lat = radians(latitude_deg)

    sin_alt = sin(dec) * sin(lat) + cos(dec) * cos(lat) * cos(ha)
    sin_alt = max(-1.0, min(1.0, sin_alt))
    alt = asin(sin_alt)

    y = -sin(ha) * cos(dec)
    x = sin(dec) * cos(lat) - cos(dec) * sin(lat) * cos(ha)
    az = atan2(y, x)

    alt_deg = degrees(alt)
    az_deg = (degrees(az) + 360.0) % 360.0
    return alt_deg, az_deg


def _pixel_to_altaz(pixel: PIXEL, camera: CameraModel, heading_deg: float) -> ALT_AZ:
    """Approximate pixel observation as local alt/az using a level camera model."""

    x = (pixel[0] - camera.width_px / 2.0) / camera.focal_length_px
    y = (camera.height_px / 2.0 - pixel[1]) / camera.focal_length_px

    alt_offset = degrees(atan2(y, 1.0))
    az_offset = degrees(atan2(x, 1.0))

    alt = alt_offset
    az = (heading_deg + az_offset) % 360.0
    return alt, az


def _angular_separation_deg(a: ALT_AZ, b: ALT_AZ) -> float:
    alt1, az1 = radians(a[0]), radians(a[1])
    alt2, az2 = radians(b[0]), radians(b[1])

    cos_sep = sin(alt1) * sin(alt2) + cos(alt1) * cos(alt2) * cos(az1 - az2)
    cos_sep = max(-1.0, min(1.0, cos_sep))
    return degrees(acos(cos_sep))


def _residuals(
    params: Sequence[float],
    matched_star_radec: Sequence[RA_DEC],
    observed_altaz: Sequence[ALT_AZ],
    utc_time: datetime,
    optimize_heading: bool,
) -> List[float]:
    lat = params[0]
    lon = params[1]
    heading = params[2] if optimize_heading else 0.0

    values: List[float] = []
    for (ra, dec), (obs_alt, obs_az) in zip(matched_star_radec, observed_altaz):
        pred_alt, pred_az = radec_to_altaz(ra, dec, utc_time, lat, lon)
        corrected_obs = (obs_alt, (obs_az - heading) % 360.0) if optimize_heading else (obs_alt, obs_az)
        values.append(_angular_separation_deg((pred_alt, pred_az), corrected_obs))
    return values


def _jacobian(
    params: List[float],
    residual_fn,
    epsilon: float = 1e-5,
) -> List[List[float]]:
    base = residual_fn(params)
    j: List[List[float]] = [[0.0 for _ in params] for _ in base]

    for col in range(len(params)):
        perturbed = list(params)
        perturbed[col] += epsilon
        shifted = residual_fn(perturbed)
        for row in range(len(base)):
            j[row][col] = (shifted[row] - base[row]) / epsilon
    return j


def _matmul_transpose_a(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    rows = len(a[0])
    cols = len(b[0])
    inner = len(a)
    out = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for i in range(rows):
        for k in range(inner):
            aik = a[k][i]
            for j in range(cols):
                out[i][j] += aik * b[k][j]
    return out


def _matvec_transpose_a(a: List[List[float]], v: List[float]) -> List[float]:
    rows = len(a[0])
    out = [0.0 for _ in range(rows)]
    for i in range(rows):
        for k in range(len(a)):
            out[i] += a[k][i] * v[k]
    return out


def _solve_linear_system(a: List[List[float]], b: List[float]) -> List[float]:
    n = len(a)
    aug = [row[:] + [b[i]] for i, row in enumerate(a)]

    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(aug[r][i]))
        aug[i], aug[pivot] = aug[pivot], aug[i]
        if abs(aug[i][i]) < 1e-12:
            raise ValueError("Singular normal equation matrix")

        scale = aug[i][i]
        for c in range(i, n + 1):
            aug[i][c] /= scale

        for r in range(n):
            if r == i:
                continue
            factor = aug[r][i]
            for c in range(i, n + 1):
                aug[r][c] -= factor * aug[i][c]

    return [aug[i][n] for i in range(n)]


def _inverse_matrix(a: List[List[float]]) -> List[List[float]]:
    n = len(a)
    inv = []
    for col in range(n):
        e = [0.0] * n
        e[col] = 1.0
        inv_col = _solve_linear_system([row[:] for row in a], e)
        inv.append(inv_col)
    return [[inv[c][r] for c in range(n)] for r in range(n)]


def solve_location_from_matches(
    matched_star_radec: Sequence[RA_DEC],
    observed_altaz: Optional[Sequence[ALT_AZ]],
    utc_time: datetime,
    imu_initial: Tuple[float, float, float],
    observed_pixels: Optional[Sequence[PIXEL]] = None,
    camera_model: Optional[CameraModel] = None,
    optimize_heading: bool = False,
    max_iterations: int = 25,
) -> PhotoEstimate:
    """Estimate latitude/longitude using nonlinear least squares.

    Args:
        matched_star_radec: Iterable of matched stars as (RA deg, Dec deg).
        observed_altaz: Measured local star directions as (alt deg, az deg).
        utc_time: Observation timestamp in UTC.
        imu_initial: Initial guess tuple (lat, lon, heading).
        observed_pixels: Optional measured pixels if alt/az not provided.
        camera_model: Required with `observed_pixels`.
        optimize_heading: Whether heading should be jointly optimized.
        max_iterations: Maximum Gauss-Newton iterations.
    """

    if not matched_star_radec:
        raise ValueError("matched_star_radec cannot be empty")

    if observed_altaz is None:
        if observed_pixels is None or camera_model is None:
            raise ValueError("Provide observed_altaz or (observed_pixels + camera_model)")
        observed_altaz = [_pixel_to_altaz(px, camera_model, imu_initial[2]) for px in observed_pixels]

    if len(matched_star_radec) != len(observed_altaz):
        raise ValueError("matched_star_radec and observed observations length mismatch")

    params = [imu_initial[0], imu_initial[1]]
    if optimize_heading:
        params.append(imu_initial[2])

    def residual_fn(p: List[float]) -> List[float]:
        return _residuals(p, matched_star_radec, observed_altaz or [], utc_time, optimize_heading)

    for _ in range(max_iterations):
        r = residual_fn(params)
        j = _jacobian(params, residual_fn)

        jt_j = _matmul_transpose_a(j, j)
        jt_r = _matvec_transpose_a(j, r)

        # Levenberg-Marquardt damping for stability.
        for d in range(len(jt_j)):
            jt_j[d][d] += 1e-4

        step = _solve_linear_system(jt_j, [-v for v in jt_r])
        candidate = [p + s for p, s in zip(params, step)]

        new_r = residual_fn(candidate)
        old_cost = sum(v * v for v in r)
        new_cost = sum(v * v for v in new_r)

        if new_cost < old_cost:
            params = candidate
            if abs(old_cost - new_cost) < 1e-10:
                break
        else:
            break


    final_res = residual_fn(params)
    n = len(final_res)
    p = len(params)
    rms = sqrt(sum(v * v for v in final_res) / max(n, 1))

    covariance = None
    if n > p:
        j = _jacobian(params, residual_fn)
        jt_j = _matmul_transpose_a(j, j)
        sigma2 = sum(v * v for v in final_res) / (n - p)
        try:
            cov = _inverse_matrix(jt_j)
            covariance = [[sigma2 * cell for cell in row] for row in cov]
        except ValueError:
            covariance = None

    lat, lon = params[0], ((params[1] + 180.0) % 360.0) - 180.0
    heading = params[2] % 360.0 if optimize_heading else imu_initial[2]

    # Approximate surface error from angular RMS.
    error_km = rms * 111.32

    return PhotoEstimate(
        latitude_deg=lat,
        longitude_deg=lon,
        heading_deg=heading,
        error_km=error_km,
        matched_star_count=len(matched_star_radec),
        residual_deg=rms,
        covariance=covariance,
    )
