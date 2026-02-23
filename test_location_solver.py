from datetime import datetime, timezone
import math
import unittest

from location_solver import solve_location_from_matches
from star_matcher import MatchedStar


class LocationSolverTests(unittest.TestCase):
    def test_solve_location_from_synthetic_matches(self):
        # Synthetic sky generated with same projection assumptions.
        lat_true = 40.0
        lon_true = 30.0
        utc = datetime(2026, 1, 15, 22, 30, tzinfo=timezone.utc)
        width = height = 1000

        stars = [
            ("Vega", 279.2347, 38.7837),
            ("Deneb", 310.3579, 45.2803),
            ("Altair", 297.6958, 8.8683),
        ]

        # Minimal forward model mirrored from solver assumptions.
        from astronomy import gmst_deg

        def alt(ra_deg, dec_deg):
            lst = (gmst_deg(utc) + lon_true) % 360
            h = math.radians((lst - ra_deg) % 360)
            if h > math.pi:
                h -= 2 * math.pi
            la = math.radians(lat_true)
            de = math.radians(dec_deg)
            s = math.sin(de) * math.sin(la) + math.cos(de) * math.cos(la) * math.cos(h)
            return math.degrees(math.asin(max(-1.0, min(1.0, s))))

        fov = 120.0
        matches = []
        for name, ra, dec in stars:
            z = 90 - alt(ra, dec)
            r = (z / (fov / 2.0)) * (width / 2.0)
            # synthetic azimuth placement (north-up, east-right)
            az = 40 + len(matches) * 70
            rad = math.radians(az)
            dx = r * math.sin(rad)
            dy = -r * math.cos(rad)
            x = width / 2.0 + dx
            y = height / 2.0 + dy
            matches.append(MatchedStar(x, y, name, ra, dec, 0.6))

        solved = solve_location_from_matches(utc, width, height, matches, fov_deg=fov)
        self.assertIsNotNone(solved)
        assert solved is not None
        self.assertGreaterEqual(solved.latitude_deg, -89.0)
        self.assertLessEqual(solved.latitude_deg, 89.0)
        self.assertGreaterEqual(solved.longitude_deg, -180.0)
        self.assertLessEqual(solved.longitude_deg, 180.0)
        self.assertLess(solved.rms_alt_error_deg, 90.0)


if __name__ == "__main__":
    unittest.main()
