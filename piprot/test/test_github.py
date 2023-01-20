#!/usr/bin/env python
import unittest
from six import StringIO

from piprot.thttp import request
from piprot.piprot import parse_req_file
from piprot.providers.github import build_github_url


class TestGithubURLs(unittest.TestCase):
    def setUp(self):
        pass

    def test_repo_url(self):
        url1 = build_github_url("sesh/piprot")
        url2 = build_github_url("sesh/piprot", "master")
        self.assertEqual(url1, url2)

    def test_absolute_repo_url(self):
        url1 = build_github_url("sesh/piprot")
        url2 = build_github_url("https://github.com/sesh/piprot")
        self.assertEqual(url1, url2)

    def test_repo_url_with_branch(self):
        url = build_github_url("sesh/piprot", "develop")
        expected = "https://raw.githubusercontent.com/sesh/piprot/develop/requirements.txt"  # noqa
        self.assertEqual(url, expected)

    def test_repo_url_with_path(self):
        url = build_github_url("sesh/piprot", path="requirements/_base.txt")
        expected = "https://raw.githubusercontent.com/sesh/piprot/master/requirements/_base.txt"  # noqa
        self.assertEqual(url, expected)

    def test_repo_url_with_access_token(self):
        url = build_github_url("sesh/piprot", token="SUCH-SECRET-MANY-T0KEN")
        expected = "https://raw.githubusercontent.com/sesh/piprot/master/requirements.txt?token=SUCH-SECRET-MANY-T0KEN"  # noqa
        self.assertEqual(url, expected)

    def test_full_github_requirements_test(self):
        url = build_github_url("sesh/piprot", branch="dc1057d95b97dd706c4c8bbe8e3733dfaaf472b8", path="requirements.txt")

        expected = "https://raw.githubusercontent.com/sesh/piprot/dc1057d95b97dd706c4c8bbe8e3733dfaaf472b8/requirements.txt"  # noqa
        self.assertEqual(url, expected)

        response = request(url)
        req_file = StringIO(response.content.decode())
        requirements = parse_req_file(req_file)
        self.assertTrue("requests" in [req for req, version, ignore in requirements])


if __name__ == "__main__":
    unittest.main()
