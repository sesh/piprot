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
        self.assertTrue(d[0][2] == False)

    def test_requirements_with_extra(self):
        f = StringIO("requests[security]==1.2.3")
        d = parse_req_file(f)
        self.assertEqual(d[0][0], 'requests')
        self.assertEqual(d[0][1], '1.2.3')

    def test_requirements_ignore(self):
        f = StringIO("requests==1.2.3  # norot")
        d = parse_req_file(f)
        self.assertEqual(d[0][0], 'requests')
        self.assertEqual(d[0][1], '1.2.3')
        self.assertEqual(d[0][2], True)

    def test_requirements_file(self):
        with open(
            os.path.join(os.path.dirname(__file__), 'files/_develop.txt')
        ) as f:
            d = parse_req_file(f, verbatim=False)
            self.assertTrue(d[0][0] == 'ipython')
            self.assertTrue(d[0][1] == '1.1.0')

    def test_recursive_requirements_file(self):
        with open(
            os.path.join(
                os.path.dirname(__file__),
                'files/test-requirements.txt'
            )
        ) as f:
            d = parse_req_file(f, verbatim=False)
            reqs = [x[0] for x in d]
            self.assertTrue('ipython' in reqs)

    def test_ignore_in_requirements_file(self):
        with open(
            os.path.join(
                os.path.dirname(__file__),
                'files/test-requirements.txt'
            )
        ) as f:
            d = parse_req_file(f, verbatim=False)
            ignored = [x[0] for x in d if x[2]]
            self.assertTrue('piprot' in ignored)

    def test_requirements_length(self):
        with open(
            os.path.join(os.path.dirname(__file__), 'files/_develop.txt')
        ) as f:
            d = parse_req_file(f, verbatim=False)
            self.assertEqual(len(d), 1)

    def test_recursive_requirements_length(self):
        with open(
            os.path.join(
                os.path.dirname(__file__),
                'files/test-requirements.txt'
            )
        ) as f:
            d = parse_req_file(f, verbatim=False)
            self.assertEqual(len(d), 5)

    def test_requirements_file_verbatim(self):
        with open(
            os.path.join(os.path.dirname(__file__), 'files/_develop.txt')
        ) as f:
            d = parse_req_file(f, verbatim=True)
            comments = [x[1] for x in d if not x[0]]
            self.assertTrue('# Development Requirements\n' in comments)

    def test_recursive_requirements_file_verbatim(self):
        with open(
            os.path.join(os.path.dirname(__file__), 'files/_develop.txt')
        ) as f:
            d = parse_req_file(f, verbatim=True)
            comments = [x[1] for x in d if not x[0]]
            self.assertTrue('# Development Requirements\n' in comments)


if __name__ == '__main__':
    unittest.main()
