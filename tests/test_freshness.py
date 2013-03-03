#!/usr/bin/env python
import unittest


class TestFreshness(unittest.TestCase):
    def setUp(self):
        pass

    def test_rotten_package(self):
        self.assertTrue(False)

    def test_fresh_package(self):
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
