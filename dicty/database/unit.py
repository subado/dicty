from typing import Optional, List, Any
from dataclasses import dataclass, field

import pycountry


class Language:
    def __init__(self, **kw: Any) -> None:
        self.code = pycountry.languages.get(**kw).alpha_3


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
    text: str
    pronunciation: Optional[Pronunciation] = None


@dataclass
class GrammaticalFeature:
    text: str


@dataclass
class Meaning:
    text: str = ''
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
    text: str
    language: Language
    definitions: List[Definition] = field(default_factory=list)
