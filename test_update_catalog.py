import unittest

from scripts.update_catalog import build_rows_from_hyg_csv


class UpdateCatalogTests(unittest.TestCase):
    def test_build_rows_from_hyg_csv_filters_and_converts(self):
        sample = """id,proper,ra,dec,mag\n1,Sirius,6.7525,-16.7161,-1.46\n2,,7.0,10.0,1.0\n3,DimStar,1.0,2.0,4.5\n"""
        rows = build_rows_from_hyg_csv(sample, mag_limit=2.0, max_rows=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].name, "Sirius")
        self.assertAlmostEqual(rows[0].ra_deg, 101.2875)


if __name__ == "__main__":
    unittest.main()
