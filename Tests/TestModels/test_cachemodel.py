import unittest
from Models.Cache.cachemodel import CacheControlModel


class TestCacheControlModel(unittest.TestCase):

    def setUp(self):
        self.model = CacheControlModel()

    def test_add_cache_should_return_None(self):
        val = self.model.add_cache("Test", "name", {})
        self.assertIsNone(val)

    def test_get_cache_data_return_dict(self):
        val = self.model.add_cache("Test", "name", {})
        val = self.model.get_cache_data("Test")
        self.assertIsInstance(val, dict)


if __name__ == "__main__":
    unittest.main()