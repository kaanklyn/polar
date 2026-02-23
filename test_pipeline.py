import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from location_solver import SolvedLocation
from pipeline import estimate_from_detected_stars
from vision import StarPoint


class PipelineTests(unittest.TestCase):
    def test_estimate_has_matched_stars_field(self):
        stars = [
            StarPoint(x=300, y=50, brightness=1000),
            StarPoint(x=200, y=120, brightness=700),
            StarPoint(x=120, y=80, brightness=650),
        ]
        utc = datetime(2026, 1, 15, 22, 30, tzinfo=timezone.utc)
        res = estimate_from_detected_stars(width=400, height=400, stars=stars, utc_dt=utc)
        self.assertIsInstance(res.matched_stars, list)
        self.assertGreaterEqual(res.location_confidence, 0.0)

    def test_rejects_solution_with_high_rms(self):
        stars = [
            StarPoint(x=300, y=50, brightness=1000),
            StarPoint(x=200, y=120, brightness=700),
            StarPoint(x=120, y=80, brightness=650),
        ]
        utc = datetime(2026, 1, 15, 22, 30, tzinfo=timezone.utc)

        with patch("pipeline.solve_location_from_matches", return_value=SolvedLocation(10.0, 20.0, 35.0, 0.0)):
            res = estimate_from_detected_stars(width=400, height=400, stars=stars, utc_dt=utc)

        self.assertIsNone(res.latitude_deg)
        self.assertIsNone(res.longitude_deg)
        self.assertEqual(res.location_confidence, 0.0)
        self.assertIn("gösterilmiyor", res.note)


if __name__ == "__main__":
    unittest.main()
