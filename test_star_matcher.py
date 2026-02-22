import unittest

from star_catalog import load_bright_star_catalog
from star_matcher import match_stars_from_points
from vision import StarPoint


class StarMatcherTests(unittest.TestCase):
    def test_returns_list(self):
        catalog = load_bright_star_catalog()
        stars = [
            StarPoint(100, 100, 1000),
            StarPoint(180, 120, 900),
            StarPoint(130, 200, 850),
            StarPoint(300, 300, 200),
        ]
        out = match_stars_from_points(stars, catalog)
        self.assertIsInstance(out, list)


if __name__ == "__main__":
    unittest.main()
