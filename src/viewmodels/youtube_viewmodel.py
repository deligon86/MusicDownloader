import threading
from src.core.utils.utils import set_variable
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import ListProperty
from src.models.YouTube.youtube_model import YouTubeModel


class YouTubeViewModel(EventDispatcher):

    search_results = ListProperty()

    def __init__(self, model: YouTubeModel):
        self._model = model
        super().__init__()

    def search(self, query, mode='fast', audio_only=None, video_only=None, search_one=False):
        """
        Search topic or video url

        Arguments:
            query (str): Keyword or YouTube url
            mode (str): Search in lightweight mode `fast` where no streams are fetched or in comprehensive mode `slow` \
                        where stream objects will be returned, but it will take more time
            audio_only (bool): Filter audio
            video_only (bool): Filter video
            search_one (bool): Expect one item if set to True

        """
        def mini_task(text):
            res = self._model.results_query(text, only_audio=audio_only, video_only=video_only, mode=mode, search_one=search_one)
            res = list(res)
            Clock.schedule_once(lambda c: set_variable(self, "search_results", res, c), 0)

        threading.Thread(target=mini_task, args=(query, ), daemon=True).start()

    def quick_search_url(self, query, audio_only=None, video_only=None):
        """
        Get the streams and return immediately if available instead of running in a thread and broadcasting the results

        Arguments:
            query (str): Keyword or YouTube url
            audio_only (bool): Filter audio
            video_only (bool): Filter video

        """
        stream_group, stream_type, streams  = self._model.results_query(query, only_audio=audio_only, video_only=video_only, mode="slow")

        if stream_group:
            return streams
        else:
            # it will be an error
            raise streams
