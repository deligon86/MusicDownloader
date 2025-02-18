class CacheControlModel:

    def __init__(self):
        self.__cache = {}

    @property
    def cache(self):
        return self.__cache

    def add_cache(self, key: str, keyword, data):
        if key in self.__cache:
            cache = self.__cache[key]
            cache[keyword] = data
        else:
            self.__cache[key] = {keyword: data}

    def get_cache_data(self, key):
        """

        :param key:
        :return: dict
        """
        if key in self.__cache.keys():
            return self.__cache.get(key)
