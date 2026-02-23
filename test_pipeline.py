import unittest

from pipeline import estimate_from_detected_stars
from vision import StarPoint


class PipelineTests(unittest.TestCase):
    def test_estimate_has_matched_stars_field(self):
        stars = [StarPoint(x=300, y=50, brightness=1000), StarPoint(x=200, y=120, brightness=700), StarPoint(x=120, y=80, brightness=650)]
        res = estimate_from_detected_stars(width=400, height=400, stars=stars)
        self.assertIsInstance(res.matched_stars, list)
        self.assertEqual(res.location_confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
