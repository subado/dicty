from dataclasses import dataclass
from abc import ABCMeta, abstractmethod

from selenium.webdriver.remote.webdriver import WebDriver

from ...database.unit import Unit, Language


@dataclass
class Selectors:
    load_persuader: str
    search_field: str


class Website(metaclass=ABCMeta):
    def __init__(self, name: str, url: str, timeout: float, language: Language, selectors: Selectors):
        self.name = name
        self.url = url
        self.timeout = timeout
        self.language = language
        self.selectors = selectors

    @abstractmethod
    def get_unit(self, search_text: str, driver: WebDriver) -> Unit:
        return NotImplemented
