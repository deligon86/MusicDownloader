import threading

from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty

from Views.baseview import BaseNormalScreenView
from Views.Common.common_widgets import TrendingItem
from ViewModels.AlbumSongs.album_viewmodel import AlbumViewModel
from Core.utils.utils import get_web_file_size


class ArtistSongItem(TrendingItem):
    """
    TODO: Add a progress indicator and disable widget while processing item to download
    """
    title = StringProperty()
    image = StringProperty()
    artist = StringProperty()
    url = StringProperty()
    
    def on_release(self):
        if self.when_clicked:
            self.when_clicked(self)
    

class ArtistView(BaseNormalScreenView):
    artist_view_data = ListProperty()

    def __init__(self, album_vm: AlbumViewModel = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._album_viewmodel = album_vm
        self._album_viewmodel.bind(error_string=self._on_error)
        self.bind(artist_view_data=self.update_view)
    
    def refresh_view(self, data, artist, bio, image):
        """
        
        Populate the view
        :param image: 
        :param bio: 
        :param artist: 
        :param data: dict[title] [url, image, song_background_story]
        :return: 
        """
        self.ids.image.source = image
        self.ids.bio.text = bio
        self.ids.artist.text = artist

        def update_view(data_dict):
            view_data = []
            view_data_append = view_data.append
            for title, details in data_dict.items():
                view = {
                    'viewclass': 'ArtistSongItem',
                    'artist': artist,
                    'image': details[1],
                    'title': title,
                    'url': details[0]
                    }
                view_data_append(view)

            # Avoid TypeError updating widgets outside kivy thread
            Clock.schedule_once(lambda c: self.set_artist_data(view_data, c), 0)
        threading.Thread(target=update_view, args=(data, ), daemon=True).start()
                 
    def process_item(self, widget: ArtistSongItem):
        """
        Process item for download
        :param widget: 
        :return: 
        """
        results = self._album_viewmodel.get_downloadable_link(widget.url)
        if results:
            link = results[0]
            size = get_web_file_size(link)
            if size > 15:
                type_ = "Zip"
                sub_type = "zip"
            else:
                type_ = "Audio"
                sub_type = "mp3"

            self._main_view.add_to_download_queue(widget.title, link, type_, sub_type)

    def set_artist_data(self, view_data, dt=None):
        """
        Set the artist data
        :param view_data:
        :param dt:
        :return:
        """
        self.artist_view_data = view_data

    def update_view(self, instance, data):
        """
        Update the recycleview
        :param instance:
        :param data:
        :return:
        """
        if data:
            self.ids.content.data = data
            self.ids.content.refresh_from_data()

    def _on_error(self, instance, error):
        """
        When an exception is thrown while trying to get the download link
        :param instance:
        :param error:
        :return:
        """
        if error:
            print(error)