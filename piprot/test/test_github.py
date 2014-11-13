#!/usr/bin/env python
import unittest
import requests
from six import StringIO

from piprot.piprot import parse_req_file
from piprot.providers.github import build_github_url

class TestGithubURLs(unittest.TestCase):
    def setUp(self):
        pass

    def test_repo_url(self):
        url1 = build_github_url('sesh/piprot')
        url2 = build_github_url('sesh/piprot', 'master')
        self.assertEqual(url1, url2)

    def test_repo_url_with_branch(self):
        url = build_github_url('sesh/piprot', 'develop')
        expected = 'https://raw.githubusercontent.com/sesh/piprot/develop/requirements.txt'
        self.assertEqual(url, expected)

    def test_repo_url_with_path(self):
        url = build_github_url('sesh/piprot', path='requirements/_base.txt')
        expected = 'https://raw.githubusercontent.com/sesh/piprot/master/requirements/_base.txt'
        self.assertEqual(url, expected)

    def test_repo_url_with_access_token(self):
        url = build_github_url('sesh/piprot', token='SUCH-SECRET-MANY-T0KEN')
        expected = 'https://raw.githubusercontent.com/sesh/piprot/master/requirements.txt?token=SUCH-SECRET-MANY-T0KEN'
        self.assertEqual(url, expected)

    def test_full_github_requirements_test(self):
        url = build_github_url('sesh/piprot', path='requirements.txt')

        expected = 'https://raw.githubusercontent.com/sesh/piprot/master/requirements.txt'
        self.assertEqual(url, expected)

        response = requests.get(url)
        req_file = StringIO(response.text)
        requirements = parse_req_file(req_file)
        self.assertTrue('piprot' in [req for req, version in requirements])


if __name__ == '__main__':
    unittest.main()
