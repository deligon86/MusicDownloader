import random
import wikipedia
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from src.core import logger
from src.core.base import BillboardConfig, connection, SessionManager


class BillBoardManagerModel:
    """
    Manager for fetching and processing Billboard chart data.
    Handles multiple international charts and artist information.
    """

    # Chart URL constants
    CHARTS = {
        'artists': "https://www.billboard.com/charts/artist-100/",
        'italy': "https://www.billboard.com/charts/billboard-italy-albums-top-100/",
        'uk': "https://www.billboard.com/charts/official-uk-songs/",
        'brazil': "https://www.billboard.com/charts/billboard-brasil-hot-100/",
        'france': "https://www.billboard.com/charts/france-songs-hotw/",
        'india': "https://www.billboard.com/charts/india-songs-hotw/",
        'safrica': "https://www.billboard.com/charts/south-africa-songs-hotw/",
        'global': "https://www.billboard.com/charts/billboard-global-200/",
        'america': "https://www.americantop40.com/charts/top-40-238/latest/",
        'spain': "https://www.billboard.com/charts/latin-songs/",
        'hot_100': "https://www.billboard.com/charts/hot-100/"
    }

    def __init__(self):
        """Initialize the Billboard manager with session and configuration."""
        self.current_results_artists: Dict[str, List[str]] = {}
        self.current_results: Dict[str, List[str]] = {}
        self.session_manager = SessionManager()
        self.session = self.session_manager.create_new_session('Billboard')
        self.url = self.CHARTS['hot_100']
        
        # Set default configuration
        self.configurator(song_list_size=20)

    def configurator(self, song_list_size: int = 5, audio_only: bool = True, 
                    verbose: bool = True) -> type[BillboardConfig]:
        """
        Configure Billboard settings.

        Args:
            song_list_size: Number of songs to fetch by default
            audio_only: Whether to fetch audio-only content
            verbose: Enable verbose logging

        Returns:
            BillboardConfig: Updated configuration object
        """
        BillboardConfig.song_list_size = song_list_size
        BillboardConfig.audio_only = audio_only
        BillboardConfig.verbosity = verbose

        return BillboardConfig

    def top_songs(self, url: Optional[str] = None, size: Optional[int] = None, 
                 use_default_size: bool = False) -> Dict[str, List[str]]:
        """
        Fetch top songs from Billboard charts.

        Args:
            url: Chart URL to fetch from (defaults to hot_100)
            size: Number of songs to fetch
            use_default_size: Use configured default size

        Returns:
            Dictionary of songs in format {title: [artist, image_url]}
        """
        if not connection():
            logger.warning("No internet connection available")
            return {}

        target_url = url or self.url
        fetch_limit = self._get_fetch_limit(size, use_default_size)

        logger.info(f"[BillBoard] Fetching top {fetch_limit} songs from {target_url}")
        
        try:
            page = self.session.get(target_url)
            page.raise_for_status()
            
            soup = BeautifulSoup(page.text, 'html.parser')
            song_items = self._extract_song_items(soup, fetch_limit)
            
            self.current_results = song_items
            return song_items

        except Exception as e:
            logger.error(f"[BillBoard] Failed to fetch songs: {e}")
            return {}

    def top_artists(self, size: Optional[int] = 15, for_pick: bool = False, 
                   use_default_size: bool = False, fetch_image: bool = True) -> Dict[str, List[str]]:
        """
        Fetch top artists from Billboard charts.

        Args:
            size: Number of artists to fetch
            for_pick: Return a random selection of 10 artists
            use_default_size: Use configured default size
            fetch_image: Whether to fetch artist images

        Returns:
            Dictionary of artists in format {artist: [image_url, biography]}
        """
        if not connection():
            raise ConnectionError("No internet connection available")

        fetch_limit = self._get_fetch_limit(size, use_default_size, default_artist_size=size)
        logger.info(f"[BillBoard] Fetching top {fetch_limit} artists")

        try:
            session = self.session_manager.create_new_session("artist_fetch")
            page = session.get(self.CHARTS['artists'])
            page.raise_for_status()

            soup = BeautifulSoup(page.text, 'html.parser')
            artists = self._extract_artist_items(soup, fetch_limit, fetch_image)
            
            self.current_results_artists = artists
            self.session_manager.delete_session("artist_fetch")

            return self._pick_artists(artists) if for_pick else artists

        except Exception as e:
            logger.error(f"[BillBoard] Failed to fetch artists: {e}")
            self.session_manager.delete_session("artist_fetch")
            return {}

    @staticmethod
    def _pick_artists(artists_data: Dict[str, List[str]], pick_count: int = 10) -> Dict[str, List[str]]:
        """
        Randomly select artists from the available data.

        Args:
            artists_data: Dictionary of artist data
            pick_count: Number of artists to select

        Returns:
            Dictionary containing randomly selected artists
        """
        if len(artists_data) <= pick_count:
            return artists_data.copy()

        selected_artists = {}
        available_artists = list(artists_data.keys())
        
        while len(selected_artists) < pick_count and available_artists:
            artist = random.choice(available_artists)
            available_artists.remove(artist)
            selected_artists[artist] = artists_data[artist]

        return selected_artists

    @staticmethod
    def get_artist_biography_wikipedia(artist: str) -> str:
        """
        Fetch artist biography from Wikipedia.

        Args:
            artist: Artist name to search for

        Returns:
            Biography text or error message
        """
        try:
            biography = wikipedia.summary(artist, sentences=3)  # Limit length
            logger.info(f"Fetched biography for '{artist}'")
            return biography
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"Wikipedia disambiguation for '{artist}': {e}")
            return f"Multiple matches found for {artist}"
        except wikipedia.exceptions.PageError:
            logger.warning(f"No Wikipedia page found for '{artist}'")
            return f"No biography available for {artist}"
        except Exception as e:
            logger.warning(f"Failed to fetch biography for '{artist}': {e}")
            return f"Could not fetch {artist}'s biography"

    def get_artist_image(self, artist: str) -> str:
        """
        Fetch artist image from Last.fm.

        Args:
            artist: Artist name to search for

        Returns:
            URL of artist image or empty string if not found
        """
        try:
            # Format artist name for URL
            formatted_artist = "+".join(part.capitalize() for part in artist.split())
            url = f"https://www.last.fm/music/{formatted_artist}/+images"

            session = self.session_manager.create_new_session("last_fm")
            response = session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            image_items = soup.find_all("li", class_="image-list-item-wrapper")
            
            self.session_manager.delete_session("last_fm")

            if image_items:
                random_image = random.choice(image_items)
                return random_image.find("img").get("src", "")

        except Exception as e:
            logger.warning(f"Failed to fetch image for '{artist}': {e}")
            self.session_manager.delete_session("last_fm")

        return ""

    def get_top_americas(self) -> Dict[str, str]:
        """
        Fetch top songs from American charts.

        Returns:
            Dictionary of songs in format {title: artist}
        """
        if not connection():
            raise ConnectionError("No internet connection available")

        try:
            session = self.session_manager.create_new_session("americas_chart", discard_old=True)
            response = session.get(self.CHARTS['america'])
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_americas_chart(soup)

        except Exception as e:
            logger.error(f"[BillBoard] Failed to fetch Americas chart: {e}")
            return {}

    def _get_fetch_limit(self, size: Optional[int], use_default_size: bool, 
                        default_artist_size: Optional[int] = None) -> Optional[int]:
        """Determine the fetch limit based on parameters."""
        if use_default_size:
            return BillboardConfig.song_list_size
        return size or default_artist_size

    def _extract_song_items(self, soup: BeautifulSoup, limit: Optional[int]) -> Dict[str, List[str]]:
        """Extract song information from BeautifulSoup object."""
        songs = {}
        items = soup.find_all("div", class_="o-chart-results-list-row-container")

        for idx, item in enumerate(items):
            if limit and idx >= limit:
                break

            try:
                title, artist, image_url = self._parse_song_item(item)
                if title and artist:
                    songs[title] = [artist, image_url]
                    logger.info(f"Song {idx + 1}: {title} -- {artist}")

            except Exception as e:
                logger.warning(f"Failed to parse song item {idx}: {e}")
                continue

        return songs

    def _parse_song_item(self, item) -> Tuple[str, str, str]:
        """Parse individual song item for title, artist, and image."""
        image_tag = item.find('div', class_='c-lazy-image').find('img')
        image_url = image_tag.get('data-lazy-src', '') if image_tag else ''

        content_item = item.find("li", class_="lrv-u-width-100p")
        title_element = content_item.find("h3", id="title-of-a-story")
        artist_element = content_item.find("span")

        title = title_element.text.strip() if title_element else ""
        artist = artist_element.text.strip() if artist_element else ""

        return title, artist, image_url

    def _extract_artist_items(self, soup: BeautifulSoup, limit: Optional[int], 
                             fetch_image: bool) -> Dict[str, List[str]]:
        """Extract artist information from BeautifulSoup object."""
        artists = {}
        items = soup.find_all("div", class_="o-chart-results-list-row-container")

        for idx, item in enumerate(items):
            if limit and idx >= limit:
                break

            try:
                artist_name = self._parse_artist_item(item)
                if artist_name:
                    biography = self.get_artist_biography_wikipedia(artist_name)
                    image_url = self.get_artist_image(artist_name) if fetch_image else ""
                    
                    artists[artist_name] = [image_url, biography]
                    logger.info(f"Artist {idx + 1}: {artist_name}")

            except Exception as e:
                logger.warning(f"Failed to parse artist item {idx}: {e}")
                continue

        return artists

    def _parse_artist_item(self, item) -> str:
        """Parse individual artist item for name."""
        content_item = item.find("li", class_="lrv-u-width-100p")
        artist_element = content_item.find("h3") if content_item else None
        
        return artist_element.text.strip() if artist_element else ""

    def _parse_americas_chart(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Parse Americas chart page for song titles and artists."""
        songs = {}
        items = soup.find_all("figure", class_="component-chartlist-item-with-counter")

        for item in items:
            try:
                title_element = item.find("a", class_="track-title")
                artist_element = item.find("a", class_="track-artist")

                if title_element and artist_element:
                    title = title_element.text.strip()
                    artist = artist_element.text.strip()
                    songs[title] = artist

            except Exception as e:
                logger.warning(f"Failed to parse Americas chart item: {e}")
                continue

        return songs

    # Maintain backward compatibility for URL constants
    @property
    def artists_url(self):
        return self.CHARTS['artists']

    @property
    def italy(self):
        return self.CHARTS['italy']

    @property
    def uk(self):
        return self.CHARTS['uk']

    @property
    def brazil(self):
        return self.CHARTS['brazil']

    @property
    def france(self):
        return self.CHARTS['france']

    @property
    def india(self):
        return self.CHARTS['india']

    @property
    def safrica(self):
        return self.CHARTS['safrica']

    @property
    def all_200(self):
        return self.CHARTS['global']

    @property
    def america(self):
        return self.CHARTS['america']

    @property
    def spain(self):
        return self.CHARTS['spain']