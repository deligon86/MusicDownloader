import re
import time

import requests
from network import logger
from youtubesearchpython import VideosSearch
from pytubefix import YouTube, Search
from Core.utils.utils import is_connected, is_valid_youtube_link
from PyQt6.QtCore import QThread

class YouTubeModel:

    def __init__(self):
        self.cache = {}

    def results_query(self, text, mode="fast", only_audio=None, video_only=None, search_one=False):
        """
        :param text:
        :param mode:
        :return: single, streams or multi, results
        """
        logger.info(f"[Searching] Searching for: {text}")
        if not search_one:
            type_, value = self.url_build(text)
            if value in self.cache:
                logger.info("[Cache] Reload from cache")
                res, mode, type_ = self.cache.get(value)
                return mode, type_, res
            else:
                try:
                    if mode == "fast":
                        if type_ == 'url':
                            # print("*** ", text, " ***")
                            res = YouTube(url=text, use_oauth=True, allow_oauth_cache=True).streams.filter(only_audio=only_audio, only_video=video_only)
                            '''while True:
                                if res:
                                    break
                                QThread.sleep(100)'''
                            if res:
                                self.cache[value] = [res, 'Single', "streams"]

                            return 'Single', "streams", res
                        else:
                            res = self.fast_api_search(value)
                            '''while True:
                                if res:
                                    break
                                QThread.sleep(100)'''
                            if res:
                                self.cache[text] = [res, 'multi', "list_dict"]
                            return "multi", "list_dict", res
                    else:
                        if type_ == "url":
                            res = YouTube(url=text, use_oauth=True, allow_oauth_cache=True).streams.filter(only_audio=only_audio, only_video=video_only)
                            '''while True:
                                if res:
                                    break
                                QThread.sleep(100)'''
                            if res:
                                self.cache[value] = [res, 'Single', "streams"]
                            return 'Single', "streams", res
                        else:
                            res = self.slow_api_search(value)
                            '''while True:
                                if res:
                                    break
                                QThread.sleep(100)'''
                            if res:
                                self.cache[text] = [res, 'multi', "list"]
                            return "multi", "list", res

                except Exception as e:
                    return None, "Error", e
        else:
            # search for only one
            type_, url = self.url_build(text)
            if type_ == "text":
                res, vid_object = self.fast_api_search(url)
                my_result = res[0]

                return my_result

    def url_build(self, text):
        """Build the url"""
        logger.info("[URL Builder] Setting up query url")
        if "https" in text:
            # check validity of url
            if is_valid_youtube_link(text):
                return 'url', text
            else:
                return None, "Invalid Video Link"
        else:
            return 'text', text

    def fast_api_search(self, build_url):
        """Fast Search
        :param build_url
        id, title, publishedTime, duration, viewCount['short'],
        thumbnails[0]['url'], descriptionSnippet['text'],
        channel['name'], channel['thumbnails'][0]['url'],
        link
        """
        logger.info("[Search] Using fast api search")
        if is_connected():
            req = VideosSearch(build_url)
            results = req.result()
            results = self.parse_fast_results(results['result'])

            return results, req

    @staticmethod
    def parse_fast_results(results_):
        logger.info(f"[Parser] Parsing resulyts total count: {len(results_)}")
        items = []
        for results in results_:
            # print(results)
            search_result = dict()
            search_result['link'] = results['link']
            search_result['title'] = results['title']
            search_result['posted'] = results['publishedTime']
            search_result['duration'] = results['duration']
            try:

                search_result['description'] = results['descriptionSnippet'][0]['text']
            except:
                search_result['description'] = "Np description"
            search_result['thumbnail'] = results['thumbnails'][0]['url']
            search_result['views'] = results['viewCount']['short']
            search_result['channel'] = results['channel']['name']
            search_result['channel-image'] = results['thumbnails'][0]['url']
            items.append(search_result)
        logger.info("[Parser] Done")
        return items

    @staticmethod
    def parse_slow_api_results(results):
        """
        Parse the results to a dict for more readability
        """
        parsed = []
        for item in results:
            res = {}

            parsed.append(res)

    def slow_api_search(self, build_url):
        """Slow and all in one search containing direct download links"""
        logger.info("[Search] Using slow, exclusive")
        yt = Search(build_url)
        return yt.results
