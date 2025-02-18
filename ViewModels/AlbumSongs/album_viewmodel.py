import threading

from Models.AlbumEngine.enginesmodel import HipHopKitEngineModel
from kivy.event import EventDispatcher
from kivy.properties import DictProperty


class AlbumViewModel(EventDispatcher):
    results = DictProperty()
    navigation_results = DictProperty()
    base_results = DictProperty()

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
                res = self._model.search(text, mode)
                self.results = res

            threading.Thread(target=_task, args=(query,), daemon=True).start()

    def navigate_songs(self, page=1):
        """
        Navigate songs pages
        :param page:
        :return:
        """

        def _task(num, mode_):
            res = self._model.navigate_page(num, mode_)
            self.navigation_results = res

        threading.Thread(target=_task, args=(page, self.navigate_mode), daemon=True).start()

    def get_base_page_results(self, mode):
        """
        :param mode: see Models.enginesmodel.HipHopKitEngineModel.navigate_page
        :return:
        """
        def _task(num, _mode):
            res = self._model.navigate_page(num, _mode)
            self.base_results = res

        threading.Thread(target=_task, args=(1, mode), daemon=True).start()

