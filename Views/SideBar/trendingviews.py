import threading
from kivy.properties import ObjectProperty, ListProperty
from kivy.clock import Clock

from Views.baseview import BaseNormalScreenView
from Views.Common.common_widgets import TrendingArtistViewItem, TrendingSongViewItem
from ViewModels.Billboard.billboard_viewmodel import BillBoardViewModel
from ViewModels.AlbumSongs.album_viewmodel import AlbumViewModel
from ViewModels.YouTube.viewmodel import YouTubeViewModel


class TrendingArtistView(BaseNormalScreenView):
    app = ObjectProperty()
    trending_artist_recycle_view_data = ListProperty()

    def __init__(self, billboard_vm: BillBoardViewModel, album_dl_vm: AlbumViewModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._view_model = billboard_vm
        self._album_view_model = album_dl_vm
        self._view_model.bind(trending_artists=self._on_artists,
                              error=self._on_refresh_error)
        self._album_view_model.bind(results=self._on_artist_probed,
                                    error_string=self._on_artist_probe_error)
        self.bind(trending_artist_recycle_view_data=self.update_recycle_view)
        self.bio_data = {}

    def refresh_view(self):
        """
        Reload the data directly from the web: Only 50
        :return:
        """
        # change progress color and start
        self.ids.progress.parent.height = 4
        self.ids.progress.opacity = 1
        self.ids.progress.color = self.app.theme_color
        self.ids.progress.start()
        # self._view_model.get_trending_artists(size=50)
        # create dummy data
        data = {}
        for n in range(20):
            data[f'artist {n}'] = ['image', 'bio']

        self._view_model.trending_artists = data

    def probe_artist(self, artist, bio, image):
        """
        Invoked when the TrendingArtistItem is clicked
        :param image:
        :param bio:
        :param artist:
        :return:
        """
        if artist not in self.bio_data:
            self.bio_data[artist] = [bio, image]
        self._album_view_model.search_song(artist, "artist")

    def set_artist_data(self, data, dt=None):
        self.trending_artist_recycle_view_data = data

    def update_recycle_view(self, instance, data):
        """
        Update the view from data
        :param instance:
        :param data:
        :return:
        """
        self.ids.progress.color = self.md_bg_color
        self.ids.progress.stop()
        self.ids.progress.parent.height = 0
        self.ids.progress.opacity = 0
        if data:
            self.ids.trending_artist.data = data
            self.ids.trending_artist.refresh_from_data()

    def _on_artists(self, instance, results):
        """
        If the view is refreshed and results are ready
        :param instance:
        :param results: dict[artist][image, bio]
        :return:
        """
        if results:

            def subtask(data: dict):
                view_data = []
                view_data_append = view_data.append  # faster compared to list.append('')

                for artist, details in data.items():
                    view = {
                        'viewclass': 'TrendingArtistViewItem',
                        'artist': artist,
                        'bio': details[1],
                        'image': details[0],
                        'when_clicked': self.probe_artist
                        }
                    view_data_append(view)

                Clock.schedule_once(lambda c: self.set_artist_data(view_data, c), 0)
            threading.Thread(target=subtask, args=(results, ), daemon=True).start()

    def _on_artist_probed(self, instance, results):
        """
        If the user clicked the TrendingArtistItem and results are received from
        album view model
        :param instance:
        :param results: dict[title][url, image, song_background_story]
        :return:
        """
        # will need to be posted to artist only view
        # Get the artist view from main view
        view = self._main_view.views['Artist View']
        # get the recently added artist
        key = list(self.bio_data.keys())[-1]
        bio, image = self.bio_data[key]
        view.refresh_view(results, key, bio, image)

    def _on_refresh_error(self, instance, error):
        """
        When there is internal error from BillboardModel when fetching content
        :param instance:
        :param error:
        :return:
        """
        if error:
            try:
                self.ids.progress.color = self.md_bg_color
                self.ids.progress.stop()
                self.ids.progress.parent.height = 0
                self.ids.progress.opacity = 0
            except TypeError:
                print("Cannot update Progress bar from external thread")

            print(error)

    def _on_artist_probe_error(self, instance, error):
        """
        When an error occur while trying to get probe artists
        :param instance:
        :param error:
        :return:
        """
        print(error)


class TrendingSongView(BaseNormalScreenView):
    app = ObjectProperty()
    trending_song_view_recycle_data = ListProperty()

    def __init__(self, view_model: BillBoardViewModel = None, yt_vm: YouTubeViewModel=None,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self._view_model = view_model
        self._youtube_view_model = yt_vm

        self._view_model.bind(trending_songs=self._on_songs,
                              error=self._on_refresh_error)
        self._youtube_view_model.bind(search_results=self._on_song_probe)
        self.bind(trending_song_view_recycle_data=self.update_recycle_view)

    def refresh(self):
        """
        Reload the songs: only 100
        :return
        """
        # set progress color and start
        self.ids.progress.parent.height = 4
        self.ids.progress.opacity = 1
        self.ids.progress.color = self.app.theme_color
        self.ids.progress.start()
        self._view_model.get_trending_songs(size=100)

    def probe_song(self, song):
        """
        Invoked when the TrendingSongItem in clicked
        :param song:
        :return:
        """
        self._youtube_view_model.search(song, mode="normal", audio_only=True)

    def set_song_data(self, data, dt=None):
        self.trending_song_view_recycle_data = data

    def update_recycle_view(self, instance, data):
        """
        Update the trending songs recycleview
        :param instance:
        :param data:
        :return:
        """
        self.ids.progress.color = self.md_bg_color
        self.ids.progress.stop()
        self.ids.progress.parent.height = 0
        self.ids.progress.opacity = 0
        if data:
            self.ids.trending_song.data = data
            self.ids.trending_song.refresh_from_data()

    @staticmethod
    def select_quality(standard="128kbps", streams=None):
        """
        Select the quality to download from the streams
        :param standard:
        :param streams: List of streams
        :return:
        """
        qualities = [stream.abr for stream in streams if stream.type.lower() == "audio"]

        if standard in qualities:
            return streams[qualities.index(standard)]
        else:
            # sort and get the last on list which is the highest
            indices = {}  # store the original stream index
            for i, val in enumerate(qualities):
                indices[val] = i

            qualities_int = sorted([int(val.split("kb"[0])) for val in qualities])
            return streams[indices[f"{qualities_int[-1]}kbps"]]

    def _on_songs(self, instance, results: dict):
        if results:
            def update_subtask(data: dict):
                view_data = []
                view_data_append = view_data.append

                for song, details in data.items():
                    if not isinstance(details, (list, tuple)) or len(details) < 2:
                        print(f"Skipping invalid data for {song}: {details}")
                        continue  # Skip invalid data

                    view = {
                        'viewclass': 'TrendingSongViewItem',
                        'artist': details[0],
                        'image': details[1],
                        'song': song,
                        'when_clicked': self.probe_song
                        }
                    view_data_append(view)

                Clock.schedule_once(lambda c: self.set_song_data(view_data, c), 0)
            threading.Thread(target=update_subtask, args=(results,), daemon=True).start()

    def _on_song_probe(self, instance, results):
        """
        Results are ready
        :param instance:
        :param results:
        :return:
        """
        if results:
            mode, type_, data = results
            stream = self.select_quality(streams=data)
            # title, download_url, type[Audio], file extension
            dl_data = (stream.title, stream.url, stream.type, stream.subtype)
            # post to download queue
            self._main_view.add_to_download_queue(*dl_data)

    def _on_refresh_error(self, instance, error):
        """
        Error while trying to refresh
        :param instance:
        :param error:
        :return:
        """
        if error:
            self.ids.progress.color = self.md_bg_color
            self.ids.progress.stop()
            self.ids.progress.parent.height = 0
            self.ids.progress.opacity = 0
            print(error)

