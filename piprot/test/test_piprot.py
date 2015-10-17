#!/usr/bin/env python
import unittest

from piprot.piprot import main


class TestRequirementsParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_requirement_exact(self):
        main([open('piprot/test/files/pytz_req.txt')])


if __name__ == '__main__':
    unittest.main()
