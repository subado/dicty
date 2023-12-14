from typing import Optional, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Pronounced:
    transcription: Optional[str] = None
    pronunciation_file: Optional[Path] = None


@dataclass
class Style:
    text: str


@dataclass
class Form(Pronounced):
    name: str
    text: str


@dataclass
class GrammaticalFeature:
    text: str


@dataclass
class Meaning:
    text: str
    styles: Optional[List[Style]] = None
    grammatical_features: Optional[List[GrammaticalFeature]] = None


@dataclass
class Definition(Pronounced):
    meanings: List[Meaning] = None
    frequency: Optional[int] = None
    part_of_speech: Optional[str] = None
    forms: Optional[List[Form]] = None


@dataclass
class Unit:
    text: str
    language_code: str
    definitions: List[Definition] = None
