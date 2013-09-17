#!/usr/bin/env python
import unittest
from StringIO import StringIO
from piprot.piprot import parse_req_file

class TestRequirementsParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_requirement_exact(self):
        f = StringIO("requests==1.2.3")
        d = parse_req_file(f)
        self.assertTrue(d[0][0] == 'requests')
        self.assertTrue(d[0][1] == '1.2.3')        

if __name__ == '__main__':
    unittest.main()
