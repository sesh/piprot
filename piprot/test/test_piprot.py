#!/usr/bin/env python
import unittest

from piprot.piprot import main


class TestRequirementsParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_requirement_exact(self):
        with self.assertRaises(SystemExit):
            with open("piprot/test/files/pytz_req.txt") as f:
                main([f])


if __name__ == "__main__":
    unittest.main()
