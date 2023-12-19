import re
import copy
from pathlib import Path
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from . import Website, Selectors
from ...database.unit import Unit, Definition, Language, Form, Meaning, GrammaticalFeature, Style, Pronunciation
from ...utils import normalize_str, catch_none


class Collins(Website):
    _part_to_forms_names = {
        'noun': ['plural'],
        'verb': ['3rd person singular present tense',
                 'present participle',
                 'past tense',
                 'past participle']
    }

    def __init__(self, name: str, url: str, timeout: float, language: Language, selectors: Selectors):
        url = 'https://www.collinsdictionary.com/dictionary/' + url
        super().__init__(name, url, timeout, language, selectors)

    @catch_none(NoSuchElementException)
    def get_frequency(self, def_tag: WebElement, driver: WebDriver) -> Optional[int]:
        frequency = def_tag.find_element(
            By.XPATH, './/span[@class="word-frequency-img"]').get_attribute('data-band')
        if frequency is None:
            return None
        return int(frequency)

    @catch_none(NoSuchElementException)
    def get_transcription(self, def_tag: WebElement, driver: WebDriver) -> str:
        return normalize_str(def_tag.find_element(
            By.XPATH, './/div[@class="mini_h2"]//span[@class="pron"]').text)

    @catch_none(NoSuchElementException)
    def get_pronunciation_file(self, tag: WebElement, driver: WebDriver) -> Optional[Path]:
        path = tag.find_element(
            By.XPATH, './/a[contains(@title, "Pronunciation for")]').get_attribute('data-src-mp3')
        if path is None:
            return None
        return Path(path)

    @catch_none(NoSuchElementException)
    def get_forms(self, content_tag: WebElement, driver: WebDriver) -> List[Form]:
        word_forms_tags = content_tag.find_elements(By.XPATH, './/span[@class="form inflected_forms type-infl"]/*')
        form_names: List[str] = []
        form: str = ''
        pronunciation: Optional[Pronunciation] = None
        forms: List[Form] = []
        for tag in word_forms_tags:
            class_attr = tag.get_attribute('class')
            if class_attr is not None:
                if 'lbl type-gram' in class_attr:
                    form_names.append(normalize_str(tag.text))

                elif 'orth' in class_attr:
                    print()
                    form = normalize_str(tag.text)

                elif 'ptr hwd_sound type-hwd_sound' in class_attr:
                    if form:
                        pronunciation = Pronunciation(pronunciation_file=self.get_pronunciation_file(tag, driver))
                        for name in form_names:
                            forms.append(Form(name=name, text=form, pronunciation=pronunciation))
                        form_names = []
                        form = ''
                        pronunciation = None
        return forms

    def delete_extra_forms(self, part_of_speech: str, forms: List[Form]):
        for part, form_names in self._part_to_forms_names.items():
            if re.compile(r'\b(?:%s)\b' % part).search(part_of_speech):
                i = 0
                while i < len(forms):
                    if forms[i].name not in form_names:
                        forms.pop(i)
                        i -= 1
                    i += 1
                return
        forms.clear()

    def get_definitions(self, content_tag: WebElement, common_def: Definition, driver: WebDriver) -> List[Definition]:
        definitions: dict[str, Definition] = {}
        meanings_tags = content_tag.find_elements(
            By.XPATH, './/div[@class="hom"]/span[contains(@class, "gramGrp")]/..')

        for mean_tag in meanings_tags:
            mean = Meaning()
            part_of_speech_tag: WebElement
            try:
                part_of_speech_tag = mean_tag.find_element(
                    By.XPATH, './span[@class="gramGrp pos"]')
            except NoSuchElementException:
                grammar = mean_tag.find_element(
                    By.XPATH, './span[@class="gramGrp"]')
                part_of_speech_tag = grammar.find_element(
                    By.XPATH, './span[@class="pos"]')
                try:
                    feature = grammar.find_element(
                        By.XPATH, './span[@class="lbl type-syntax"]').text
                    feature = normalize_str(feature)
                    mean.grammatical_features.append(GrammaticalFeature(feature))
                except NoSuchElementException:
                    pass

            part_of_speech: str = normalize_str(part_of_speech_tag.text)
            if part_of_speech not in definitions:
                definitions[part_of_speech] = Definition(
                    frequency=common_def.frequency,
                    part_of_speech=part_of_speech,
                    forms=copy.copy(common_def.forms),
                    pronunciation=common_def.pronunciation
                )
                if definitions[part_of_speech].forms is not None:
                    self.delete_extra_forms(part_of_speech, definitions[part_of_speech].forms)

            sense_tag = mean_tag.find_element(By.XPATH, './div[@class="sense"]')
            mean.text = sense_tag.find_element(By.XPATH, './div[@class="def"]').text

            senses_tags = sense_tag.find_elements(
                By.XPATH, 'span[contains(@class, "lbl") and '
                '(contains(@class, "type-register") or contains(@class, "type-pragmatics"))]')
            for tag in senses_tags:
                mean.styles.append(Style(normalize_str(tag.text)))

            definitions[part_of_speech].meanings.append(mean)

        return list(definitions.values())

    def get_unit(self, search_text: str, driver: WebDriver) -> Unit:
        match = re.compile("^definition of '(.+)'$").match(driver.find_element(By.XPATH, '//h1').text.lower())
        if match:
            text = match.group(1)
            unit = Unit(text=text, language=self.language)

            defs_tags = driver.find_elements(By.XPATH, '//div[contains(@class, "Cob_Adv_Brit")]/*')

            for def_tag in defs_tags:
                common_def = Definition()

                common_def.frequency = self.get_frequency(def_tag, driver)
                common_def.pronunciation = Pronunciation(
                    transcription=self.get_transcription(def_tag, driver),

                    pronunciation_file=self.get_pronunciation_file(
                        def_tag.find_element(By.XPATH, './/div[@class="mini_h2"]'), driver)
                )

                content_tag = def_tag.find_element(By.XPATH, './/div[contains(@class, "content definitions")]')
                forms = self.get_forms(content_tag, driver)
                if forms is not None:
                    common_def.forms = forms
                unit.definitions += self.get_definitions(content_tag, common_def, driver)
            return unit
        raise Exception
