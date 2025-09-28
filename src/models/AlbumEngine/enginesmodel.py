import requests
from typing import Protocol
from bs4 import BeautifulSoup as Soup
from src.core import SessionManager, logger
from src.core.utils.utils import merge_dict, strip_cdn_url


class BaseEngine(Protocol):

    def search(self, query, mode) -> dict:
        ...


class HipHopKitEngineModel(BaseEngine):
    """
    Engine for probing artifacts at the site from music to albums
    """
    search_url = "https://justnaija.com/search?q={}&SearchIt="
    base_music_url = "https://justnaija.com/music/"
    base_foreign_url = "https://justnaija.com/music/foreign/"
    base_album_page_url = "https://justnaija.com/music/album/"
    next_page_url = "https://justnaija.com/music/album/page/{}/"
    next_page_foreign = "https://justnaija.com/music/foreign/page/{}/"
    next_page_music = "https://justnaija.com/music-mp3/page/{}/"
    albums = {}
    current_page = 1

    def __init__(self, max_page=40, navigate_all_pages=False, verbose=True):
        self.max_pages = max_page
        self.nav_all = navigate_all_pages
        self.verbose = verbose
        self.session_manager = SessionManager()
        self.session = self.session_manager.create_new_session("HipHopKit")
        self.available_pages = {}

    def search(self, query, mode="all"):
        """
        Search for content online

        :param query: The search keywords
        :param mode: The search mode, available modes are: songs, artists, foreign, all
        :rtype: dict
        :return:
            A dictionary of search results
        """
        all_results = {}
        if query:
            query = query.replace(" ", "+")
            url = self.search_url.format(query)  # build url
            logger.info(f"[HipHopKit Engine] Building query...")
            page = self.session.get(url)
            # only artists mode has a different page layout from the rest modes
            if mode == "artist":
                all_results = self.__probe_for_artists(page.text, query)
            else:
                all_results = self.parse_ordinal_page(page.text, mode.lower())

        return all_results

    def __set_max_pages(self, url, mode):
        """
        Get the maximum page to query
        :param url: The url to extract the pages for
        :return:
        """
        pages = 50
        mode = mode.lower()
        req = requests.get(url)
        sp = Soup(req.content, 'html.parser')
        pager = sp.find("div", attrs={"class": "pages"})
        if pager:
            page_info = pager.find("span", attrs={"class": "pages-info"})
            text = page_info.text
            text = text.strip("(").strip(")").strip()
            num_text = text.split(":")[-1]
            pages = int(num_text)

        self.available_pages[mode] = pages

    @staticmethod
    def parse_ordinal_page(page, mode="all"):
        """
        Just extract the search results items
        :param mode: Extraction mode `all|songs|albums`. defaults to `all`
        :param page:
        :return:
            Dictionary containing results in form of {'title': [link, image, description]}
        """
        found = {}
        sp = Soup(page, 'html.parser')
        logger.info(f"[HipHopKit Engine] Parsing page...")
        container = sp.find_all("article", attrs={"class": "result"})
        index = 0
        results = sp.find_all("div", attrs={"class": "result-info"})
        for result in results:
            link = result.find("a")
            desc = result.find("p", attrs={"class": "result-desc"})
            item = container[index]
            img = item.find("div", attrs={"class": "result-img"})
            im = img.findChild("img")
            if im:
                im = strip_cdn_url(im.get("src").split("?")[0])
            else:
                im = ''
            if link:
                link_ = link.get("href")
                if mode == "albums":
                    if "[Album]" not in link_:
                        continue
                elif mode == "songs":
                    if "[Album]" in link_:
                        continue
                logger.info(f"[HipHopKit Engine] Found link for: {link_}")
                found[link.text] = [link_, im, desc.text]
            index += 1
        logger.info(f"HipHopKit Engine: Building results ...")
        return found

    def parse_page(self, content):
        """
        For use in page navigation
        :param content: HTML page content
        :return: Dictionary in format `{title?artist: [link, image]}`
        """
        page_items = {}
        logger.info("[HipHopKitEngine] Parsing page...")
        sp = Soup(content.text, "html.parser")
        main = sp.find_all("article", attrs={"class": "a-file myfile"})
        container = sp.find_all("div", attrs={"class": "info infohome"})
        index = 0
        for item in container:
            cont = item.find("h3", attrs={"class": "file-name myhome"})
            link = ""
            artist_name = ""
            title = ""
            img = ""
            if cont:
                linker = cont.find("a")
                link = linker.get("href")
                title = cont.text
            span_tag = item.find("span", attrs={"class": "fa fa-certificate"})
            if span_tag:
                artist_tag = span_tag.find("a")
                if artist_tag:
                    artist_name = artist_tag.text
            else:
                artist_name = "Unknown"

            item_im = main[index]
            img_cont = item_im.find("div", attrs={"class": "image"})
            im = img_cont.find("img", attrs={"class": "lazy"})
            if im:
                img_ = im.get("data-src")
                if img_:
                    img = strip_cdn_url(img_.split("?")[0])

            page_items[f"{title}COL{artist_name}"] = [link, img]
            logger.info(f"HipHopKit Engine: {title} by {artist_name} {[link, img]}")

            index += 1

        return page_items

    def get_final_album_link(self, link):
        """
        Get the link to the remote file that is downloadable

        :param link:
        :rtype: dict
        :return: Dictionary containing `link`, `description`, `tags`
        """
        description = ""
        tags = ""
        download_link = ""
        page = self.session.get(link)
        sp = Soup(page.text, "html.parser")
        parent = sp.find("p", attrs={"class": "song-download"})
        d_link = parent.find("a")
        if d_link:
            logger.info("[Kit Engine] Found the download link")
            logger.info("[Kit Engine] Will download in a while")

            download_link = d_link.get("href")

        details_ = sp.find("div", attrs={"class": "details"})
        ps = details_.find_all("p")
        for p in ps:
            text = p.text
            description += f"{text}\n"

        # find the id3 tags
        id3 = sp.find("ul", attrs={"class": "id3-info"})
        for child in id3.children:
            tags += f"{child.text}\n"

        return {'link': download_link, 'description': description, 'tags': tags}

    def navigate_page(self, page_num=1, mode="albums"):
        """
        Navigate pages

        :param page_num: The page to navigate to
        :param mode: The content type to fetch. The available modes are: `albums`, `foreign`, `songs`
        :rtype: dict
        :return:
            Empty dictionary if the current page exceed the maximum page limit or a dictionary. Refer `self.parse_page`
        """
        mode = mode.lower()
        if mode in self.available_pages:
            self.max_pages = self.available_pages[mode]

        if page_num > self.max_pages:
            logger.warning("We cannot Fetch Content Past this Page")
            return {}

        elif page_num == 1:
            url = self.base_music_url
            match mode:
                case "albums":
                    url = self.base_album_page_url
                case "foreign":
                    url = self.base_foreign_url
                case "songs":
                    url = self.base_music_url
            if mode not in self.available_pages:
                # set limit for pages that can be fetched in that mode
                self.__set_max_pages(url, mode)

        else:
            url = self.next_page_music.format(page_num)
            match mode:
                case "albums":
                    url = self.next_page_url.format(page_num)
                case "foreign":
                    url = self.next_page_foreign.format(page_num)
                case "songs":
                    url = self.next_page_music.format(page_num)

        page = self.session.get(url)
        return self.parse_page(page)

    def get_album_link(self, link):
        """
        Gets the item link

        :param link: The link to fetch content
        :rtype: dict
        :return:
            A dictionary in format: `{'link': download_link, 'description': details, 'tags': tags}`
        """
        details_ = ""
        tags = ""
        download_link = ""
        logger.info("HipHopKit Engine: Building request....")
        cont = self.session.get(link)
        sp = Soup(cont.text, "html.parser")
        logger.info("HipHopKit Engine: Parsing page........")
        parent = sp.find("p", attrs={"class": "song-download"})
        d_link = parent.find("a")
        if d_link:
            download_link = d_link.get("href")
            logger.info("HipHopKit ENGINE: Found Album link: {}".format(download_link))
        try:
            details = sp.find("div", attrs={"class": "details"})
            details_ = details.text.strip()

            id3 = sp.find("table", attrs={"class": "id3-table"})
            for child in id3.children:
                tags += f"{child.text}\n"
        except:
            pass

        return {'link': download_link, 'description': details_, 'tags': tags}

    def __probe_for_artists(self, page, query):
        """
        Check for artists songs

        :param page: The HTML page content
        :query: The used search query
        :rtype: dict
        :return:
            A dictionary
        """
        results = {}
        # get num pages
        pages = 1
        sp = Soup(page, 'html.parser')
        span = sp.find("span", attr={'class': 'page-info'})
        if span:
            text = span.text.strip()
            num = text.split(":")[1].strip(")")
            pages = int(num.strip(" "))
            new_url = "https://justnaija.com/search?q={}&folder=&p={}"
            for page in range(pages):
                req = self.session.get(new_url.format(query, page))
                # sp1 = Soup(req.text, 'html.parser')
                result = self.parse_ordinal_page(req.text)
                results = merge_dict(results, result)
        else:
            result = self.parse_ordinal_page(page)
            results = merge_dict(results, result)

        # for each page probe for links
        return results


if __name__ == "__main__":
    import requests
    hp = HipHopKitEngineModel()
    res = hp.navigate_page(3, mode="songs")
    print(res)
