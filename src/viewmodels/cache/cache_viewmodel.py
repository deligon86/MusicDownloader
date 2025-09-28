from kivy.event import EventDispatcher
from src.models.Cache.cachemodel import CacheControlModel


class CacheControlViewModel(EventDispatcher):

    def __init__(self, *args, **kwargs):
        name = kwargs.pop("name")
        super().__init__(*args, **kwargs)
        self.model = CacheControlModel(name=name)



