from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from typing import List, Sequence

from star_catalog import CatalogStar
from vision import StarPoint


@dataclass
class MatchedStar:
    image_x: float
    image_y: float
    name: str
    ra_deg: float
    dec_deg: float
    score: float


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _ang_sep_deg(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    c = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
    c = max(-1.0, min(1.0, c))
    return math.degrees(math.acos(c))


def _triangle_signature(a: float, b: float, c: float) -> tuple[float, float]:
    sides = sorted([a, b, c])
    if sides[0] <= 1e-6:
        return (999.0, 999.0)
    return (sides[1] / sides[0], sides[2] / sides[0])


def match_stars_from_points(
    stars: Sequence[StarPoint],
    catalog: Sequence[CatalogStar],
    max_image_stars: int = 10,
    max_catalog_stars: int = 20,
) -> List[MatchedStar]:
    """Triangle ratio-based rough star ID for Stellarium-like renders.

    Returns up to 3 matched stars. This is a fast MVP matcher, not production astrometry.
    """
    img = sorted(stars, key=lambda s: s.brightness, reverse=True)[:max_image_stars]
    cat = sorted(catalog, key=lambda s: s.mag)[:max_catalog_stars]

    if len(img) < 3 or len(cat) < 3:
        return []

    best = None
    best_err = 1e9

    for i_idx in itertools.combinations(range(len(img)), 3):
        ia, ib, ic = [img[k] for k in i_idx]
        di = _triangle_signature(
            _dist((ia.x, ia.y), (ib.x, ib.y)),
            _dist((ia.x, ia.y), (ic.x, ic.y)),
            _dist((ib.x, ib.y), (ic.x, ic.y)),
        )

        for c_idx in itertools.combinations(range(len(cat)), 3):
            ca, cb, cc = [cat[k] for k in c_idx]
            dc = _triangle_signature(
                _ang_sep_deg(ca.ra_deg, ca.dec_deg, cb.ra_deg, cb.dec_deg),
                _ang_sep_deg(ca.ra_deg, ca.dec_deg, cc.ra_deg, cc.dec_deg),
                _ang_sep_deg(cb.ra_deg, cb.dec_deg, cc.ra_deg, cc.dec_deg),
            )
            err = abs(di[0] - dc[0]) + abs(di[1] - dc[1])
            if err < best_err:
                best_err = err
                best = (i_idx, c_idx)

    if best is None or best_err > 0.25:
        return []

    i_idx, c_idx = best
    chosen_img = [img[k] for k in i_idx]
    chosen_cat = [cat[k] for k in c_idx]

    chosen_img.sort(key=lambda p: p.brightness, reverse=True)
    chosen_cat.sort(key=lambda p: p.mag)

    score = max(0.0, 1.0 - min(1.0, best_err / 0.25))
    out: List[MatchedStar] = []
    for ip, cs in zip(chosen_img, chosen_cat):
        out.append(
            MatchedStar(
                image_x=ip.x,
                image_y=ip.y,
                name=cs.name,
                ra_deg=cs.ra_deg,
                dec_deg=cs.dec_deg,
                score=score,
            )
        )
    return out
