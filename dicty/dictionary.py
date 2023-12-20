from .database import Database
from .scraper import Scraper
from .scraper.website import Selectors
from .scraper.website.collins import Collins
from .database.unit import Language


class Dictionary:
    def __init__(self) -> None:
        self.db = Database('dictionary')
        self.scraper = Scraper(headless=True)
        self.create_websites()

    def create_websites(self) -> None:
        self.websites = [
            Collins(
                'Collins English Dictionary',
                'english',
                10,
                Language(name='English'),
                Selectors(
                    load_persuader='//div[@class="dictionaries dictionary"]',
                    search_field='//div[@class="search-input-container"]//input[@class="search-input autoc-input"]'
                )
            )
        ]
