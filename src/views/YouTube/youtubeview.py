from kivy.animation import Animation
from kivymd.utils import asynckivy
from src.core import logger
from src.viewmodels.youtube_viewmodel import YouTubeViewModel
from src.views.Common.common_widgets import CommonYouTubeItem, CommonYouTubeHttpResultItem
from src.views.baseview import BaseNormalScreenView


class YouTubeView(BaseNormalScreenView):

    def __init__(self, view_model: YouTubeViewModel = None, **kwargs):
        self._view_model = view_model
        super().__init__(**kwargs)

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
        show_mini_progress = isinstance(widget, CommonYouTubeItem)
        self._download_processor.process_item(widget=widget, target_media="video", mini_progress=show_mini_progress)

    def _on_search_results(self, instance, results):
        """
        When the search is complete and has returned results
        :param instance:
        :param results:
        :return:
        """
        if results:
            self.ids.content.clear_widgets()

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
                            command=self.process_item
                            )

                        self.ids.content.add_widget(widget)

        if results[0]:
            Animation(opacity=0, duration=.3).start(self.progress)
            self.progress.stop()
            asynckivy.start(subtask(results))

        else:
            Animation(opacity=0, duration=.3).start(self.progress)
            self.progress.stop()
            msg = "[YouTube Search] No results, Possible error: {}. Raising error".format(results[-1])
            logger.warning(msg)
            self._notification_handler.post_notification(title="Error", message=msg)
            # raise results[-1]
