import datetime
import os
import re
import queue

from docutils.nodes import container
from kivy.metrics import dp
from kivy.properties import StringProperty

from Views.Common.common_layouts import AutoCustomThemeCard
from Views.Common.common_widgets import CommonLabel
from Views.baseview import BaseNormalScreenView
from Models.Download.downloadmodel import DownloadModel
from ViewModels.Download.download_viewmodel import DownloadViewModel


class DownloadViewContainer(AutoCustomThemeCard):
    tag = StringProperty()


class DownloadView(BaseNormalScreenView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.downloaded_items = {}
        self.download_location = os.path.join(os.path.expanduser("~"), "Downloads")
        self.download_queue = queue.Queue()
        self.active_task_count = 0
        self.maximum_task_count = 3

    def add_to_queue(self, title, link, type_, format_):
        if self.active_task_count == self.maximum_task_count:
            self.download_queue.put_nowait((title, link, type_, format_))
        else:
            self.download_task(title, link, type_, format_)

    def download_task(self, task_title, task_link, task_type, task_format):
        """
        Download the task
        :param task_title: title
        :param task_link: the downloadable link
        :param task_type: Audio/Video/Zip
        :param task_format: compatible file extension
        :return:
        """
        cont, title = self.get_cont(task_title)
        download_item = DownloadViewModel(model=DownloadModel())
        download_item.bind(finished=self._on_task_finished)
        cont.add_widget(download_item)
        cont.height = (len(cont.children) - 1) * dp(download_item.height) + dp(50)

        download_item.set_variables(
            title=title, link=task_link, file_type=task_type, file_format=task_format,
            download_path=self.download_location
        )
        self.active_task_count += 1

    def get_cont(self, title, new_title=True, tag=None, use_tag=False):
        """
        Get the container according to the tag to add downloads
        :param title:
        :param new_title:
        :param tag: date in formart Day Month, year
        :param use_tag:
        :return:
        """
        if new_title:
            title = self.disburse_title(title)

        # get group parent, use main layout for now
        parent = self.ids.content
        tag_ = str(datetime.datetime.now().strftime("%B %d, %Y"))
        cont = [child for child in parent.children if child.tag == tag_]
        if cont:
            container = cont[0]
        else:
            if use_tag:
                if tag:
                    tag_ = tag
            container = DownloadViewContainer(tag=tag_)
            container.add_widget(CommonLabel(text=tag_,
                                             sub_header=True,
                                             size_hint_y=None,
                                             height=dp(48)))
            parent.add_widget(container)

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
            files = os.listdir(self.download_location)
            processed = [file.split(".")[0] for file in files]
            if title in processed:
                count = max(set(processed), key=processed.count)
                title = f"{title}-{count}"

        return title

    def _on_task_finished(self, _, finished):
        if finished:
            self.active_task_count -= 1
            # check for item in queue and download
            if not self.download_queue.empty():
                task = self.download_queue.get_nowait()
                self.download_task(*task)
