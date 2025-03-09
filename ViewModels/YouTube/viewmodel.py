import threading

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import ListProperty
from Models.YouTube.youtube_model import YouTubeModel


class YouTubeViewModel(EventDispatcher):

    search_results = ListProperty()

    def __init__(self, model: YouTubeModel):
        self._model = model
        super().__init__()

    def search(self, query, mode='fast', audio_only=None, video_only=None, search_one=False):
        """
        Search topic or video url
        """
        def mini_task(text):
            res = self._model.results_query(text)
            res = list(res)
            Clock.schedule_once(lambda c: self.set_results(res, c), 0)

        threading.Thread(target=mini_task, args=(query, ), daemon=True).start()

    def set_results(self, results, dt=None):

        self.search_results = results

    def quick_search_url(self, url, audio_only=None, video_only=None):
        """
        Get the streams
        :param url:
        :return:
        """
        res = self._model.results_query(url, only_audio=audio_only, video_only=video_only)
        return res[-1]
