#!/usr/bin/env python
import unittest
from piprot import build_github_url

class TestGithubURLs(unittest.TestCase):
    def setUp(self):
        pass

    def test_repo_url(self):
        url1 = build_github_url('sesh/piprot')
        url2 = build_github_url('sesh/piprot', 'master')
        self.assertEqual(url1, url2)

if __name__ == '__main__':
    unittest.main()
