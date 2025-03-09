import threading

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import DictProperty, StringProperty
from Models.Billboard.billboardmodel import BillBoardManagerModel


class BillBoardViewModel(EventDispatcher):
    trending_songs = DictProperty()
    trending_artists = DictProperty()
    category = StringProperty("all")
    top_americas = DictProperty()
    error = StringProperty()

    def __init__(self, model: BillBoardManagerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = model

    def get_trending_artists(self, size=None):

        def mini_task():
            try:
                songs = self._model.top_songs(size=size)  # fetch all
                Clock.schedule_once(lambda c: self.set_variable("trending_songs", songs, c), 0)
            except ConnectionError:
                Clock.schedule_once(lambda c: self.set_variable("error", f"Cannot get trending songs. No intenet", c), 0)
            except Exception as e:
                error = str(e)
                Clock.schedule_once(lambda c: self.set_variable("error", f"Error getting trending songs: {error}", c), 0)

        threading.Thread(target=mini_task, daemon=True).start()

    def get_trending_songs(self, size=None):
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

        def mini_task(category_url, size_):
            try:
                artists = self._model.top_artists(size=size)  # fetch all
                Clock.schedule_once(lambda c: self.set_variable("trending_artists", artists, c), 0)
            except ConnectionError:
                Clock.schedule_once(lambda c: self.set_variable("error", "Error getting billboard artists. No internet", c), 0)
            except Exception as e:
                error = str(e)
                Clock.schedule_once(lambda c: self.set_variable("error", f"Error getting billboard artists: {error}", c), 0)

        threading.Thread(target=mini_task, args=(url, size), daemon=True).start()

    def get_top_america(self):

        def mini_task():
            try:
                cat_res = self._model.get_top_americas()
                Clock.schedule_once(lambda c: self.set_variable("top_americas", cat_res, c), 0)
            except Exception as e:
                error = str(e)
                Clock.schedule_once(lambda c: self.set_variable('error', f"Error fetching Americas: {error}", c), 0)

        threading.Thread(target=mini_task, daemon=True).start()

    def set_variable(self, variable, data, dt=None):
        """
        Update variables
        :param variable:
        :param data:
        :param dt:
        :return:
        """
        setattr(self, variable, data)
