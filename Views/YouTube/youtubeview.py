from kivy.properties import ObjectProperty

from Views.baseview import BaseNormalScreenView
from ViewModels.YouTube.viewmodel import YouTubeViewModel


class YouTubeView(BaseNormalScreenView):

    def __init__(self, view_model: YouTubeViewModel=None, *args, **kwargs):
        self._view_model = view_model
        self._view_model.bind(results_changed=self._on_search_results)

        super().__init__(*args, **kwargs)

    def search(self, text):
        self._view_model.search(text)

    def _on_search_results(self, instance, results):
        """
        When the search is complete and has returned results
        :param instance:
        :param results:
        :return:
        """
