import re
import uuid as uuid4

from typing import Optional, List

from sqlalchemy import UniqueConstraint, Column, ForeignKey, Table
from sqlalchemy.orm import (
    Mapped,
    DeclarativeBase,
    mapped_column,
    relationship,
    validates,
    MappedAsDataclass,
    declared_attr,
)
from sqlalchemy.types import Uuid


class Base(DeclarativeBase, MappedAsDataclass):
    @declared_attr.directive
    def __tablename__(cls: DeclarativeBase) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()


def force_lowercase(self: DeclarativeBase, key: str, value: Optional[str]) -> Optional[str]:
    return None if value is None else value.lower()


class Id(MappedAsDataclass):
    uuid: Mapped[uuid4.UUID] = mapped_column(Uuid, init=False, default_factory=uuid4.uuid4, primary_key=True)


class String(MappedAsDataclass):
    value: Mapped[str]


class PartOfSpeech(Base, Id, String):
    pass


class Language(Base):
    code: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    parts_of_speech: Mapped[List['PartOfSpeech']] = relationship(
        secondary='language_parts_of_speech',
        default_factory=list
    )

    force_lowercase = validates('code', 'name')(force_lowercase)


language_parts_of_speech = Table(
    'language_parts_of_speech',
    Base.metadata,
    Column('language_code', ForeignKey(Language.code), primary_key=True),
    Column('part_of_speech_uuid', ForeignKey(PartOfSpeech.uuid), primary_key=True)
)


class Source(Base, Id):
    name: Mapped[str]
    url: Mapped[str]
    languages: Mapped[List['Language']] = relationship(
        secondary='source_language',
        default_factory=list
    )

    force_lowercase = validates('name')(force_lowercase)

    __table_args__ = (
        UniqueConstraint('name'),
    )


source_language = Table(
    'source_language',
    Base.metadata,
    Column('language_code', ForeignKey(Language.code), primary_key=True),
    Column('source_uuid', ForeignKey(Source.uuid), primary_key=True)
)


class Unit(Base, Id, String):
    language_code = mapped_column(ForeignKey('language.code'))
    source_uuid = mapped_column(ForeignKey('source.uuid'))

    source: Mapped['Source'] = relationship()
    language: Mapped['Language'] = relationship()
    definitions: Mapped[List['Definition']] = relationship(
        cascade='all, delete',
        default_factory=list
    )

    __table_args__ = (
        UniqueConstraint('value', 'language_code', 'source_uuid'),
    )


class Pronunciation(Base, Id):
    transcription: Mapped[Optional[str]] = mapped_column(default=None)
    audio_path: Mapped[Optional[str]] = mapped_column(default=None)

    __table_args__ = (
        UniqueConstraint(transcription, audio_path),
    )


class Definition(Base, Id):
    unit_uuid = mapped_column(ForeignKey('unit.uuid'))
    part_of_speech_uuid = mapped_column(ForeignKey('part_of_speech.uuid'), nullable=True)
    part_of_speech: Mapped[Optional[PartOfSpeech]] = relationship()

    forms: Mapped[List['Form']] = relationship(
        cascade='all, delete',
        default_factory=list
    )
    senses: Mapped[List['Sense']] = relationship(
        cascade='all, delete',
        default_factory=list
    )

    __table_args__ = (
        UniqueConstraint(unit_uuid),
    )


class Form(Base, Id, String):
    name: Mapped[Optional[str]] = mapped_column(default=None)
    definition_uuid = mapped_column(ForeignKey('definition.uuid'))

    pronunciations: Mapped['Pronunciation'] = relationship(
        default_factory=list,
        secondary='form_pronunciations'
    )

    force_lowercase = validates('name')(force_lowercase)

    __table_args__ = (
        UniqueConstraint('name', 'value', 'definition_uuid'),
    )


form_pronunciations = Table(
    'form_pronunciations',
    Base.metadata,
    Column('form_uuid', ForeignKey(Form.uuid), primary_key=True),
    Column('pronunciation_uuid', ForeignKey(Pronunciation.uuid), primary_key=True)
)


class Sense(Base, Id, String):
    definition_uuid = mapped_column(ForeignKey('definition.uuid'))

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
        UniqueConstraint('value', definition_uuid),
    )


class Example(Base, Id, String):
    sense_uuid = mapped_column(ForeignKey('sense.uuid'))

    __table_args__ = (
        UniqueConstraint('value', sense_uuid),
    )


class Synonym(Base, Id, String):
    unit_uuid = mapped_column(ForeignKey('sense.uuid'))
    sense_uuid: Mapped[Optional[uuid4.UUID]] = mapped_column(ForeignKey('unit.uuid'), default=None)

    __table_args__ = (
        UniqueConstraint('value', sense_uuid),
    )


class Style(Base, Id, String):
    sense_uuid = mapped_column(ForeignKey('sense.uuid'))

    __table_args__ = (
        UniqueConstraint('value', sense_uuid),
    )


class GrammaticalFeature(Base, Id, String):
    sense_uuid = mapped_column(ForeignKey('sense.uuid'))

    __table_args__ = (
        UniqueConstraint('value', sense_uuid),
    )
