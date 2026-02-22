import unittest

from pipeline import estimate_from_detected_stars
from vision import StarPoint


class PipelineTests(unittest.TestCase):
    def test_estimate_from_detected_stars_returns_lat_only(self):
        stars = [StarPoint(x=300, y=50, brightness=1000), StarPoint(x=200, y=120, brightness=700)]
        res = estimate_from_detected_stars(width=400, height=400, stars=stars)
        self.assertIsNone(res.longitude_deg)
        self.assertGreaterEqual(res.latitude_deg, -90)
        self.assertLessEqual(res.latitude_deg, 90)


if __name__ == "__main__":
    unittest.main()
