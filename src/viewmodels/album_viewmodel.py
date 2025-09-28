import threading
from kivy.clock import Clock
from src.models.AlbumEngine.enginesmodel import HipHopKitEngineModel
from kivy.event import EventDispatcher
from kivy.properties import DictProperty, StringProperty, BooleanProperty
from src.core import logger
from src.core.utils.utils import set_variable


class AlbumViewModel(EventDispatcher):
    results = DictProperty(force_dispatch=True)
    navigation_results = DictProperty(force_dispatch=True)
    base_results = DictProperty(force_dispatch=True)
    error_string = StringProperty(force_dispatch=True)
    error = BooleanProperty(force_dispatch=True)

    def __init__(self, model: HipHopKitEngineModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = model
        self.navigate_mode = "songs"

    def search_song(self, query, mode):
        """
        Search

        Arguments:
            mode (str): The search mode, can be any of: `songs`, `albums`, `artist`, 'foreign`
            query (str): The search keyword

        """
        if query:
            def _task(text):
                try:
                    res = self._model.search(text, mode)
                    Clock.schedule_once(lambda c: set_variable(self, 'results', res, c), 0)
                except Exception as e:
                    error = str(e)
                    Clock.schedule_once(lambda c: set_variable(self, 'error', True, c), 0)
                    Clock.schedule_once(lambda c: set_variable(self, 'error_string',
                                                               f"Search error: {error}", c), 0)

            threading.Thread(target=_task, args=(query,), daemon=True).start()

    def navigate_songs(self, page=1):
        """
        Navigate songs pages

        Arguments:
            page (int): The page to navigate to
        """

        def _task(num, mode_):
            try:
                res = self._model.navigate_page(num, mode_)
                Clock.schedule_once(lambda c: set_variable(self,'navigation_results', res, c), 0)
            except Exception as e:
                error = f"Navigate error : {str(e)}"
                Clock.schedule_once(lambda c: set_variable(self, 'error', True, c), 0.02)
                Clock.schedule_once(lambda c: set_variable(self, 'error_string',
                                                           f"{error}", c), 0.01)
                logger.warning(error)


        threading.Thread(target=_task, args=(page, self.navigate_mode), daemon=True).start()

    def get_base_page_results(self, mode):
        """
        Get the page results

        Arguments:
            mode (str): The mode for querying. Can be any of `albums`, `foreign`, `songs`

        Returns:
        """
        def _task(num, _mode):
            try:
                res = self._model.navigate_page(num, _mode)
                Clock.schedule_once(lambda c: set_variable(self, 'base_results', res, c), 0)
            except Exception as e:
                error = str(e)
                Clock.schedule_once(lambda c: set_variable(self, 'error', True, c), 0)
                Clock.schedule_once(lambda c: set_variable(self, 'error_string', f"Base page error : "
                                                                       f"{error}", c), 0)
                logger.warning(self.error_string)

        threading.Thread(target=_task, args=(1, mode), daemon=True).start()

    def get_downloadable_link(self, link):
        """
        Get the link to the remote file with the file contents

        Arguments:
            link (str): The link to fetch downloadable link content from

        Returns:
            A dict containing link, description and tags if its valid, or it will return None
        """
        try:
            res = self._model.get_album_link(link)
            return res
        except Exception as e:
            error = str(e)
            logger.warning(f"[AlbumViewModel] Error fetching download link `{link}` error, {error}")
            Clock.schedule_once(lambda c: set_variable(self, 'error', True, c), 0)
            Clock.schedule_once(lambda c: set_variable(self, 'error_string', f"Link error :{error}",
                                                       c), 0)

