#!/usr/bin/env python
import unittest
from piprot.piprot import get_version_and_release_date


class TestFreshness(unittest.TestCase):
    def setUp(self):
        pass

    def test_rotten_package(self):
        v1, r1 = get_version_and_release_date("requests", "1.1.0")
        v2, r2 = get_version_and_release_date("requests")
        self.assertNotEqual(v1, v2)
        self.assertNotEqual(r1, r2)

    def test_fresh_package(self):
        v1, r1 = get_version_and_release_date("requests")
        v2, r2 = get_version_and_release_date("requests", v1)
        self.assertEqual(v1, v2)
        self.assertEqual(r1, r2)

    def test_pytz_package(self):
        v1, r1 = get_version_and_release_date("pytz", "2015.4")
        v2, r1 = get_version_and_release_date("pytz", "2010l")
        self.assertTrue(v2 < v1)

    def test_bad_version_number(self):
        v1, r1 = get_version_and_release_date("unidecode", "0.4.21")
        v1, r1 = get_version_and_release_date("unidecode", "0.04.21")

    def test_bad_package_name(self):
        v1, r2 = get_version_and_release_date("not-a-valid-package-brntn")
        self.assertEqual(v1, None)
        self.assertEqual(r2, None)


if __name__ == "__main__":
    unittest.main()
