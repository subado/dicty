from typing import Optional, List
from dataclasses import dataclass, field
from ..utils import add_tabs

import pycountry


class Language:
    def __init__(self, code: Optional[str] = None, **kw: Optional[str]) -> None:
        if code is None:
            self.code: str = pycountry.languages.get(**kw).alpha_3
        else:
            self.code = code

    def __repr__(self):
        s = self.code
        return s


@dataclass
class Pronunciation:
    transcription: Optional[str] = None
    pronunciation_file: Optional[str] = None

    def __repr__(self):
        s = '['
        if self.transcription is not None:
            s += self.transcription
        s += ']'
        s += '('
        if self.pronunciation_file is not None:
            s += self.pronunciation_file
        s += ')'
        return s


@dataclass
class Style:
    text: str

    def __repr__(self):
        s = self.text
        return s


@dataclass
class Form:
    name: str
    text: str
    pronunciation: Optional[Pronunciation] = None

    def __repr__(self):
        s = f'{self.name} \t {self.text}'
        if self.pronunciation is not None:
            s += str(self.pronunciation)
        return s


@dataclass
class GrammaticalFeature:
    text: str

    def __repr__(self):
        s = self.text
        return s


@dataclass
class Meaning:
    text: str = ''
    styles: List[Style] = field(default_factory=list)
    grammatical_features: List[GrammaticalFeature] = field(default_factory=list)

    def __repr__(self):
        s = self.text + '\n'
        if len(self.styles) > 0:
            s += 'styles: ' + str(self.styles) + '\n'
        if len(self.grammatical_features) > 0:
            s += 'grammatical_features: ' + str(self.grammatical_features) + '\n'

        return s


@dataclass
class Definition:
    meanings: List[Meaning] = field(default_factory=list)
    frequency: Optional[int] = None
    part_of_speech: Optional[str] = None
    forms: List[Form] = field(default_factory=list)
    pronunciation: Optional[Pronunciation] = None

    def __repr__(self):
        head = ''
        if self.pronunciation is not None:
            head += str(self.pronunciation) + '\n'
        if self.part_of_speech is not None:
            head += self.part_of_speech + '\n'
        if self.frequency is not None:
            head += f'frequency\t{self.frequency}\n'

        head += 'forms:\n'
        forms = ''
        for i in range(len(self.forms)):
            forms += str(self.forms[i]) + '\n'
        head += add_tabs(forms) + '\n'

        body = ''
        for i in range(len(self.meanings)):
            body += f'{i + 1})\n'
            body += str(self.meanings) + '\n'
        body = add_tabs(body)

        return head + body


@dataclass
class Unit:
    text: str
    language: Language
    definitions: List[Definition] = field(default_factory=list)

    def __repr__(self):
        head = self.text + f'[{self.language}]' + '\n'
        body = ''
        for i in range(len(self.definitions)):
            body += f'{i + 1}.\n'
            body += str(self.definitions[i]) + '\n'
        body = add_tabs(body)

        return head + body
