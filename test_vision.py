import unittest

from vision import pixel_to_alt_az


class VisionTests(unittest.TestCase):
    def test_pixel_center_maps_to_camera_direction(self):
        alt, az = pixel_to_alt_az(
            x=500,
            y=250,
            width=1000,
            height=500,
            camera_az_deg=30,
            camera_alt_deg=40,
            hfov_deg=60,
            vfov_deg=40,
        )
        self.assertAlmostEqual(alt, 40)
        self.assertAlmostEqual(az, 30)


if __name__ == "__main__":
    unittest.main()
