import uuid

from typing import Optional, Final, List, TypeVar

from sqlalchemy import UniqueConstraint, Column, ForeignKey
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column, relationship, validates
from sqlalchemy.types import CHAR, REAL, Text, Uuid

from . import db

Frequency = float
LANGUAGE_CODE_LEN: Final = 3

T = TypeVar('T', bound=db.Model)


def force_lowercase(self: T, key: str, value: Optional[str]) -> Optional[str]:
    return None if value is None else value.lower()


class Id(MappedAsDataclass):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, init=False, default_factory=uuid.uuid4, primary_key=True)


class Language(db.Model):
    code: Mapped[str] = mapped_column(CHAR(LANGUAGE_CODE_LEN), primary_key=True)
    name: Mapped[str] = mapped_column(Text)

    force_lowercase = validates('code', 'name')(force_lowercase)


class Dictionary(db.Model, Id):
    name: Mapped[str] = mapped_column(Text)
    languages: Mapped[List['Language']] = relationship(
        secondary='dictionary_language',
    )

    force_lowercase = validates('name')(force_lowercase)

    __table_args__ = (
        UniqueConstraint(name),
    )


dictionary_language = db.Table(
    'dictionary_language',
    Column('language_code', ForeignKey(Language.code), primary_key=True),
    Column('dictionary_id', ForeignKey(Dictionary.id), primary_key=True)
)


class Unit(db.Model, Id):
    text: Mapped[str] = mapped_column(Text)
    language_code = mapped_column(ForeignKey('language.code'))
    dictionary_id = mapped_column(ForeignKey('dictionary.id'))

    language: Mapped['Language'] = relationship()
    dictionary: Mapped['Dictionary'] = relationship()
    definitions: Mapped[List['Definition']] = relationship(
        cascade='all, delete',
        default_factory=list
    )

    __table_args__ = (
        UniqueConstraint(text, language_code, dictionary_id),
    )


class Pronunciation(db.Model, Id):
    transcription: Mapped[Optional[str]] = mapped_column(Text, default=None)
    pronunciation_file: Mapped[Optional[str]] = mapped_column(Text, default=None)

    __table_args__ = (
        UniqueConstraint(transcription, pronunciation_file),
    )


class Definition(db.Model, Id):
    part_of_speech: Mapped[Optional[str]] = mapped_column(Text, default=None)
    frequency: Mapped[Optional[Frequency]] = mapped_column(REAL, default=None)
    unit_id = mapped_column(ForeignKey('unit.id'))
    pronunciation_id = mapped_column(ForeignKey('pronunciation.id'), nullable=True, default=None)

    pronunciation: Mapped[Optional['Pronunciation']] = relationship(default=None)
    forms: Mapped[List['Form']] = relationship(
        cascade='all, delete',
        default_factory=list
    )
    meanings: Mapped[List['Meaning']] = relationship(
        cascade='all, delete',
        default_factory=list
    )

    force_lowercase = validates('part_of_speech')(force_lowercase)

    __table_args__ = (
        UniqueConstraint(part_of_speech, frequency, unit_id, pronunciation_id),
    )


class Form(db.Model, Id):
    name: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    definition_id = mapped_column(ForeignKey('definition.id'))
    pronunciation_id = mapped_column(ForeignKey('pronunciation.id'), nullable=True)

    pronunciation: Mapped[Optional['Pronunciation']] = relationship()

    force_lowercase = validates('name')(force_lowercase)

    __table_args__ = (
        UniqueConstraint(name, text, definition_id, pronunciation_id),
    )


class Meaning(db.Model, Id):
    text: Mapped[str] = mapped_column(Text)
    definition_id = mapped_column(ForeignKey('definition.id'))

    examples: Mapped[List['Example']] = relationship(
        cascade='all, delete',
        default_factory=list
    )
    synonyms: Mapped[List['Synonym']] = relationship(
        cascade='all, delete',
        default_factory=list
    )
    styles: Mapped[List['Style']] = relationship(
        cascade='all, delete',
        default_factory=list
    )
    grammatical_features: Mapped[List['GrammaticalFeature']] = relationship(
        cascade='all, delete',
        default_factory=list
    )

    __table_args__ = (
        UniqueConstraint(text, definition_id),
    )


class Example(db.Model, Id):
    text: Mapped[str] = mapped_column(Text)
    meaning_id = mapped_column(ForeignKey('meaning.id'))

    __table_args__ = (
        UniqueConstraint(text, meaning_id),
    )


class Synonym(db.Model, Id):
    text: Mapped[Optional[str]] = mapped_column(Text)
    meaning_id = mapped_column(ForeignKey('meaning.id'))

    __table_args__ = (
        UniqueConstraint(text, meaning_id),
    )


class Style(db.Model, Id):
    text: Mapped[str] = mapped_column(Text)
    meaning_id = mapped_column(ForeignKey('meaning.id'))

    __table_args__ = (
        UniqueConstraint(text, meaning_id),
    )


class GrammaticalFeature(db.Model, Id):
    text: Mapped[str] = mapped_column(Text)
    meaning_id = mapped_column(ForeignKey('meaning.id'))

    __table_args__ = (
        UniqueConstraint(text, meaning_id),
    )
