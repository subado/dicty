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
class Definition(Pronounced):
    text: str
    part_of_speech: Optional[str] = None
    styles: Optional[List[Style]] = None
    forms: Optional[List[Form]] = None
    grammatical_features: Optional[List[GrammaticalFeature]] = None


@dataclass
class Unit:
    text: str
    language_code: str
    frequency: Optional[int] = None
    definitions: List[Definition] = None
