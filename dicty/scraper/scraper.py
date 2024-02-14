from typing import Optional, List
import random
import datetime
import time
from dataclasses import dataclass

from flask import Flask
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from .website import Website
from ..db.models import Dictionary, Language, Unit
from ..db import db


@dataclass
class DictionaryToWebsites:
    dictionary: Dictionary
    websites: List[Website]


class Scraper:
    def __init__(self, headless: bool = True) -> None:
        self.dict_to_websites: List[DictionaryToWebsites] = []
        self.headless = headless

        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.set_capability('pageLoadStrategy', 'none')
        self.driver = webdriver.Firefox(options=options)

        random.seed(datetime.datetime.now().timestamp())

    def init_app(self, app: Flask, dict_to_websites: List[DictionaryToWebsites]):
        self.dict_to_websites = dict_to_websites
        for i in self.dict_to_websites:
            res = db.session.execute(
                db.select(Dictionary)
                .where(Dictionary.name == i.dictionary.name)
            ).scalar()
            if res is None:
                db.session.add(i.dictionary)
            else:
                i.dictionary = res
        db.session.commit()

    def get_unit(self, dictionary: Dictionary, search_text: str, language: Language) -> Optional[Unit]:
        if language in dictionary.languages:
            for i in range(len(self.dict_to_websites)):
                self.dict_to_websites[i].dictionary = db.session.merge(self.dict_to_websites[i].dictionary)
            mappings = filter(lambda i: i.dictionary == dictionary, self.dict_to_websites)
            for m in mappings:
                for w in m.websites:
                    is_good = False
                    urls: List[str] = []
                    for langs_to_urls in w.languages_to_urls:
                        for i in range(len(langs_to_urls.languages)):
                            langs_to_urls.languages[i] = db.session.merge(langs_to_urls.languages[i])
                            if language == langs_to_urls.languages[i]:
                                is_good = True
                                urls = langs_to_urls.urls
                                break
                    if is_good:
                        for url in urls:
                            url = w.base_url + url
                            self.driver.get(url)
                            try:
                                WebDriverWait(self.driver, w.timeout).until(
                                    EC.presence_of_element_located((By.XPATH, w.selectors.search_field)))
                            finally:
                                pass

                            time.sleep(random.random())
                            search = self.driver.find_element(By.XPATH, w.selectors.search_field)
                            search.send_keys(search_text + Keys.RETURN)

                            try:
                                WebDriverWait(self.driver, w.timeout).until(
                                    EC.presence_of_element_located((By.XPATH, w.selectors.load_persuader)))
                            finally:
                                pass

                            unit = w.get_unit(self.driver, dictionary, search_text, language)
                            if unit is not None:
                                return unit
        return None

    def __del__(self) -> None:
        self.driver.close()
