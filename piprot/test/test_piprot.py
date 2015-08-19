#!/usr/bin/env python
import os
import unittest
from six import StringIO

from piprot.piprot import main

class TestRequirementsParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_requirement_exact(self):
        d = main([open('piprot/test/files/pytz_req.txt')])


if __name__ == '__main__':
    unittest.main()
