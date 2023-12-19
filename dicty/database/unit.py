from typing import Optional, List
from pathlib import Path
from dataclasses import dataclass, field

import pycountry


class Language:
    def __init__(self, **kw):
        self.code = pycountry.languages.get(**kw).alpha_3


@dataclass
class Pronunciation:
    transcription: Optional[str] = None
    pronunciation_file: Optional[Path] = None


@dataclass
class Style:
    text: str


@dataclass
class Form:
    name: str = None
    text: str = None
    pronunciation: Pronunciation = None


@dataclass
class GrammaticalFeature:
    text: str


@dataclass
class Meaning:
    text: str = None
    styles: Optional[List[Style]] = field(default_factory=list)
    grammatical_features: Optional[List[GrammaticalFeature]] = field(default_factory=list)


@dataclass
class Definition:
    meanings: List[Meaning] = field(default_factory=list)
    frequency: Optional[int] = None
    part_of_speech: Optional[str] = None
    forms: Optional[List[Form]] = field(default_factory=list)
    pronunciation: Pronunciation = None


@dataclass
class Unit:
    text: str
    language: Language
    definitions: List[Definition] = field(default_factory=list)
