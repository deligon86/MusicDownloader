import queue
import threading

from kivy.clock import Clock

from Models.AlbumEngine.enginesmodel import HipHopKitEngineModel
from kivy.event import EventDispatcher
from kivy.properties import DictProperty, StringProperty, BooleanProperty


class AlbumViewModel(EventDispatcher):
    results = DictProperty()
    navigation_results = DictProperty()
    base_results = DictProperty()
    error_string = StringProperty()
    error = BooleanProperty()

    def __init__(self, model: HipHopKitEngineModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = model
        self.navigate_mode = "songs"

    def search_song(self, query, mode):
        """
        Search
        :param mode:
        :param query: see Models.enginesmodel.HipHopKitEngineModel.search
        :return:
        """
        if query:
            def _task(text):
                try:
                    res = self._model.search(text, mode)
                    Clock.schedule_once(lambda c: self.set_variable('results', res, c), 0)
                except Exception as e:
                    Clock.schedule_once(lambda c: self.set_variable('error', True, c), 0)
                    Clock.schedule_once(lambda c: self.set_variable('error_string', str(e), c), 0)

            threading.Thread(target=_task, args=(query,), daemon=True).start()

    def navigate_songs(self, page=1):
        """
        Navigate songs pages
        :param page:
        :return:
        """

        def _task(num, mode_):
            try:
                res = self._model.navigate_page(num, mode_)
                Clock.schedule_once(lambda c: self.set_variable('navigation_results', res, c), 0)
            except Exception as e:
                error = str(e)
                Clock.schedule_once(lambda c: self.set_variable('error', True, c), 0)
                Clock.schedule_once(lambda c: self.set_variable('error_string', error, c), 0)

        threading.Thread(target=_task, args=(page, self.navigate_mode), daemon=True).start()

    def get_base_page_results(self, mode):
        """
        :param mode: see Models.enginesmodel.HipHopKitEngineModel.navigate_page
        :return:
        """
        def _task(num, _mode):
            try:
                res = self._model.navigate_page(num, _mode)
                Clock.schedule_once(lambda c: self.set_variable('base_results', res, c), 0)
            except Exception as e:
                Clock.schedule_once(lambda c: self.set_variable('error', True, c), 0)
                Clock.schedule_once(lambda c: self.set_variable('error_string', f"Base page error: {e}", c), 0)

        threading.Thread(target=_task, args=(1, mode), daemon=True).start()

    def get_downloadable_link(self, link):
        q = queue.Queue()

        def _task(q_, link_):
            try:
                res = self._model.get_album_link(link_)
                q_.put(res)
            except Exception as e:
                Clock.schedule_once(lambda c: self.set_variable('error', True, c), 0)
                Clock.schedule_once(lambda c: self.set_variable('error_string', str(e), c), 0)

        threading.Thread(target=_task, args=(q, link))

        if not q.empty():
            return q.get_nowait()

    def set_variable(self, variable, data, dt=None):
        """
        Update the variables
        :param variable:
        :param data:
        :param dt:
        :return:
        """
        setattr(self, variable, data)
