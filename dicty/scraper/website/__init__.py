from typing import List, Optional
from dataclasses import dataclass
from abc import ABCMeta, abstractmethod

from selenium.webdriver.remote.webdriver import WebDriver

from ...db.models import Dictionary, Language, Unit


@dataclass
class LanguagesToUrls:
    languages: List[Language]
    urls: List[str]


@dataclass
class Selectors:
    load_persuader: str
    search_field: str


@dataclass
class Website(metaclass=ABCMeta):
    selectors: Selectors
    base_url: str
    timeout: float
    languages_to_urls: List[LanguagesToUrls]

    @abstractmethod
    def get_unit(self, driver: WebDriver, dictionary: Dictionary, search_text: str, language: Language) -> Optional[Unit]:
        return NotImplemented
