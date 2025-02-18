import os
import re
from Views.baseview import BaseNormalScreenView
from ViewModels.Download.download_viewmodel import DownloadViewModel


class DownloadView(BaseNormalScreenView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.downloaded_items = {}
        self.download_location = None

    def download_task(self):
        pass

    def get_cont(self, title, new_title=True, tag=None, use_tag=False):
        if new_title:
            title = self.disburse_title(title)

        # get group parent, use main layout for now
        parent = self.main_cont

        return parent, title

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
