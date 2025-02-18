import unittest
import re
from unittest.mock import patch, MagicMock

# Adjust the import paths to match your project structure.
from Core.utils.utils import is_valid_youtube_link, is_connected

class TestUtils(unittest.TestCase):
    # Tests for is_valid_youtube_link

    def test_is_valid_youtube_link_valid_url(self):
        """Test that a standard YouTube URL returns True."""
        valid_link = "https://www.youtube.com/watch?v=rChLaLZd3Mo"
        self.assertTrue(is_valid_youtube_link(valid_link))

    def test_is_valid_youtube_link_valid_youtu_be_url(self):
        """Test that a shortened YouTube URL returns True."""
        valid_link = "https://youtu.be/rChLaLZd3Mo"
        self.assertTrue(is_valid_youtube_link(valid_link))

    def test_is_valid_youtube_link_invalid_domain(self):
        """Test that a non-YouTube URL returns False."""
        invalid_link = "https://www.example.com/watch?v=rChLaLZd3Mo"
        self.assertFalse(is_valid_youtube_link(invalid_link))

    def test_is_valid_youtube_link_invalid_format(self):
        """Test that a badly formatted YouTube URL returns False."""
        invalid_link = "https://www.youtube.com/watch=ei39ejie3"
        self.assertFalse(is_valid_youtube_link(invalid_link))

    # Tests for is_connected

    @patch('Core.utils.utils.requests.get')
    def test_is_connected_success(self, mock_get):
        """
        Simulate a successful connection by having requests.get return a dummy response.
        Since is_connected uses max_retry as the timeout, we pass a small value for testing.
        """
        dummy_response = MagicMock()
        mock_get.return_value = dummy_response

        # Since is_connected is defined with a self parameter, pass None for self.
        self.assertTrue(is_connected(None, max_retry=1))
        mock_get.assert_called_once_with("https://google.com", timeout=1)

    @patch('Core.utils.utils.requests.get', side_effect=Exception("Network Error"))
    def test_is_connected_failure(self, mock_get):
        """
        Simulate a connection failure by having requests.get raise an Exception.
        """
        self.assertFalse(is_connected(None, max_retry=1))
        mock_get.assert_called_once_with("https://google.com", timeout=1)

if __name__ == '__main__':
    unittest.main()
