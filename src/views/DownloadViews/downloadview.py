import os
import re
import random
import datetime

from kivy.clock import Clock
from kivymd.utils import asynckivy
from src.core import logger
from src.core.utils.utils import load_download_data
from kivy.metrics import dp
from kivy.properties import (
    StringProperty, ObjectProperty
)
from src.viewmodels.download_viewmodel import DownloadViewModel
from src.views.baseview import BaseNormalScreenView
from src.views.Common.common_widgets import CommonLabel
from src.views.Common.common_layouts import AutoCustomThemeCard
from src.views.DownloadViews.downloadviewitem import DownloadViewItem


class DownloadViewContainer(AutoCustomThemeCard):
    tag = StringProperty()


class DownloadView(BaseNormalScreenView):
    _download_view_model = ObjectProperty()

    def __init__(self, download_view_model:DownloadViewModel=None, **kwargs):
        super().__init__(**kwargs)
        self.downloaded_items = {}
        self.dl_view_model_binded = False
        self._download_view_model = download_view_model

        if self._download_view_model and not self.dl_view_model_binded:
            self.bind_download_view_model()
        else:
            self.bind(_download_view_model=self.on_download_view_model,
                      download_cache_batch=self.on_download_cache_batch)

    def add_to_download_queue(self, title, link, type_, format_, view_model_id):
        self._download_view_model.add_to_queue(title=title, link=link, type_=type_,
                                              format_=format_, view_model_id=view_model_id)

    def bind_download_view_model(self):
        self.dl_view_model_binded = True
        self._download_view_model.bind(download_task=self.on_download_task,
                                        download_cache_batch = self.on_download_cache_batch)

    def start_simulation(self):
        """
        For development testing of widgets functionality and behavior
        :return:
        """
        types = ["Audio", "Video", "Zip"]
        formats = ["mp3", "mp4", "zip"]
        for iteration in range(len(self.downloaded_items), len(self.downloaded_items) + 10):
            vmid, vm = self._download_view_model.generate_view_model()
            self.add_to_download_queue(title=f"Title: {iteration}", link=f"Link: {iteration}",
                                       type_=random.choice(types), format_=random.choice(formats), view_model_id=vmid)

    def get_cont(self, title, new_title=True, tag=None):
        """
        Get the container according to the tag to add downloads
        :param title:
        :param new_title:
        :param tag: date in format Day Month, year
        :return:
        """
        if new_title:
            title = self.disburse_title(title)

        # get group parent, use main layout for now
        parent = self.ids.content
        if tag:
            tag_ = tag
        else:
            tag_ = str(datetime.datetime.now().strftime("%B %d, %Y"))

        cont = [child for child in parent.children if child.tag == tag_]
        if cont:
            container = cont[0]
        else:
            container = DownloadViewContainer(tag=tag_)
            container.theme_changed = True  # trigger update
            container.add_widget(CommonLabel(text=tag_,
                                             sub_header=True,
                                             size_hint_y=None,
                                             height=dp(48)))
            parent.add_widget(container)
            container.height = dp(50)

        return container, title

    def disburse_title(self, title):

        def get_count(title_, keys):
            found = []
            for key in keys:
                m = re.search(title_, key)
                if m:
                    found.append(key)
            return len(found)

        c = get_count(title, self.downloaded_items.keys())
        if c > 0:
            title = f"{title}-({c + 1})"
        else:
            # look in location
            files = os.listdir(self._download_view_model.download_location)
            processed = [file.split(".")[0] for file in files]
            if title in processed:
                count = max(set(processed), key=processed.count)
                title = f"{title}-{count}"

        return title

    def load_download_cache(self, cache_data):
        for cache in cache_data:
            id_, vm = self._download_view_model.generate_view_model()
            item = DownloadViewItem(download_item_view_model=vm)
            # dirty way fix for assigning the important fields like title, link, e.t.c
            vm.model.title = cache.get('title')
            vm.model.download_file_path = cache.get("path")
            vm.model.url = cache.get("link")
            vm.model.file_type = cache.get("filetype")
            vm.silent_notification = True
            item.set_variables(cache.get("title"), cache.get("link"), cache.get("filetype"),
                               cache.get("file_format"), cache.get("path"), offline=True)
            cont, _ = self.get_cont(cache.get("title"), tag=cache.get("date"))
            cont.add_widget(item)
            cont.height += dp(110)
            vm.finished_download = True

    def on_enter(self, *args):
        # test download widgets behavior
        if self._download_view_model.simulate_downloads:
            self.start_simulation()

    def on_start(self, _=None):
        """
        When the application is launching
        """
        self._download_view_model.start_batch_loader()

    def on_download_task(self, _, task):
        """
        A task is ready to be downloaded
        Attributes:
            _ : binder instance
            task (dict): A dictionary containing the download data

        """
        logger.info(f"[Download] Task {task}")
        if task:
            cont, title = self.get_cont(task.get("title"))  # get cont by title
            view_model = self._download_view_model.get_item_view_model(task.get("view_model_id"))
            download_item = DownloadViewItem(download_item_view_model=view_model)

            cont.add_widget(download_item)
            cont.height = (len(cont.children) - 1) * dp(download_item.height) + dp(50) + (
                        (len(cont.children) - 1) * dp(5))

            download_item.set_variables(
                title=title, link=task.get('link'), file_type=task.get("type"), file_format=task.get("format"),
                download_path=self._download_view_model.download_location,
                simulated=self._download_view_model.simulate_downloads
            )  # can set the simulated flag here for testing

            download_item.theme_changed = True  # Trigger theme changes
            self.downloaded_items[task.get('title')] = task

    def on_download_view_model(self, _, view_model):
        if view_model:
            self.bind_download_view_model()

    def on_download_cache_batch(self, _, batch):
        if batch:
            self.load_download_cache(batch)
