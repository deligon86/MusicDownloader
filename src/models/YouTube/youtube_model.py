from src.core import logger
from youtubesearchpython import VideosSearch
from pytubefix import YouTube, Search, StreamQuery
from src.core.utils.utils import is_valid_youtube_link


class YouTubeModel:

    def __init__(self, use_auth=False, allow_auth_cache=False):
        self.use_auth = use_auth
        self.allow_auth_cache = allow_auth_cache
        self.cache = {}

    def results_query(self, text, mode="fast", only_audio=None, video_only=None, search_one=False):
        """
        Perform a search

        :param text: Search keyword
        :param mode: lightweight mode `fast` or comprehensive mode `slow` that will return stream objects
        :param only_audio: Filter audio
        :param video_only: Filter video
        :param search_one: Return only 1 item
        :return:
            A tuple. `(Single, streams, results)` or `(Multi, list_dict, results)` or `(Multi, list, results)`
            The first value in the returned tuple is the mode, the second value being the result type it can be \
            list or list of dicts. The last value in the tuple is the results
        """
        logger.info(f"[Searching] Searching for '{text}'")

        def query():
            try:
                if mode == "fast":
                    if type_ == 'url':
                        result = YouTube(url=text, use_oauth=self.use_auth, allow_oauth_cache=self.allow_auth_cache).streams.filter(
                            only_audio=only_audio, only_video=video_only)
                        result = self.query_streams(result)

                        if result:
                            self.cache[value] = [result, 'Single', "streams"]

                        return 'Single', "streams", result
                    else:
                        result, req = self.fast_api_search(value)
                        if result:
                            self.cache[text] = [result, 'multi', "list_dict"]

                        return "Multi", "list_dict", result
                else:
                    if type_ == "url":
                        result = YouTube(url=text, use_oauth=self.use_auth, allow_oauth_cache=self.allow_auth_cache).streams.filter(
                            only_audio=only_audio, only_video=video_only)
                        result = self.query_streams(result)
                        if result:
                            self.cache[value] = [result, 'Single', "streams"]
                        return 'Single', "streams", result
                    else:
                        result = self.normal_api_search(value)

                        if result:
                            self.cache[text] = [result, 'multi', "list"]
                        return "Multi", "list", result

            except Exception as e:
                return None, "Error", e

        if not search_one:
            type_, value = self.url_build(text)
            if value in self.cache:
                logger.info("[Cache] Reload from cache")
                res, mode, type_ = self.cache.get(value)
                if res:
                    return mode, type_, res
                else:
                    # if cache had no data
                    return query()
            else:
                return query()
        else:
            # search for only one
            type_, url = self.url_build(text)
            if type_ == "text":
                res, vid_req_object = self.fast_api_search(url)
                return "Single", "dict", res[0]

            else:
                res = self.normal_api_search(url)
                return "Single", "stream", res

    @staticmethod
    def url_build(text):
        """
        Build the url
        :param text
        :rtype: tuple

        """
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
        """
        Lightweight Search
        :param build_url
        :rtype: tuple
        :return
            Tuple (list, youtubesearchpython.VideoSearch). List contains dicts of results. The VideoSearch object can
            be used to probe for more results
        """
        logger.info("[Search] Using fast api search")
        req = VideosSearch(build_url)
        results = req.result()
        results = self.parse_fast_results(results['result'])

        return results, req

    @staticmethod
    def parse_fast_results(results_):
        """
        Format the results from the lightweight search
        """
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
                description = ""
                for idx in results['descriptionSnippet']:
                    description += results['descriptionSnippet'][idx].get('text')
                    description += "\n"

                search_result['description'] = description
            except KeyError:
                search_result['description'] = "Description is unreachable"
            except Exception as e:
                search_result['description'] = "Description is unreachable"

            search_result['thumbnail'] = results['thumbnails'][0]['url']
            search_result['views'] = results['viewCount']['short']
            search_result['channel'] = results['channel']['name']
            search_result['channel-image'] = results['thumbnails'][0]['url']
            items.append(search_result)
        logger.info("[Parser] Done")
        return items

    @staticmethod
    def parse_normal_api_results(results):
        """
        Parse the results to a dict for easy accessibility
        """

    @staticmethod
    def normal_api_search(build_url):
        """
        Slow and all in one search containing direct download links with streams objects
        :param build_url
        :return:
            list of `pytubefix.YouTube` objects

        """
        logger.info("[Search] Using slow, exclusive")
        yt = Search(build_url)
        return yt.results

    def query_streams(self, streams):
        video_stream_progressive = streams.filter(progressive=True)
        audio_streams = streams.filter(only_audio=True)

        return video_stream_progressive.fmt_streams + audio_streams.fmt_streams
