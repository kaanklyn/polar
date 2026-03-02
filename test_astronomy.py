from datetime import datetime, timezone
import unittest

from astronomy import estimate_lat_from_polaris, gmst_deg, normalize_lon, parse_utc


class AstronomyTests(unittest.TestCase):
    def test_parse_utc(self):
        dt = parse_utc("2026-01-15T22:30:00Z")
        self.assertEqual(dt.tzinfo, timezone.utc)
        self.assertEqual(dt.hour, 22)

    def test_normalize_lon(self):
        self.assertAlmostEqual(normalize_lon(190), -170)
        self.assertAlmostEqual(normalize_lon(-190), 170)

    def test_lat_from_polaris(self):
        self.assertAlmostEqual(estimate_lat_from_polaris(70.0), 70.7)

    def test_gmst_range(self):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        v = gmst_deg(dt)
        self.assertGreaterEqual(v, 0)
        self.assertLess(v, 360)


if __name__ == "__main__":
    unittest.main()
