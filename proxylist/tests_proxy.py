import unittest

from proxylist.proxy import get_location_country_name


class TestProxy(unittest.TestCase):
    def test_country_name(self):
        self.assertEqual("Peru", get_location_country_name("pe"))
        self.assertEqual("Peru", get_location_country_name("PE"))
        self.assertEqual("", get_location_country_name("xx"))


if __name__ == '__main__':
    unittest.main()
