import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os

from src.core.utils.utils import (
    is_valid_youtube_link, is_connected,
    strip_cdn_url, format_string,
    sanitize_filename, get_web_file_size,
    merge_dict, rgb_to_hex,
    save_download_data, load_download_data
)


class TestYouTubeLinkValidation(unittest.TestCase):
    """Test YouTube link validation scenarios"""
    
    def test_valid_youtube_urls(self):
        """Test various valid YouTube URL formats"""
        valid_urls = [
            "https://www.youtube.com/watch?v=rChLaLZd3Mo",
            "https://youtu.be/rChLaLZd3Mo",
            "http://www.youtube.com/watch?v=rChLaLZd3Mo",
            "https://www.youtube.com/embed/rChLaLZd3Mo",
            "www.youtube.com/watch?v=rChLaLZd3Mo"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(is_valid_youtube_link(url))

    def test_invalid_youtube_urls(self):
        """Test various invalid YouTube URL formats"""
        invalid_urls = [
            "https://www.example.com/watch?v=rChLaLZd3Mo",
            "https://www.youtube.com/watch=ei39ejie3",
            "https://vimeo.com/123456",
            "not a url",
            ""
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(is_valid_youtube_link(url))


class TestNetworkConnectivity(unittest.TestCase):
    """Test internet connectivity checks"""
    
    @patch('src.core.utils.utils.requests.get')
    def test_is_connected_success(self, mock_get):
        """Test successful internet connection"""
        mock_get.return_value = MagicMock()
        
        result = is_connected(max_retry=1)
        
        self.assertTrue(result)
        mock_get.assert_called_once_with("https://google.com", timeout=1)

    @patch('src.core.utils.utils.requests.get')
    def test_is_connected_failure(self, mock_get):
        """Test failed internet connection"""
        mock_get.side_effect = Exception("Network error")
        
        result = is_connected(max_retry=1)
        
        self.assertFalse(result)
        mock_get.assert_called_once_with("https://google.com", timeout=1)


class TestCDNUrlStripping(unittest.TestCase):
    """Test CDN URL stripping functionality"""
    
    def test_strip_wordpress_cdn_url(self):
        """Test WordPress CDN URL stripping"""
        cdn_url = "https://i0.wp.com/justnaija.com/uploads/2025/09/image.jpg"
        expected = "https://justnaija.com/uploads/2025/09/image.jpg"
        
        result = strip_cdn_url(cdn_url)
        
        self.assertEqual(result, expected)

    def test_strip_non_cdn_url_returns_original(self):
        """Test that non-CDN URLs return unchanged"""
        original_url = "https://example.com/image.jpg"
        
        result = strip_cdn_url(original_url)
        
        self.assertEqual(result, original_url)


class TestStringFormatting(unittest.TestCase):
    """Test string formatting utilities"""
    
    def test_format_string_removes_special_chars(self):
        """Test special character removal"""
        test_cases = [
            ("file@name#123", "filename123"),
            ("hello-world", "helloworld"),
            ("test  spaces", "testspaces")
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = format_string(input_str)
                self.assertEqual(result, expected)

    def test_sanitize_filename_replaces_problematic_chars(self):
        """Test filename sanitization"""
        test_cases = [
            ("file/name", "filename"),
            ("path|to|file", "pathtofile"),
            ("file$name&test", "filenametest")
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = sanitize_filename(input_str)
                self.assertEqual(result, expected)


class TestWebFileSize(unittest.TestCase):
    """Test web file size retrieval"""
    
    @patch('src.core.utils.utils.requests.head')
    def test_get_web_file_size_success(self, mock_head):
        """Test successful file size retrieval"""
        mock_response = MagicMock()
        mock_response.headers = {"Content-Length": "1048576"}  # 1 MB in bytes
        mock_head.return_value = mock_response
        
        result = get_web_file_size("https://example.com/file.mp4", "MB")
        
        self.assertAlmostEqual(result, 1.0, places=2)

    @patch('src.core.utils.utils.requests.head')
    def test_get_web_file_size_failure_returns_zero(self, mock_head):
        """Test file size retrieval failure returns zero"""
        mock_head.side_effect = Exception("Network error")
        
        result = get_web_file_size("https://example.com/file.mp4")
        
        self.assertEqual(result, 0)


class TestDictionaryOperations(unittest.TestCase):
    """Test dictionary utility functions"""
    
    def test_merge_dict_updates_primary_dict(self):
        """Test dictionary merging functionality"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        
        result = merge_dict(dict1, dict2)
        
        self.assertEqual(dict1, {"a": 1, "b": 3, "c": 4})
        self.assertEqual(result, dict2)


class TestColorConversion(unittest.TestCase):
    """Test color format conversion"""
    
    def test_rgb_to_hex_conversion(self):
        """Test RGB to HEX color conversion"""
        test_cases = [
            ([0.0, 0.0, 0.0], "#000000"),      # Black
            ([1.0, 1.0, 1.0], "#FFFFFF"),      # White
            ([1.0, 0.0, 0.0], "#FF0000"),      # Red
            ([0.0, 1.0, 0.0], "#00FF00"),      # Green
            ([0.0, 0.0, 1.0], "#0000FF"),      # Blue
        ]
        
        for rgb, expected_hex in test_cases:
            with self.subTest(rgb=rgb, expected=expected_hex):
                result = rgb_to_hex(rgb)
                self.assertEqual(result, expected_hex)


class TestDownloadDataPersistence(unittest.TestCase):
    """Test download data save/load functionality"""
    
    @patch('src.core.utils.utils.get_app_home_directory')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_download_data(self, mock_file, mock_get_dir):
        """Test saving download data"""
        mock_get_dir.return_value = "/test/path"
        test_data = {"url": "test.com", "status": "completed"}
        
        save_download_data(test_data)
        
        mock_file.assert_called_with("/test/path/downloads.json", "w")
    
    @patch('src.core.utils.utils.get_app_home_directory')
    @patch('builtins.open', new_callable=mock_open, read_data='[{"test": "data"}]')
    def test_load_download_data_success(self, mock_file, mock_get_dir):
        """Test loading existing download data"""
        mock_get_dir.return_value = "/test/path"
        
        result = load_download_data()
        
        self.assertEqual(result, [{"test": "data"}])
        mock_file.assert_called_with("/test/path/downloads.json", "r")
    
    @patch('src.core.utils.utils.get_app_home_directory')
    @patch('builtins.open')
    def test_load_download_data_handles_json_decode_error(self, mock_file, mock_get_dir):
        """Test JSON decode error handling"""
        mock_get_dir.return_value = "/test/path"
        mock_file.side_effect = [
            mock_open(read_data='invalid json').return_value,
            mock_open().return_value
        ]
        
        result = load_download_data()
        
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()