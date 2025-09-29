import unittest
from unittest.mock import patch, MagicMock, Mock
import random
from bs4 import BeautifulSoup

from src.models.Billboard.billboardmodel import BillBoardManagerModel


class TestBillBoardModel(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.model = BillBoardManagerModel()
        self.mock_html_content = """
        <div class="o-chart-results-list-row-container">
            <div class="c-lazy-image">
                <img data-lazy-src="https://example.com/image1.jpg"/>
            </div>
            <li class="lrv-u-width-100p">
                <h3 id="title-of-a-story">Song Title 1</h3>
                <span>Artist 1</span>
            </li>
        </div>
        <div class="o-chart-results-list-row-container">
            <div class="c-lazy-image">
                <img data-lazy-src="https://example.com/image2.jpg"/>
            </div>
            <li class="lrv-u-width-100p">
                <h3 id="title-of-a-story">Song Title 2</h3>
                <span>Artist 2</span>
            </li>
        </div>
        """

    def test_initialization(self):
        """Test model initializes with correct default values."""
        self.assertEqual(self.model.url, "https://www.billboard.com/charts/hot-100/")
        self.assertEqual(self.model.current_results, {})
        self.assertEqual(self.model.current_results_artists, {})
        self.assertIsNotNone(self.model.session_manager)

    def test_configurator_sets_correct_values(self):
        """Test configurator properly sets BillboardConfig values."""
        config = self.model.configurator(
            song_list_size=10, 
            audio_only=False, 
            verbose=False
        )
        
        self.assertEqual(config.song_list_size, 10)
        self.assertEqual(config.audio_only, False)
        self.assertEqual(config.verbosity, False)

    @patch('src.models.Billboard.billboardmodel.connection')
    @patch('src.models.Billboard.billboardmodel.SessionManager')
    def test_top_songs_success(self, mock_session_manager, mock_connection):
        """Test successful retrieval of top songs."""
        # Mock dependencies
        mock_connection.return_value = True
        mock_session = MagicMock()
        mock_session_manager.return_value.create_new_session.return_value = mock_session
        mock_session.get.return_value.text = self.mock_html_content

        # Execute
        result = self.model.top_songs(size=2)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertIn("Song Title 1", result)
        self.assertEqual(result["Song Title 1"][0], "Artist 1")
        self.assertEqual(result["Song Title 1"][1], "https://example.com/image1.jpg")

    @patch('src.models.Billboard.billboardmodel.connection')
    def test_top_songs_no_connection(self, mock_connection):
        """Test top_songs handles no internet connection gracefully."""
        mock_connection.return_value = False

        result = self.model.top_songs()

        self.assertEqual(result, {})
        self.assertEqual(self.model.current_results, {})

    @patch('src.models.Billboard.billboardmodel.connection')
    @patch('src.models.Billboard.billboardmodel.SessionManager')
    def test_top_songs_with_size_limit(self, mock_session_manager, mock_connection):
        """Test top_songs respects size parameter."""
        mock_connection.return_value = True
        mock_session = MagicMock()
        mock_session_manager.return_value.create_new_session.return_value = mock_session
        mock_session.get.return_value.text = self.mock_html_content

        result = self.model.top_songs(size=1)

        self.assertEqual(len(result), 1)
        self.assertIn("Song Title 1", result)

    @patch('src.models.Billboard.billboardmodel.connection')
    @patch('src.models.Billboard.billboardmodel.SessionManager')
    @patch.object(BillBoardManagerModel, 'get_artist_biography_wikipedia')
    @patch.object(BillBoardManagerModel, 'get_artist_image')
    def test_top_artists_success(self, mock_get_image, mock_get_bio, mock_session_manager, mock_connection):
        """Test successful retrieval of top artists."""
        # Mock dependencies
        mock_connection.return_value = True
        mock_session = MagicMock()
        mock_session_manager.return_value.create_new_session.return_value = mock_session
        
        # Mock HTML content for artists
        artists_html = """
        <div class="o-chart-results-list-row-container">
            <li class="lrv-u-width-100p">
                <h3>Artist Name</h3>
            </li>
        </div>
        """
        mock_session.get.return_value.text = artists_html
        mock_get_bio.return_value = "Mock biography"
        mock_get_image.return_value = "https://example.com/artist.jpg"

        # Execute
        result = self.model.top_artists(size=1, fetch_image=True)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertIn("Artist Name", result)
        self.assertEqual(result["Artist Name"][0], "https://example.com/artist.jpg")
        self.assertEqual(result["Artist Name"][1], "Mock biography")

    @patch('src.models.Billboard.billboardmodel.connection')
    def test_top_artists_no_connection(self, mock_connection):
        """Test top_artists raises ConnectionError when no internet."""
        mock_connection.return_value = False

        with self.assertRaises(ConnectionError):
            self.model.top_artists(size=1)

    @patch('src.models.Billboard.billboardmodel.wikipedia.summary')
    def test_get_artist_biography_wikipedia_success(self, mock_wikipedia_summary):
        """Test successful biography retrieval from Wikipedia."""
        mock_wikipedia_summary.return_value = "This is a test biography."

        result = self.model.get_artist_biography_wikipedia("Taylor Swift")

        self.assertEqual(result, "This is a test biography")
        mock_wikipedia_summary.assert_called_once_with("Taylor Swift")

    @patch('src.models.Billboard.billboardmodel.wikipedia.summary')
    def test_get_artist_biography_wikipedia_failure(self, mock_wikipedia_summary):
        """Test biography retrieval handles Wikipedia exceptions."""
        mock_wikipedia_summary.side_effect = Exception("Wikipedia error")

        result = self.model.get_artist_biography_wikipedia("Unknown Artist")

        self.assertEqual(result, "Could not fetch Unknown Artist's biography")

    @patch('src.models.Billboard.billboardmodel.SessionManager')
    def test_get_artist_image_success(self, mock_session_manager):
        """Test successful artist image retrieval."""
        # Mock session and response
        mock_session = MagicMock()
        mock_session_manager.return_value.create_new_session.return_value = mock_session
        
        # Mock HTML with images
        images_html = """
        <li class="image-list-item-wrapper">
            <img src="https://example.com/artist1.jpg"/>
        </li>
        <li class="image-list-item-wrapper">
            <img src="https://example.com/artist2.jpg"/>
        </li>
        """
        mock_session.get.return_value.text = images_html

        # Mock random.choice to return first element
        with patch('random.choice', side_effect=lambda x: x[0]):
            result = self.model.get_artist_image("Ed Sheeran")

        self.assertEqual(result, "https://example.com/artist1.jpg")

    @patch('src.models.Billboard.billboardmodel.SessionManager')
    def test_get_artist_image_no_images_found(self, mock_session_manager):
        """Test artist image retrieval when no images are found."""
        mock_session = MagicMock()
        mock_session_manager.return_value.create_new_session.return_value = mock_session
        mock_session.get.return_value.text = "<html></html>"  # No images

        result = self.model.get_artist_image("Unknown Artist")

        self.assertEqual(result, "")

    def test_pick_artists_selection(self):
        """Test artist picking selects correct number of artists."""
        test_artists = {
            "Artist1": ["img1", "bio1"],
            "Artist2": ["img2", "bio2"],
            "Artist3": ["img3", "bio3"],
            "Artist4": ["img4", "bio4"],
            "Artist5": ["img5", "bio5"],
        }

        # Mock random.choice to select first 2 artists
        with patch('random.choice', side_effect=["Artist1", "Artist2"]):
            result = self.model._BillBoardManagerModel__pick_artists(test_artists)

        self.assertEqual(len(result), 2)
        self.assertIn("Artist1", result)
        self.assertIn("Artist2", result)

    @patch('src.models.Billboard.billboardmodel.connection')
    @patch('src.models.Billboard.billboardmodel.SessionManager')
    def test_get_top_americas_success(self, mock_session_manager, mock_connection):
        """Test successful retrieval of top Americas songs."""
        mock_connection.return_value = True
        mock_session = MagicMock()
        mock_session_manager.return_value.create_new_session.return_value = mock_session
        
        # Mock HTML content for Americas chart
        americas_html = """
        <figure class="component-chartlist-item-with-counter">
            <a class="track-title">Song 1</a>
            <a class="track-artist">Artist 1</a>
        </figure>
        <figure class="component-chartlist-item-with-counter">
            <a class="track-title">Song 2</a>
            <a class="track-artist">Artist 2</a>
        </figure>
        """
        mock_session.get.return_value.text = americas_html

        result = self.model.get_top_americas()

        self.assertEqual(len(result), 2)
        self.assertEqual(result["Song 1"], "Artist 1")
        self.assertEqual(result["Song 2"], "Artist 2")

    @patch('src.models.Billboard.billboardmodel.connection')
    def test_get_top_americas_no_connection(self, mock_connection):
        """Test get_top_americas raises ConnectionError when no internet."""
        mock_connection.return_value = False

        with self.assertRaises(ConnectionError):
            self.model.get_top_americas()

    @patch('src.models.Billboard.billboardmodel.connection')
    @patch('src.models.Billboard.billboardmodel.SessionManager')
    def test_top_artists_for_pick(self, mock_session_manager, mock_connection):
        """Test top_artists with for_pick parameter returns limited selection."""
        mock_connection.return_value = True
        mock_session = MagicMock()
        mock_session_manager.return_value.create_new_session.return_value = mock_session
        
        # Create multiple artists in HTML
        artists_html = "".join([
            f'<div class="o-chart-results-list-row-container"><li class="lrv-u-width-100p"><h3>Artist {i}</h3></li></div>'
            for i in range(15)
        ])
        mock_session.get.return_value.text = artists_html

        # Mock the biography and image methods
        with patch.object(self.model, 'get_artist_biography_wikipedia') as mock_bio, \
             patch.object(self.model, 'get_artist_image') as mock_image:
            mock_bio.return_value = "Bio"
            mock_image.return_value = "image.jpg"

            result = self.model.top_artists(for_pick=True)

        # Should return exactly 10 artists when for_pick=True
        self.assertEqual(len(result), 10)

    def test_url_constants(self):
        """Test that all URL constants are properly defined."""
        expected_urls = [
            'artists_url', 'italy', 'uk', 'brazil', 'france', 
            'india', 'safrica', 'all_200', 'america', 'spain'
        ]
        
        for url_attr in expected_urls:
            self.assertTrue(hasattr(self.model, url_attr))
            url_value = getattr(self.model, url_attr)
            self.assertIsInstance(url_value, str)
            self.assertTrue(url_value.startswith('http'))


if __name__ == '__main__':
    unittest.main()