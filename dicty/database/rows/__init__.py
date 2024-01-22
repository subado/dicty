from typing import NewType, Optional
from dataclasses import dataclass

RowId = NewType('RowId', int)


@dataclass
class BaseRow:
    id: RowId


def _row_to_id(row: Optional[BaseRow]) -> Optional[RowId]:
    if row is None:
        return None
    return row.id


@dataclass
class UnitPropertyRow:
    unit_id: RowId


@dataclass
class DefinitionPropertyRow:
    definition_id: RowId


@dataclass
class MeaningPropertyRow:
    meaning_id: RowId


@dataclass
class UnitRow(BaseRow):
    unit: str
    language_code: str


@dataclass
class DefinitionRow(BaseRow, UnitPropertyRow):
    part_of_speech: Optional[str] = None
    frequency: Optional[int] = None
    pronunciation_id: Optional[RowId] = None


@dataclass
class PronunciationRow(BaseRow):
    transcription: Optional[str] = None
    pronunciation_file: Optional[str] = None


@dataclass
class MeaningRow(BaseRow, DefinitionPropertyRow):
    meaning: str


@dataclass
class FormRow(BaseRow, DefinitionPropertyRow):
    name: str
    form: str
    pronunciation_id: Optional[RowId] = None


@dataclass
class StyleRow(BaseRow, MeaningPropertyRow):
    style: str


@dataclass
class GrammaticalFeatureRow(BaseRow, MeaningPropertyRow):
    feature: str
