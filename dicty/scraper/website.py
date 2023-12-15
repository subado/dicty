from dataclasses import dataclass

from selenium.webdriver.remote.webdriver import BaseWebDriver

from ..database.unit import Unit, Language


@dataclass
class Selectors:
    load_persuader: str
    search_field: str


class Website:
    def __init__(self, name: str, url: str, timeout: float, language: Language, selectors: Selectors):
        self.name = name
        self.url = url
        self.timeout = timeout
        self.language = language
        self.selectors = selectors

    def get_unit(driver: BaseWebDriver) -> Unit:
        pass
