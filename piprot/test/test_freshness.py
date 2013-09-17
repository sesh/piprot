#!/usr/bin/env python
import unittest
from piprot.piprot import get_version_and_release_date

class TestFreshness(unittest.TestCase):
    def setUp(self):
        pass

    def test_rotten_package(self):
        v1, r1 = get_version_and_release_date('requests', '1.1.0')
        v2, r2 = get_version_and_release_date('request')
        self.assertNotEqual(v1, v2)
        self.assertNotEqual(r1, r2)

    def test_fresh_package(self):
        v1, r1 = get_version_and_release_date('request')
        v2, r2 = get_version_and_release_date('request', v1)
        self.assertEqual(v1, v2)
        self.assertEqual(r1, r2)

if __name__ == '__main__':
    unittest.main()
