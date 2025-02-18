import unittest
from unittest.mock import patch, MagicMock
from Models.YouTube.youtube_model import YouTubeModel


class TestYouTubeModel(unittest.TestCase):

    def setUp(self):
        self.model = YouTubeModel()

    def test_url_builder_non_valid_link(self):
        # For an invalid YouTube link, patch is_valid_youtube_link to return False.
        with patch('Models.YouTube.youtube_model.is_valid_youtube_link', return_value=False):
            result = self.model.url_build("https://www.youtube.com/watch=ei39ejie3")
            self.assertEqual(result, (None, "Invalid Video Link"))

    def test_url_builder_valid_link(self):
        # For a valid YouTube URL, patch is_valid_youtube_link to return True.
        valid_url = "https://www.youtube.com/watch?v=rChLaLZd3Mo"
        with patch('Models.YouTube.youtube_model.is_valid_youtube_link', return_value=True):
            result = self.model.url_build(valid_url)
            self.assertEqual(result, ('url', valid_url))

    def test_fast_api_search_valid_build_url(self):
        # Simulate a fast API search returning a dummy result.
        dummy_api_response = {
            'result': [{
                'link': 'dummy_link',
                'title': 'dummy_title',
                'publishedTime': 'dummy_time',
                'duration': 'dummy_duration',
                'descriptionSnippet': [{'text': 'dummy_description'}],
                'thumbnails': [{'url': 'dummy_thumbnail'}],
                'viewCount': {'short': 'dummy_views'},
                'channel': {'name': 'dummy_channel'}
            }]
        }
        # Create a dummy VideosSearch instance that returns our dummy API response.
        dummy_videosearch = MagicMock()
        dummy_videosearch.result.return_value = dummy_api_response

        with patch('Models.YouTube.youtube_model.is_connected', return_value=True), \
             patch('Models.YouTube.youtube_model.VideosSearch', return_value=dummy_videosearch):
            results, req = self.model.fast_api_search("dummy_search")
            # Check that fast_api_search returns a list (from parse_fast_results)
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['link'], 'dummy_link')
            # And that the VideosSearch instance is returned as the second item.
            self.assertEqual(req, dummy_videosearch)

    def test_fast_api_search_invalid_build_url(self):
        # If there is no connection, is_connected returns False, so fast_api_search should return None.
        with patch('Models.YouTube.youtube_model.is_connected', return_value=False):
            result = self.model.fast_api_search("dummy_search")
            self.assertIsNone(result)

    def test_results_query_mode_fast_with_audio_only_as_true(self):
        # Test the branch when a valid URL is provided (thus type_ == 'url') in fast mode.
        dummy_streams = ['dummy_stream']
        # Create a dummy YouTube instance whose .streams.filter() returns our dummy stream immediately.
        dummy_youtube_instance = MagicMock()
        dummy_youtube_instance.streams.filter.return_value = dummy_streams

        valid_url = "https://www.youtube.com/watch?v=valid"
        with patch('Models.YouTube.youtube_model.is_valid_youtube_link', return_value=True), \
             patch('Models.YouTube.youtube_model.YouTube', return_value=dummy_youtube_instance):
            mode, type_str, res = self.model.results_query(valid_url, mode="fast", only_audio=True)
            self.assertEqual(mode, 'Single')
            self.assertEqual(type_str, "stream")
            self.assertEqual(res, dummy_streams)
            # Also verify that the result is cached.
            self.assertIn(valid_url, self.model.cache)

    def test_results_query_mode_fast_with_both_audio_only_video_only_as_true(self):
        # Test results_query when both only_audio and video_only are provided.
        dummy_streams = ['dummy_stream']
        dummy_youtube_instance = MagicMock()
        dummy_youtube_instance.streams.filter.return_value = dummy_streams

        valid_url = "https://www.youtube.com/watch?v=valid"
        with patch('Models.YouTube.youtube_model.is_valid_youtube_link', return_value=True), \
             patch('Models.YouTube.youtube_model.YouTube', return_value=dummy_youtube_instance):
            mode, type_str, res = self.model.results_query(valid_url, mode="fast", only_audio=True, video_only=True)
            self.assertEqual(mode, 'Single')
            # Depending on your implementation, type_str might be "stream" or "streams"
            # Here we check for one of the expected values.
            self.assertIn(type_str, ["stream", "streams"])
            self.assertEqual(res, dummy_streams)

    def test_results_query_mode_fast_with_both_audio_only_video_only_as_true_search_one_true(self):
        # Test the search_one branch.
        # In this branch, if url_build returns type 'text', the method calls fast_api_search
        # and returns the first element of the resulting list.
        dummy_result = [{'link': 'dummy_link', 'title': 'dummy_title'}]
        # Patch fast_api_search to return a tuple (dummy_result, dummy_object)
        with patch.object(YouTubeModel, 'fast_api_search', return_value=(dummy_result, MagicMock())):
            # Also patch url_build so that text is treated as a text search (non-URL)
            with patch.object(YouTubeModel, 'url_build', return_value=('text', 'dummy search text')):
                result = self.model.results_query("dummy search text", mode="fast", search_one=True)
                self.assertEqual(result, dummy_result[0])

    def test_results_query_mode_fast_with_audio_only_search_as_true(self):
        # Another test for the search_one branch with a non-URL text.
        dummy_result = [{'link': 'dummy_link', 'title': 'dummy_title'}]
        with patch.object(YouTubeModel, 'fast_api_search', return_value=(dummy_result, MagicMock())):
            # Without patching url_build here, a text without "https" will yield ('text', text)
            result = self.model.results_query("dummy search text", mode="fast", search_one=True)
            self.assertEqual(result, dummy_result[0])

if __name__ == '__main__':
    unittest.main()
