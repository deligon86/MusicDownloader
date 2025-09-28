"""
Some base classes
"""
import os
import requests
from requests import Session


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


# Singleton sessionmanager to manage sessions
# will have to remove this, it doesn't improve anything
class SessionManager:
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.use_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
            self.sessions = {}
            self._initialized = True

    def create_new_session(self, session, discard_old=False):
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
        return self.sessions[session]

    def delete_session(self, session):
        if session in self.sessions:
            self.sessions.pop(session)


def connection(max_retry=5):
    #logger.info("[ConnectionTest] Testing for active Connection")
    try:
        requests.get("https://google.com", timeout=max_retry)
        #logger.info("ConnectionTest: Succeeded")
        return True
    except Exception as e:
        #logger.warning(f"ConnectionTest: Failed with Error {e}")
        return False


def get_app_home_directory():
    """
    Get home path
    For now, supports windows
    """
    home_name = "MusicDL"
    path = os.path.join(os.path.expanduser("~"), os.path.join("AppData/Local", home_name))
    if not os.path.exists(path):
        os.makedirs(path)
    return path
