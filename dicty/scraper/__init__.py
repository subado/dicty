import random
import datetime
import time

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from .website import Website


class Scraper:
    def __init__(self, headless=True):
        self.headless = headless
        options = Options()

        if headless:
            options.add_argument('--headless')

        random.seed(datetime.datetime.now().timestamp())
        options.set_capability('pageLoadStrategy', 'none')
        self.driver = webdriver.Firefox(options=options)

    def get_unit(self, search_text: str, website: Website):
        self.driver.get(website.url)
        try:
            WebDriverWait(self.driver, website.timeout).until(
                EC.presence_of_element_located((By.XPATH, website.selectors.search_field)))
        finally:
            pass

        time.sleep(random.random())
        search = self.driver.find_element(By.XPATH, website.selectors.search_field)
        search.send_keys(search_text + Keys.RETURN)

        try:
            WebDriverWait(self.driver, website.timeout).until(
                EC.presence_of_element_located((By.XPATH, website.selectors.load_persuader)))
        finally:
            pass

        return website.get_unit(website, self.driver)

    def __del__(self):
        self.driver.close()
