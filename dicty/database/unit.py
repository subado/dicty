from typing import Optional, List
from pathlib import Path


class Pronounced:
    def __init__(self, transcription: Optional[str] = None, pronunciation_file: Optional[Path] = None):
        self.transcription = transcription
        self.pronunciation_file = pronunciation_file


class Style:
    def __init__(self, text):
        self.text = text


class Form(Pronounced):
    def __init__(self, name, text, **kw):
        self.name = name
        self.text = text

        super().__init__(**kw)


class GrammaticalFeature:
    def __init__(self, text):
        self.text = text


class Definition(Pronounced):
    def __init__(self, text: str, part_of_speech: Optional[str] = None,
                 styles: Optional[List[Style]] = None, forms: Optional[List[Form]] = None,
                 grammatical_features: Optional[List[GrammaticalFeature]] = None, **kw):
        self.text = text
        self.part_of_speech = part_of_speech
        self.styles = styles
        self.forms = forms
        self.grammatical_features = grammatical_features

        super().__init__(**kw)


class Unit:
    def __init__(self, text: str, language_code: str, definitions: List[Definition]):
        self.text = text
        self.language_code = language_code
        self.definitions = definitions
