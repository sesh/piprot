#!/usr/bin/env python
import unittest

from piprot.piprot import parse_version

class TestRequirementsParser(unittest.TestCase):

    def test_billiard_versions(self):
        """
        Test for #42: https://github.com/sesh/piprot/issues/42
        """
        v1 = parse_version('3.3.0.20')
        v2 = parse_version('3.3.0.2')
        v3 = parse_version('3.3.0.22')

        self.assertTrue(v2 < v1)
        self.assertTrue(v2 < v3)
        self.assertTrue(v1 < v3)

    def test_length_missmatch(self):
        v1 = parse_version('3.2')
        v2 = parse_version('3.2.1')
        v3 = parse_version('3.1.19')

        self.assertTrue(v1 < v2)
        self.assertTrue(v3 < v1)
        self.assertTrue(v3 < v2)
