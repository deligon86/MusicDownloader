from Core.utils.utils import merge_dict
from .enginesmodel import BaseEngine
from Models.Cache.cachemodel import CacheControlModel


class AlbumManagerModel:

    def __init__(self):
        self._engines = {}
        self._engine = None
        self._search_rule = None
        self._cache_manager = None

    def add_cache_control(self, cache: CacheControlModel):
        self._cache_manager = cache

    def set_search_rule(self, rule):
        """
        Rules:
            1. use all engines
            2. use default engine
        """
        self._search_rule = rule

    def add_engine(self, name, engine:BaseEngine):
        self._engines[name] = engine

    def get_engine(self):
        return self._engine

    def set_engine(self, name):
        if name in self._engines:
            self._engine = self._engines[name]

    def results_query(self, keyword):
        """

        :param keyword:
        :return: dict[title] = [link, image, description]
        """
        results = {}
        cache = self._cache_manager.get_cache_data("album search")
        if cache:
            if keyword in cache:
                return cache[keyword]
        else:
            match self._search_rule:
                case "use all engines":
                    for engine in self._engines.values():
                        r = engine.search(keyword)
                        results = merge_dict(results, r)
                case "use default engine":
                    results = self._engine.search(keyword)

            # add to cache
            self._cache_manager.add_cache("album search", keyword, results)
            return results
