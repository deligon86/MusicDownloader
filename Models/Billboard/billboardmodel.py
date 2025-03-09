import random
import wikipedia
from random import choice
from bs4 import BeautifulSoup as Soup
from Core.base import BillboardConfig
from Core.base import connection, Logger, SessionManager


class BillBoardManagerModel:

    artists_url = "https://www.billboard.com/charts/artist-100/"
    italy = "https://www.billboard.com/charts/billboard-italy-albums-top-100/"
    uk = "https://www.billboard.com/charts/official-uk-songs/"
    brazil = "https://www.billboard.com/charts/billboard-brasil-hot-100/"
    france = "https://www.billboard.com/charts/france-songs-hotw/"
    india = "https://www.billboard.com/charts/india-songs-hotw/"
    safrica = "https://www.billboard.com/charts/south-africa-songs-hotw/"
    all_200 = "https://www.billboard.com/charts/billboard-global-200/"
    america = "https://www.americantop40.com/charts/top-40-238/latest/"
    spain = "https://www.billboard.com/charts/latin-songs/"

    def __init__(self,):
        self.current_results_artists = {}
        self.verbose = True
        self.session_manager = SessionManager()

        self.url = "https://www.billboard.com/charts/hot-100/"
        self.current_results = {}
        self.logger = Logger()

        self.session = self.session_manager.create_new_session('Billboard')
        self.configurator(song_list_size=5)


    def configurator(self, song_list_size=5, audio_only=True, verbose=True):
        """
        :param song_list_size:
        :param audio_only:
        :param verbose:
        :return:  Billboard Config class
        """
        BillboardConfig.song_list_size = song_list_size
        BillboardConfig.audio_only = audio_only
        BillboardConfig.verbosity = verbose

        return BillboardConfig

    def top_songs(self, url="https://www.billboard.com/charts/hot-100/", size=None, use_default_size=False):
        found = {}
        if connection():
            self.logger.info("[BillBoardConnection] Starting connection")
            page = self.session.get(url)
            sp = Soup(page.text, 'html.parser')
            items = sp.find_all("div", attrs={"class": "o-chart-results-list-row-container"})
            counter = 0
            self.logger.info("[BillBoardFetcher] Fetched Items...")

            if use_default_size:
                size = BillboardConfig.song_list_size
            else:
                if size:
                    size = size
                else:
                    size = None

            for item in items:
                if size:
                    if counter == size:
                        break
                image_tag = item.find(
                    'div', attrs={'class': 'c-lazy-image'}
                    )
                # print(image_tag)
                image_tag = image_tag.find_next("img")
                self.logger.highlight(f"[BillBardImage Tag] {image_tag.get('data-lazy-src')}")
                item_ = item.find("li", attrs={"class": "lrv-u-width-100p"})
                song = item_.find("h3", attrs={"id": "title-of-a-story"})
                artist = item_.find("span")
                self.logger.info(f"[Item]{counter + 1} {song.text.strip()} --by-- {artist.text.strip()}")
                found[song.text.strip()] = [artist.text.strip(), image_tag.get('data-lazy-src')]

                counter += 1
        else:
            raise ConnectionError("No internet connection")
        self.current_results = found

        return found

    def top_artists(self, size=15, for_pick=False, use_default_size=False, fetch_image=True):
        """
        Get the top artists\n
        set number of items to fetch on size or fetch all if no size is given and no use_default_size is given
        :return: Dict[artist] = [image, bio]
        """

        limit = None

        if size is not None:
            limit = size
        else:
            if use_default_size:
                limit = BillboardConfig.artist_list_size

        self.logger.info(f"[BillBoardConfig] Setting Fetch Limit to: {limit}")

        found = {}
        if connection():
            session = self.session_manager.create_new_session("recom artist")
            self.logger.info("[BillBoardConnection] Starting connection")
            page = session.get(self.artists_url)
            sp = Soup(page.text, 'html.parser')
            items = sp.find_all("div", attrs={"class": "o-chart-results-list-row-container"})
            counter = 0
            bio = "No bio"
            image = ""
            self.logger.info("[BillBoardFetcher] Fetched Items...")
            for item in items:
                if limit:
                    if counter == limit:
                        break
                item_ = item.find("li", attrs={"class": "lrv-u-width-100p"})
                artist = item_.find("h3").text.strip()
                bio = self.get_artist_biography_wikipedia(artist)
                if fetch_image:
                    image = self.get_artist_image(artist)
                found[artist] = [image, bio]
                self.logger.info(f"[BillBoardResult] {artist}")
                counter += 1
        else:
            raise ConnectionError("No internet connection")
        self.current_results_artists = found
        # discard session
        self.session_manager.delete_session("recom artist")

        if for_pick:
            return self.__pick_artists(found)
        else:
            return found

    @staticmethod
    def __pick_artists(found):
        picked = {}
        while True:
            if len(picked) == 10:
                break

            select = choice(list(found.keys()))
            if select not in list(picked.keys()):
                picked[select] = found[select]

        return picked

    def get_artist_biography_wikipedia(self, artist):
        bio =""
        try:
            bio = wikipedia.summary(artist)
            self.logger.info(f"Fetched artist '{artist}' bio")
        except Exception as e:
            bio =  f"Could not fetch {artist}'s biography"
            self.logger.warning(f"[BillBoardBiography] {bio} with exception: {e}")

        return bio

    def get_artist_image(self, artist):
        url = "https://www.last.fm/music/{}/+images"
        art = artist.split(" ")
        art = [r.capitalize() for r in art]
        artist = "+".join(art)
        img = ""

        req = self.session_manager.create_new_session("last fm")
        req = req.get(url.format(artist))
        sp = Soup(req.text, "html.parser")
        items = sp.find_all("li", attrs={"class": "image-list-item-wrapper"})
        if items:
            item = random.choice(items)
            img = item.find("img").get("src")

        # discard session
        self.session_manager.delete_session("last fm")

        return img

    def get_top_americas(self):
        session = self.session_manager.create_new_session("top americas", discard_old=True)
        found = {}
        if connection():
            req = session.get(self.america)
            sp = Soup(req.text, 'html.parser')
            items = sp.find_all("figure", attrs={'class': 'component-chartlist-item-with-counter'})
            for item in items:
                title = item.find_next("a", attrs={'class': 'track-title'}).text.strip()
                artist = item.find_next("a", attrs={'class': 'track-artist'}).text.strip()

                found[title] = artist
        else:
            raise ConnectionError("No internet connection")

        return found
