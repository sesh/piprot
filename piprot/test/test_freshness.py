#!/usr/bin/env python
import unittest
from piprot.piprot import get_version


class TestFreshness(unittest.TestCase):
    def setUp(self):
        pass

    def test_rotten_package(self):
        v1, r1, v2, r2 = get_version('pip', 'requests', '1.1.0')
        self.assertNotEqual(v1, v2)
        self.assertNotEqual(r1, r2)

    def test_fresh_package(self):
        _, _, v1, r1 = get_version('pip', 'requests', '1.1.0')
        v2, r2, _, _ = get_version('pip', 'requests', v1)
        self.assertEqual(v1, v2)
        self.assertEqual(r1, r2)

    def test_pytz_package(self):
        v1, _, _, _ = get_version('pip', 'pytz', '2015.4')
        v2, _, _, _ = get_version('pip', 'pytz', '2010l')
        self.assertTrue(v2 < v1)

    def test_rotten_package_conda(self):
        v1, r1, v2, r2 = get_version('conda', 'requests', '1.1.0')
        self.assertNotEqual(v1, v2)
        self.assertNotEqual(r1, r2)

    def test_fresh_package_conda(self):
        _, _, v1, r1 = get_version('conda', 'requests', '1.1.0')
        v2, r2, _, _ = get_version('conda', 'requests', v1)
        self.assertEqual(v1, v2)
        self.assertEqual(r1, r2)


if __name__ == '__main__':
    unittest.main()
