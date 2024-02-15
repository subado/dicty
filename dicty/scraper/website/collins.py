import re
import copy
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from . import Website, Selectors, LanguagesToUrls
from ...db.models import Dictionary, Unit, Definition, Language, Form, Meaning, GrammaticalFeature, Style, Pronunciation, Example, Synonym, Frequency
from ...db import db
from ...db.bakery import get_language
from ...utils import normalize_str, ignore_exception


class Collins(Website):
    _part_to_forms_names = {
        'noun': ['plural'],
        'verb': ['3rd person singular present tense',
                 'present participle',
                 'past tense',
                 'past participle']
    }

    def __init__(self, **kw):
        super().__init__(
            base_url='https://www.collinsdictionary.com/dictionary/',
            languages_to_urls=[
                LanguagesToUrls(
                    languages=[get_language(db.session()).params(name='english').scalar()],
                    urls=['/english']
                )
            ],
            selectors=Selectors(
                load_persuader='//div[@class="dictionaries dictionary"]',
                search_field='//div[@class="search-input-container"]//input[@class="search-input autoc-input"]'
            ),
            **kw
        )

    @ignore_exception(NoSuchElementException)
    def get_frequency(self, driver: WebDriver, def_tag: WebElement) -> Optional[Frequency]:
        frequency = def_tag.find_element(
            By.XPATH, './/span[@class="word-frequency-img"]').get_attribute('data-band')
        if frequency is None:
            return None
        return Frequency(frequency)

    @ignore_exception(NoSuchElementException)
    def get_transcription(self, driver: WebDriver, def_tag: WebElement) -> str:
        return normalize_str(def_tag.find_element(
            By.XPATH, './/div[@class="mini_h2"]//span[@class="pron"]').text)

    @ignore_exception(NoSuchElementException)
    def get_audio_url(self, driver: WebDriver, tag: WebElement) -> Optional[str]:
        path = tag.find_element(
            By.XPATH, './/a[contains(@title, "Pronunciation for")]').get_attribute('data-src-mp3')
        return path

    @ignore_exception(NoSuchElementException)
    def get_forms(self, driver: WebDriver, content_tag: WebElement) -> List[Form]:
        word_forms_tags = content_tag.find_elements(By.XPATH, './/span[@class="form inflected_forms type-infl"]/*')
        form_names: List[str] = []
        text: str = ''
        pronunciation: Optional[Pronunciation] = None
        forms: List[Form] = []
        for tag in word_forms_tags:
            class_attr = tag.get_attribute('class')
            if class_attr is not None:
                if 'lbl type-gram' in class_attr:
                    form_names.append(normalize_str(tag.text))

                elif 'orth' in class_attr:
                    text = normalize_str(tag.text)

                elif 'ptr hwd_sound type-hwd_sound' in class_attr:
                    if text:
                        pronunciation = Pronunciation(audio_url=self.get_audio_url(driver, tag))
                        for name in form_names:
                            forms.append(Form(name=name, text=text, pronunciation=pronunciation))
                        form_names = []
                        text = ''
                        pronunciation = None
        return forms

    def delete_extra_forms(self, part_of_speech: str, forms: List[Form]) -> None:
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

    def get_definitions(self, driver: WebDriver, content_tag: WebElement, common_def: Definition) -> List[Definition]:
        definitions: dict[str, Definition] = {}
        meanings_tags = content_tag.find_elements(
            By.XPATH, './/div[@class="hom"]/span[contains(@class, "gramGrp")]/..')

        for mean_tag in meanings_tags:

            sense_tag = mean_tag.find_element(By.XPATH, './div[@class="sense"]')
            mean = Meaning(text=sense_tag.find_element(By.XPATH, './div[@class="def"]').text)

            styles_tags = sense_tag.find_elements(
                By.XPATH, 'span[contains(@class, "lbl") and '
                '(contains(@class, "type-register") or contains(@class, "type-pragmatics"))]')
            for tag in styles_tags:
                mean.styles.append(Style(text=normalize_str(tag.text)))

            examples_tags = sense_tag.find_elements(By.XPATH, './div[@class="cit type-example"]/span[@class="quote"]')
            for tag in examples_tags:
                mean.examples.append(Example(text=tag.text))

            synonyms_tags = sense_tag.find_elements(By.XPATH, './div[@class="thes"]/a[@class="form ref"]')
            for tag in synonyms_tags:
                mean.synonyms.append(Synonym(text=normalize_str(tag.text)))

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
                    mean.grammatical_features.append(GrammaticalFeature(text=feature))
                except NoSuchElementException:
                    pass

            part_of_speech: str = normalize_str(part_of_speech_tag.text)
            if part_of_speech not in definitions:
                definitions[part_of_speech] = Definition(
                    frequency=copy.copy(common_def.frequency),
                    part_of_speech=copy.copy(part_of_speech),
                    forms=copy.copy(common_def.forms),
                    pronunciation=common_def.pronunciation
                )
                if definitions[part_of_speech].forms is not None:
                    self.delete_extra_forms(part_of_speech, definitions[part_of_speech].forms)

            definitions[part_of_speech].meanings.append(mean)

        return list(definitions.values())

    def get_unit(self, driver: WebDriver, dictionary: Dictionary, search_text: str, language: Language) -> Optional[Unit]:
        match = re.compile("^definition of '(.+)'$").match(driver.find_element(By.XPATH, '//h1').text.lower())
        if match:
            text = match.group(1)
            unit = Unit(text=text, language=language, dictionary=dictionary)

            defs_tags = driver.find_elements(By.XPATH, '//div[contains(@class, "Cob_Adv_Brit")]/*')

            for def_tag in defs_tags:
                common_def = Definition()

                common_def.frequency = self.get_frequency(driver, def_tag)
                common_def.pronunciation = Pronunciation(
                    transcription=self.get_transcription(driver, def_tag),
                    audio_url=self.get_audio_url(
                        driver, def_tag.find_element(By.XPATH, './/div[@class="mini_h2"]'))
                )

                content_tag = def_tag.find_element(By.XPATH, './/div[contains(@class, "content definitions")]')
                forms = self.get_forms(driver, content_tag)
                if forms is not None:
                    common_def.forms = forms
                unit.definitions += self.get_definitions(driver, content_tag, common_def)
            return unit
        return None
