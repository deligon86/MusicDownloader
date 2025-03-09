import random

from kivy.animation import Animation
from kivymd.utils import asynckivy
from kivymd.uix.progressbar.progressbar import MDProgressBar
from ViewModels.YouTube.viewmodel import YouTubeViewModel
from Views.Common.common_widgets import CommonYouTubeItem, CommonYouTubeHttpResultItem
from Views.baseview import BaseNormalScreenView


class YouTubeView(BaseNormalScreenView):

    def __init__(self, view_model: YouTubeViewModel = None, *args, **kwargs):
        self._view_model = view_model
        super().__init__(*args, **kwargs)

        self._view_model.bind(search_results=self._on_search_results)
        self.progress = self.ids.progress

    def search(self, text):
        self.progress.opacity = 1
        self.progress.start()

        self._view_model.search(text)

    def process_item(self, widget: CommonYouTubeItem | CommonYouTubeHttpResultItem):
        """
        Process the item before passing to downloader
        :param widget  CommonYouTubeItem or CommonYouTubeResultItem
        :return:
        """
        if widget.downloadable:
            self._main_view.add_to_download_queue(
                title=widget.title, link=widget.link,
                type_=widget.stream_type, format_=widget.stream_format
                )
        else:
            # have to further process it
            streams = self._view_model.quick_search_url(widget.link)
            stream = self.select_quality(streams)
            self._main_view.add_to_download_queue(
                title=widget.title, link=stream.url,
                type_=stream.type, format_=stream.sub_type
                )

    @staticmethod
    def select_quality(streams, standard="120kbps", mode="audio"):
        """
        Select a quality from the streams
        :param streams: list of streams
        :param standard: default 126kbps in audio maximum is 326kbps, default for video 720p but depends on the stream can be upto 2k
        :param mode: audio/video
        :return:
        """

        if mode == "audio":
            stream_quality = [stream.abr for stream in streams]
            stream_quality_int = [stream.split("kb")[0] for stream in stream_quality]
        else:
            standard = "720p"
            stream_quality = [stream.resolution for stream in streams]
            stream_quality_int = [stream.split("p")[0] for stream in stream_quality]

        if stream_quality in stream_quality:
            index = stream_quality.index(standard)
            return streams[index]
        else:
            indices = {}  # store the original stream index
            for i, val in enumerate(stream_quality):
                indices[val] = i

            qualities_int_sorted = sorted(stream_quality_int)
            # reconstruct the whole thing together
            if mode == "audio":
                return streams[indices[f"{qualities_int_sorted[-1]}kbps"]]
            else:
                return streams[indices[f"{qualities_int_sorted[-1]}p"]]

    def _on_search_results(self, instance, results):
        """
        When the search is complete and has returned results
        :param instance:
        :param results:
        :return:
        """

        async def subtask(res):
            mode, type_, data = res
            if mode == "Single":
                if type_ == "streams":
                    # used a YouTube link from search so data contain audio/video stream object
                    for stream in data:
                        quality = "Redacted"
                        format_ = ""

                        if stream.type.lower() == "video":
                            quality = stream.resolution
                        elif stream.type.lower() == "audio":
                            quality = stream.abr

                        format_ = stream.subtype

                        ci = CommonYouTubeHttpResultItem(
                            stream_type=stream.type,
                            title=stream.title,
                            stream_quality=quality,
                            link=stream.url,
                            stream_format=format_,
                            downloadable=True,
                            command=self.process_item
                            )
                        self.ids.content.add_widget(ci)

            elif mode == "Multi":
                if type_ == "list":
                    # list of results from YouTube object
                    for stream in data:
                        quality = "0"
                        format_ = ""

                        if stream.type.lower() == "video":
                            quality = stream.resolution
                        elif stream.type.lower() == "audio":
                            quality = stream.abr

                        format_ = stream.subtype

                        ci = CommonYouTubeHttpResultItem(
                            stream_type=stream.type,
                            title=stream.title,
                            stream_quality=quality,
                            link=stream.url,
                            stream_format=format_,
                            downloadable=True,
                            command=self.process_item
                            )
                        self.ids.content.add_widget(ci)

                elif type_ == "list_dict":
                    # from fast mode: list of dicts
                    for item in data:
                        widget = CommonYouTubeItem(
                            thumbnail=item['thumbnail'],
                            title=item['title'],
                            description=item['description'],
                            publish_date=str(item['posted']),
                            link=item['link'],
                            author=item['channel'],
                            views=item['views'],
                            channel_image=item['channel-image'],
                            duration=item['duration'],
                            downloadable=False,
                            command=self.process_youtube_item
                            )

                        self.ids.content.add_widget(widget)

        Animation(opacity=0, duration=.2).start(self.progress)
        self.progress.stop()

        asynckivy.start(subtask(results))


