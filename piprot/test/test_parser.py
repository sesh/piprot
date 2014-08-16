#!/usr/bin/env python
import os
import unittest
from six import StringIO

from piprot.piprot import parse_req_file

class TestRequirementsParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_requirement_exact(self):
        f = StringIO("requests==1.2.3")
        d = parse_req_file(f)
        self.assertTrue(d[0][0] == 'requests')
        self.assertTrue(d[0][1] == '1.2.3')

    def test_requirements_file(self):
        d = parse_req_file(open(os.path.join(os.path.dirname(__file__), 'files/_develop.txt')), verbatim=False)
        self.assertTrue(d[0][0] == 'ipython')
        self.assertTrue(d[0][1] == '1.1.0')

    def test_recursive_requirements_file(self):
        d = parse_req_file(open(os.path.join(os.path.dirname(__file__), 'files/test-requirements.txt')), verbatim=False)
        reqs = [x[0] for x in d]
        self.assertTrue('ipython' in reqs)

    def test_requirements_length(self):
        d = parse_req_file(open(os.path.join(os.path.dirname(__file__), 'files/_develop.txt')), verbatim=False)
        self.assertEqual(len(d), 1)

    def test_recursive_requirements_length(self):
        d = parse_req_file(open(os.path.join(os.path.dirname(__file__), 'files/test-requirements.txt')), verbatim=False)
        self.assertEqual(len(d), 3)

    def test_requirements_file_verbatim(self):
        d = parse_req_file(open(os.path.join(os.path.dirname(__file__), 'files/_develop.txt')), verbatim=True)
        comments = [x[1] for x in d if not x[0]]
        self.assertTrue('# Development Requirements\n' in comments)

    def test_recursive_requirements_file_verbatim(self):
        d = parse_req_file(open(os.path.join(os.path.dirname(__file__), 'files/_develop.txt')), verbatim=True)
        comments = [x[1] for x in d if not x[0]]
        self.assertTrue('# Development Requirements\n' in comments)


if __name__ == '__main__':
    unittest.main()
