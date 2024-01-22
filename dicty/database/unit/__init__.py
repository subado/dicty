from typing import Optional, List
from dataclasses import dataclass, field
from ...utils import add_tabs

import pycountry


class Language:
    def __init__(self, code: Optional[str] = None, **kw: Optional[str]) -> None:
        if code is None:
            self.code: str = pycountry.languages.get(**kw).alpha_3
        else:
            self.code = code


@dataclass
class Pronunciation:
    transcription: Optional[str] = None
    pronunciation_file: Optional[str] = None


@dataclass
class Style:
    text: str


@dataclass
class Form:
    name: str
    form: str
    pronunciation: Optional[Pronunciation] = None


@dataclass
class GrammaticalFeature:
    text: str


@dataclass
class Meaning:
    meaning: str = ''
    styles: List[Style] = field(default_factory=list)
    grammatical_features: List[GrammaticalFeature] = field(default_factory=list)


@dataclass
class Definition:
    meanings: List[Meaning] = field(default_factory=list)
    frequency: Optional[int] = None
    part_of_speech: Optional[str] = None
    forms: List[Form] = field(default_factory=list)
    pronunciation: Optional[Pronunciation] = None


@dataclass
class Unit:
    unit: str
    language: Language
    definitions: List[Definition] = field(default_factory=list)
