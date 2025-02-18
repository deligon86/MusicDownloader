import threading

from kivy.event import EventDispatcher
from kivy.properties import DictProperty, StringProperty
from Models.Billboard.billboardmodel import BillBoardManagerModel


class BillBoardViewModel(EventDispatcher):
    trending_songs = DictProperty()
    trending_artists = DictProperty()
    category = StringProperty("all")
    top_americas = DictProperty()

    def __init__(self, model:BillBoardManagerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = model

    def get_trending_artists(self):

        def mini_task():
            artists = self._model.top_artists(size=None)  # fetch all
            self.trending_artists = artists
        threading.Thread(target=mini_task, daemon=True).start()

    def get_trending_songs(self):
        url = self._model.all_200

        match self.category:
            case "brazil":
                url = self._model.brazil
            case "france":
                url = self._model.france
            case "italy":
                url = self._model.italy
            case "india":
                url = self._model.india
            case "safrica":
                url = self._model.safrica
            case "spain":
                url = self._model.spain
            case "uk":
                url = self._model.uk

        def mini_task(category_url):
            cat_res = self._model.top_songs(category_url)
            self.trending_songs = cat_res

        threading.Thread(target=mini_task, args=(url, ), daemon=True).start()

    def get_top_america(self):

        def mini_task():
            cat_res = self._model.get_top_americas()
            self.top_americas = cat_res

        threading.Thread(target=mini_task, daemon=True).start()

