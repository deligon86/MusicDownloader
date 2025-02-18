"""
Some base classes
"""
import requests
from requests import Session
from urllib.parse import urlsplit


class MusicScrapperConfig:
    """configurator class for music scrapper"""
    navigate_all_pages = False
    start_page = 1
    verbosity = True
    max_page = 200


class BillboardConfig:
    """configurator class for billboard scrapper"""
    song_list_size = 50  # default 5
    artist_list_size = 15
    audio_only = True
    verbosity = True


class Colors:
    critical = "\033[1;31m"
    success = "\033[1;32m"
    warning = "\033[1;33m"  # yellow
    highlight = "\033[1;37m"
    header = "\033[0;35m"
    endc ="\033[0m"


# Will have to make this singleton
class Logger:

    def __init__(self):
        pass

    @staticmethod
    def warning(msg):

        print(f"{Colors.warning}[WARNING   ] {msg} {Colors.endc}")

    @staticmethod
    def critical(msg):

        print(f"{Colors.critical}[Critical ] {msg} {Colors.endc}")

    @staticmethod
    def success(msg):

        print(f"{Colors.success}[Success  ] {msg} {Colors.endc}")

    @staticmethod
    def highlight(msg):

        print(f"{Colors.highlight}[Check   ] {msg} {Colors.endc}")

    @staticmethod
    def info(msg):

        print(f"{Colors.header}[Info     ] {msg} {Colors.endc}")


class Common:
    logger = Logger()

    def __init__(self):
        self.session = Session()
        self.verbose = False
    
    def create_new_session(self):
        """returns a new session object"""

        return Session()


class SessionManager:

    def __init__(self):
        self.use_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
        self.sessions = {}

    def create_new_session(self, session, link=None, discard_old=False):
        # base_ = urlsplit(link)[0]
        if session in self.sessions.keys():
            if discard_old:
                headers = {"User-Agent": self.use_agent}
                new_ses = Session()
                new_ses.headers = headers
                self.sessions[session] = new_ses
                return new_ses
            else:
                return self.sessions[session]

        else:
            new_ses = Session()
            self.sessions[session] = new_ses
            return new_ses

    def get_session(self, session):
        if session in self.sessions.keys():
            return self.sessions[session]

    def delete_session(self, session):
        if session in self.sessions:
            self.sessions.pop(session)


def connection(max_retry=5):
    Logger.info("[ConnectionTest] Testing for active Connection")
    try:
        requests.get("https://google.com", timeout=max_retry)
        Logger.info("[ConnectionTest] Succeeded")
        return True
    except Exception as e:
        Logger.info(f"[ConnectionTest] Failed with Error: {e}")
        return False
