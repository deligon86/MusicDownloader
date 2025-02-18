import threading
from kivy.event import EventDispatcher
from kivy.properties import ListProperty
from Models.YouTube.youtube_model import YouTubeModel


class YouTubeViewModel(EventDispatcher):

    results_changed = ListProperty()

    def __init__(self, model: YouTubeModel):
        self._model = model
        super().__init__()

    def search(self, query):
        """
        Search topic or video url
        """
        def mini_task(text):
            res = self._model.results_query(text)
            self.results_changed = list(res)

        threading.Thread(target=mini_task, args=(query, ), daemon=True).start()
