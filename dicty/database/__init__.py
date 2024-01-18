from typing import Optional, Any, List

import psycopg
from psycopg.rows import class_row
from psycopg import sql, Cursor
import pycountry

from ..utils import not_none
from .unit import Unit, Definition, Pronunciation, Meaning, Style, GrammaticalFeature, Form, Language
from .rows import RowId, BaseRow, UnitRow, DefinitionRow, PronunciationRow, MeaningRow, FormRow, StyleRow, GrammaticalFeatureRow, _row_to_id


class Database:
    def __init__(self, dbname: str, options: str = '') -> None:
        self._dbname = dbname
        self._options = options
        self._dsn = f'dbname={self._dbname} ' + options
        self.create()

    def create(self) -> None:
        with psycopg.connect(f'dbname=postgres {self._options}', autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT datname FROM pg_catalog.pg_database
                    WHERE lower(datname)=lower(%s)
                            """, [self._dbname])
                if cur.fetchone() is None:
                    cur.execute(sql.SQL('CREATE DATABASE {}')
                                .format(sql.Identifier(self._dbname)))

                    self.create_tables()

    def create_tables(self) -> None:
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                lang_code_len = 3
                cur.execute(sql.SQL("""
                    CREATE TABLE languages_codes (
                        code char({lang_code_len}) PRIMARY KEY
                    );

                    CREATE TABLE units (
                        id SERIAL PRIMARY KEY,
                        unit text  NOT NULL,
                        language_code char({lang_code_len}) REFERENCES languages_codes NOT NULL,
                        UNIQUE(unit, language_code)
                    );

                    CREATE TABLE pronunciations (
                        id SERIAL PRIMARY KEY,
                        transcription text NULL,
                        pronunciation_file text NULL,
                        UNIQUE(transcription,  pronunciation_file)
                    );

                    CREATE TABLE definitions (
                        id SERIAL PRIMARY KEY,
                        unit_id integer REFERENCES units NOT NULL,
                        part_of_speech text NULL,
                        frequency smallint NULL,
                        pronunciation_id integer REFERENCES pronunciations
                    );

                    CREATE TABLE meanings (
                        id SERIAL PRIMARY KEY,
                        definition_id integer REFERENCES definitions NOT NULL,
                        meaning text NOT NULL
                    );

                    CREATE TABLE styles (
                        id SERIAL PRIMARY KEY,
                        meaning_id integer REFERENCES meanings NOT NULL,
                        style text NOT NULL
                    );

                    CREATE TABLE forms (
                        id SERIAL PRIMARY KEY,
                        definition_id integer REFERENCES definitions NOT NULL,
                        name text NOT NULL,
                        form text NOT NULL,
                        pronunciation_id integer REFERENCES pronunciations
                    );

                    CREATE TABLE grammatical_features (
                        id SERIAL PRIMARY KEY,
                        meaning_id integer REFERENCES meanings NOT NULL,
                        feature text NOT NULL
                    );
                """).format(lang_code_len=lang_code_len))

                conn.commit()

                self.insert_languages_codes()

    def insert_languages_codes(self) -> None:
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                for lang in pycountry.languages:
                    cur.execute("INSERT INTO languages_codes (code) VALUES (%s)", [lang.alpha_3])

                conn.commit()

    def insert_unit(self, cur: Cursor[BaseRow], unit: Unit) -> RowId:
        cur.execute("""
            INSERT INTO units (unit, language_code) VALUES(%(unit)s, %(language_code)s) RETURNING id
        """, {'unit': unit.text,
              'language_code': unit.language.code})

        row = not_none(cur.fetchone())
        for definition in unit.definitions:
            self.insert_definition(cur, definition, row.id)
        return row.id

    def insert_definition(self, cur: Cursor[BaseRow], definition: Definition, unit_id: RowId) -> RowId:
        cur.execute("""
            INSERT INTO definitions (unit_id, part_of_speech, frequency)
                VALUES (%(unit_id)s, %(part_of_speech)s, %(frequency)s) RETURNING id
        """, {'unit_id': unit_id,
              'part_of_speech': definition.part_of_speech,
              'frequency': definition.frequency})

        row = not_none(cur.fetchone())

        if definition.pronunciation is not None:
            pronunciation_id = self.insert_pronunciation(cur, definition.pronunciation)
            if pronunciation_id is not None:
                cur.execute("""
                    UPDATE definitions
                        SET pronunciation_id = %(pronunciation_id)s
                        WHERE id = %(id)s
                """, {'pronunciation_id': pronunciation_id,
                      'id': row.id})
        for meaning in definition.meanings:
            self.insert_meaning(cur, meaning, row.id)
        for form in definition.forms:
            self.insert_form(cur, form, row.id)

        return row.id

    def insert_pronunciation(self, cur: Cursor[BaseRow], pronunciation: Pronunciation) -> RowId:
        pronunciation_id = self.select_pronunciation_id(
            cur,
            PronunciationRow(
                RowId(0),
                transcription=pronunciation.transcription,
                pronunciation_file=pronunciation.pronunciation_file
            )
        )
        if pronunciation_id is None:
            cur.execute("""
                INSERT INTO pronunciations (transcription, pronunciation_file)
                    VALUES (%(transcription)s, %(pronunciation_file)s) RETURNING id
            """, {'transcription': pronunciation.transcription,
                  'pronunciation_file': pronunciation.pronunciation_file})
            row = not_none(cur.fetchone())
            pronunciation_id = row.id

        return pronunciation_id

    def insert_meaning(self, cur: Cursor[BaseRow], meaning: Meaning, definition_id: RowId) -> RowId:
        cur.execute("""
            INSERT INTO meanings (definition_id, meaning)
                VALUES (%(definition_id)s, %(meaning)s) RETURNING id
        """, {'definition_id': definition_id,
              'meaning': meaning.text})
        row = not_none(cur.fetchone())
        for style in meaning.styles:
            self.insert_style(cur, style, row.id)
        for grammatical_feature in meaning.grammatical_features:
            self.insert_grammatical_feature(cur, grammatical_feature, row.id)
        return row.id

    def insert_style(self, cur: Cursor[BaseRow], style: Style, meaning_id: RowId) -> RowId:
        cur.execute("""
            INSERT INTO styles (meaning_id, style)
                VALUES (%(meaning_id)s, %(style)s) RETURNING id
        """, {'meaning_id': meaning_id,
              'style': style.text})
        return not_none(cur.fetchone()).id

    def insert_grammatical_feature(self, cur: Cursor[BaseRow], feature: GrammaticalFeature, meaning_id: RowId) -> RowId:
        cur.execute("""
            INSERT INTO grammatical_features (meaning_id, feature)
                VALUES (%(meaning_id)s, %(feature)s) RETURNING id
        """, {'meaning_id': meaning_id,
              'feature': feature.text})
        row = cur.fetchone()
        assert row is not None
        return row.id

    def insert_form(self, cur: Cursor[BaseRow], form: Form, definition_id: RowId) -> RowId:
        cur.execute("""
            INSERT INTO forms (definition_id, name, form)
                VALUES (%(definition_id)s, %(name)s, %(form)s) RETURNING id
        """, {'definition_id': definition_id,
              'name': form.name,
              'form': form.text})
        row = not_none(cur.fetchone())
        if form.pronunciation is not None:
            pronunciation_id = self.insert_pronunciation(cur, form.pronunciation)
            if pronunciation_id is not None:
                cur.execute("""
                    UPDATE forms
                        SET pronunciation_id = %(pronunciation_id)s
                        WHERE id = %(id)s
                    """, {'pronunciation_id': pronunciation_id,
                          'id': row.id})

        return row.id

    def select_pronunciation_id(self, cur: Cursor[BaseRow], pronunciation_row: PronunciationRow) -> Optional[RowId]:
        cur.execute("""
            SELECT id FROM pronunciations WHERE
                transcription IS NOT DISTINCT FROM %(transcription)s AND
                pronunciation_file IS NOT DISTINCT FROM %(pronunciation_file)s
            """, {'transcription': pronunciation_row.transcription,
                  'pronunciation_file': pronunciation_row.pronunciation_file})
        return _row_to_id(cur.fetchone())

    def select_unit_id(self, cur: Cursor[BaseRow], unit_row: UnitRow) -> Optional[RowId]:
        cur.execute("""
            SELECT id FROM units WHERE
                unit = %(unit)s AND
                language_code = %(language_code)s
            """, {'unit': unit_row.unit,
                  'language_code': unit_row.language_code})
        return _row_to_id(cur.fetchone())

    def connect(self, *args: Any, **kwargs: Any) -> psycopg.Connection:
        return psycopg.connect(self._dsn, *args, **kwargs)

    def select_unit_row(self, cur: Cursor[UnitRow], unit_id: RowId) -> Optional[UnitRow]:
        cur.execute("""
            SELECT id, unit, language_code FROM units WHERE
                id = %(id)s
            """, {'id': unit_id})
        return cur.fetchone()

    def select_definition_rows(self, cur: Cursor[DefinitionRow], unit_id: RowId) -> List[DefinitionRow]:
        cur.execute("""
            SELECT id, unit_id, part_of_speech, frequency, pronunciation_id FROM definitions WHERE
                unit_id = %(unit_id)s
            """, {'unit_id': unit_id})
        return cur.fetchall()

    def select_meaning_rows(self, cur: Cursor[MeaningRow], definition_id: RowId) -> List[MeaningRow]:
        cur.execute("""
                SELECT id, definition_id, meaning FROM meanings WHERE
                    definition_id = %(definition_id)s
                """, {'definition_id': definition_id})
        return cur.fetchall()

    def select_form_rows(self, cur: Cursor[FormRow], definition_id: RowId) -> List[FormRow]:
        cur.execute("""
                SELECT id, definition_id, name, form FROM forms WHERE
                    definition_id = %(definition_id)s
                """, {'definition_id': definition_id})
        return cur.fetchall()

    def select_pronunciation_row(self, cur: Cursor[PronunciationRow], pronunciation_id: RowId) -> Optional[PronunciationRow]:
        cur.execute("""
            SELECT id, transcription, pronunciation_file FROM pronunciations WHERE
                id = %(pronunciation_id)s
            """, {'pronunciation_id': pronunciation_id})
        return cur.fetchone()

    def select_style_rows(self, cur: Cursor[StyleRow], meaning_id: RowId) -> List[StyleRow]:
        cur.execute("""
            SELECT id, style, meaning_id FROM styles WHERE
                meaning_id = %(meaning_id)s
            """, {'meaning_id': meaning_id})
        return cur.fetchall()

    def select_grammatical_features(self, cur: Cursor[GrammaticalFeatureRow], meaning_id: RowId) -> List[GrammaticalFeatureRow]:
        cur.execute("""
            SELECT id, feature, meaning_id FROM grammatical_features WHERE
                meaning_id = %(meaning_id)s
            """, {'meaning_id': meaning_id})
        return cur.fetchall()

    def get_unit(self, conn: psycopg.Connection, unit_id: RowId) -> Optional[Unit]:
        cur = conn.cursor(row_factory=class_row(UnitRow))
        unit_row = self.select_unit_row(cur, unit_id)
        cur.close()

        if unit_row is None:
            return None

        return Unit(unit_row.unit, Language(unit_row.language_code), self.get_definitions(conn, unit_id))

    def get_definitions(self, conn: psycopg.Connection, unit_id: RowId) -> List[Definition]:
        cur = conn.cursor(row_factory=class_row(DefinitionRow))
        definition_rows = self.select_definition_rows(cur, unit_id)
        cur.close()

        definitions: List[Definition] = []
        if len(definition_rows) != 0:
            for row in definition_rows:
                definitions.append(
                    Definition(
                        self.get_meanings(conn, row.id),
                        row.frequency,
                        row.part_of_speech,
                        self.get_forms(conn, row.id)
                    )
                )
                if row.pronunciation_id is not None:
                    definitions[len(definitions) - 1].pronunciation = self.get_pronunciation(conn, row.pronunciation_id)

        return definitions

    def get_meanings(self, conn: psycopg.Connection, definition_id: RowId) -> List[Meaning]:
        cur = conn.cursor(row_factory=class_row(MeaningRow))
        meaning_rows = self.select_meaning_rows(cur, definition_id)
        cur.close()

        meanings: List[Meaning] = []
        if len(meaning_rows) != 0:
            for row in meaning_rows:
                meanings.append(
                    Meaning(
                        row.meaning,
                        self.get_styles(conn, row.id),
                        self.get_grammatical_features(conn, row.id)
                    )
                )

        return meanings

    def get_forms(self, conn: psycopg.Connection, definition_id: RowId) -> List[Form]:
        cur = conn.cursor(row_factory=class_row(FormRow))
        form_rows = self.select_form_rows(cur, definition_id)
        cur.close()

        forms: List[Form] = []
        if len(form_rows) != 0:
            for row in form_rows:
                forms.append(
                    Form(
                        row.name,
                        row.form,
                    )
                )
                if row.pronunciation_id is not None:
                    forms[len(forms) - 1].pronunciation = self.get_pronunciation(conn, row.pronunciation_id)

        return forms

    def get_pronunciation(self, conn: psycopg.Connection, pronunciation_id: RowId) -> Optional[Pronunciation]:
        cur = conn.cursor(row_factory=class_row(PronunciationRow))
        row = self.select_pronunciation_row(cur, pronunciation_id)
        cur.close()

        if row is not None:
            return Pronunciation(row.transcription, row.pronunciation_file)

        return None

    def get_styles(self, conn: psycopg.Connection, meaning_id: RowId) -> List[Style]:
        cur = conn.cursor(row_factory=class_row(StyleRow))
        style_rows = self.select_style_rows(cur, meaning_id)
        cur.close()

        styles: List[Style] = []
        if len(style_rows) != 0:
            for row in style_rows:
                styles.append(
                    Style(
                        row.style
                    )
                )
        return styles

    def get_grammatical_features(self, conn: psycopg.Connection, meaning_id: RowId) -> List[GrammaticalFeature]:
        cur = conn.cursor(row_factory=class_row(GrammaticalFeatureRow))
        feature_rows = self.select_grammatical_features(cur, meaning_id)
        cur.close()

        features: List[GrammaticalFeature] = []
        if len(feature_rows) != 0:
            for row in feature_rows:
                features.append(
                    GrammaticalFeature(
                        row.feature
                    )
                )
        return features
