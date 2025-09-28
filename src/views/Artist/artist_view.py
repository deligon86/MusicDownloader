import threading
from kivy.clock import Clock

from src.core import logger
from src.core.utils.utils import set_variable
from kivy.properties import StringProperty, ListProperty
from src.views.baseview import BaseNormalScreenView
from src.views.Common.common_widgets import TrendingItem
from src.viewmodels.album_viewmodel import AlbumViewModel


class ArtistSongItem(TrendingItem):

    title = StringProperty()
    image = StringProperty()
    artist = StringProperty()
    url = StringProperty()
    
    def on_release(self):
        if self.when_clicked:
            self.when_clicked(self)
    

class ArtistView(BaseNormalScreenView):
    """
    Display individual artist with their details: name, picture, biography, songs
    """
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
                    'url': details[0],
                    'when_clicked': self.process_item
                    }
                view_data_append(view)

            # Avoid TypeError updating widgets outside kivy thread
            Clock.schedule_once(lambda c: set_variable(self, 'artist_view_data', view_data, c), 0)
        threading.Thread(target=update_view, args=(data, ), daemon=True).start()
                 
    def process_item(self, widget: ArtistSongItem):
        """
        Process item for download
        Arguments:
            widget (ArtistSongItem)
        """
        self._download_processor.process_item(widget=widget, mode="hiphopkit")

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
        Update the recyclerview
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
            msg = f"[ArtistViewGetDownloadLinkError] {error}"
            logger.warning(error)
            self._notification_handler.post_notification(title="Error", message=msg)
