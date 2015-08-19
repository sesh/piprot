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

    def test_regex_versions(self):
        v1 = parse_version('2014.12.24')
        v2 = parse_version('2013-12-31')
        self.assertTrue(v2 < v1)

    def test_length_missmatch(self):
        v1 = parse_version('3.2')
        v2 = parse_version('3.2.1')
        v3 = parse_version('3.1.19')

        self.assertTrue(v1 < v2)
        self.assertTrue(v3 < v1)
        self.assertTrue(v3 < v2)

    def test_versions(self):
        version_examples = [
            ('2.7.0', [2, 7, 0]),
            ('0.9.2', [0, 9, 2]),

            # 42: Billiard
            ('0.9.2.2', [0, 9, 2, 2]),

            # 42: regex
            ('2014.12.24', [2014, 12, 24]),
            ('2013-12-31', [2013, 12, 31]),

            # 45: Kombu
            ('3.0.17-20140602', [3, 0, 17, 20140602]),

            ('1234567', [1234567,]),
            ('1.2.  3', [1, 2, 3]),
            ('1.2.3  ', [1, 2, 3]),

        ]

        for version, parts in version_examples:
            self.assertEqual(parse_version(version).parts, parts)
