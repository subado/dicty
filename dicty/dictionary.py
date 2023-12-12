import pycountry

from .database import Database
from .scraper import Scraper
from .scraper.website import Website, Selectors


class Dictionary:
    def __init__(self) -> None:
        self.db = Database('dictionary')
        self.scraper = Scraper(headless=False)
        self.create_websites()

    def create_websites(self) -> None:
        self.websites = [
            Website(
                'Collins English Dictionary',
                'https://www.collinsdictionary.com/dictionary/english',
                10,
                pycountry.languages.get(name='English').alpha_3,
                Selectors(
                    load_persuader='//h1',
                    search_field='//div[@class="search-input-container"]//input[@class="search-input autoc-input"]',
                )),
            Website(
                "Oxford Learner's Dictionary",
                'https://www.oxfordlearnersdictionaries.com/definition/english/',
                8,
                pycountry.languages.get(name='English').alpha_3,
                Selectors(
                    load_persuader='//h1',
                    search_field='//div[@class="searchfield"]//input[@class="searchfield_input"]')
            )
        ]
