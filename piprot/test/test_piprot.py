#!/usr/bin/env python
import unittest

from piprot.piprot import main


class TestRequirementsParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_requirement_exact(self):
        with self.assertRaises(SystemExit):
            main([open('piprot/test/files/pytz_req.txt')])

    def test_conda_exact(self):
        with self.assertRaises(SystemExit):
            main([open('piprot/test/files/test-conda.yml')])


if __name__ == '__main__':
    unittest.main()
