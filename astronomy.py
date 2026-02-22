"""Offline yıldız tabanlı konum tahmini için temel astronomi fonksiyonları."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math


@dataclass
class LocationEstimate:
    latitude_deg: float
    longitude_deg: float
    confidence: float


def parse_utc(utc_str: str) -> datetime:
    s = utc_str.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def julian_date(dt: datetime) -> float:
    """UTC datetime -> Julian Date."""
    year = dt.year
    month = dt.month
    day = dt.day + (dt.hour + (dt.minute + (dt.second + dt.microsecond / 1e6) / 60) / 60) / 24

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + a // 4

    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    return jd


def gmst_deg(dt: datetime) -> float:
    """Greenwich Mean Sidereal Time, degree."""
    jd = julian_date(dt)
    t = (jd - 2451545.0) / 36525.0
    gmst = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * t * t
        - (t * t * t) / 38710000.0
    )
    return gmst % 360.0


def normalize_lon(lon: float) -> float:
    lon = ((lon + 180.0) % 360.0) - 180.0
    return lon


def estimate_lat_from_polaris(polaris_alt_deg: float, refraction_correction_deg: float = 0.7) -> float:
    """
    Polaris yüksekliğinden enlem tahmini.

    Basit model: latitude ~= alt(POLARIS) + correction
    correction: atmosferik kırılma + Polaris kutup uzaklığı için kaba düzeltme.
    """
    return max(-90.0, min(90.0, polaris_alt_deg + refraction_correction_deg))


def hour_angle_deg(lat_deg: float, dec_deg: float, alt_deg: float, az_deg: float) -> float:
    """Yükseklik-azimut verisinden saat açısını çıkarır."""
    lat = math.radians(lat_deg)
    dec = math.radians(dec_deg)
    alt = math.radians(alt_deg)
    az = math.radians(az_deg)

    # sin(dec) = sin(lat)sin(alt) - cos(lat)cos(alt)cos(A)
    # cos(H) = (sin(alt) - sin(lat)sin(dec)) / (cos(lat)cos(dec))
    numerator = math.sin(alt) - math.sin(lat) * math.sin(dec)
    denominator = math.cos(lat) * math.cos(dec)
    if abs(denominator) < 1e-9:
        raise ValueError("Geçersiz geometri: denominator ~ 0")

    cos_h = max(-1.0, min(1.0, numerator / denominator))
    h = math.degrees(math.acos(cos_h))

    # sin(H) işareti için azimut kullanımı (kuzey=0, doğu=90)
    # Yaklaşık imza: doğu yarımkürede H negatif, batıda pozitif
    if 0 <= az_deg < 180:
        h = -h

    return h


def estimate_location(
    utc_dt: datetime,
    polaris_alt_deg: float,
    star_ra_deg: float,
    star_dec_deg: float,
    star_alt_deg: float,
    star_az_deg: float,
) -> LocationEstimate:
    lat = estimate_lat_from_polaris(polaris_alt_deg)

    h = hour_angle_deg(lat, star_dec_deg, star_alt_deg, star_az_deg)
    lst = (star_ra_deg + h) % 360.0
    gmst = gmst_deg(utc_dt)

    # LST = GMST + longitude(east positive)
    lon = normalize_lon(lst - gmst)

    # Çok basit confidence: polaris altı 10-85 aralığındaysa daha iyi
    if 10 <= polaris_alt_deg <= 85:
        conf = 0.8
    else:
        conf = 0.5

    return LocationEstimate(latitude_deg=lat, longitude_deg=lon, confidence=conf)
