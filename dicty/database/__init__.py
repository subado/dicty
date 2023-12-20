from typing import Optional, NewType

import psycopg
from psycopg import sql, Cursor
from psycopg.rows import class_row
import pycountry
from pydantic import BaseModel

from .unit import Unit, Definition, Pronunciation, Meaning, Style, GrammaticalFeature, Form


RowId = NewType('RowId', int)


class BaseTable(BaseModel):
    id: RowId


def _table_to_id(base_table: Optional[BaseTable]) -> Optional[RowId]:
    if base_table is not None:
        return base_table.id
    return None


class Database:
    def __init__(self, name: str) -> None:
        self.name = name
        self.create()

    def create(self) -> None:
        with psycopg.connect('dbname=postgres user=postgres', autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT datname FROM pg_catalog.pg_database
                    WHERE lower(datname)=lower(%s)
                            """, [self.name])
                if cur.fetchone() is None:
                    cur.execute(sql.SQL('CREATE DATABASE {}')
                                .format(sql.Identifier(self.name)))

                    self.create_tables()

    def create_tables(self) -> None:
        with psycopg.connect(f'dbname={self.name} user=postgres') as conn:
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
        with psycopg.connect(f'dbname={self.name} user=postgres') as conn:
            with conn.cursor() as cur:
                for lang in pycountry.languages:
                    cur.execute("INSERT INTO languages_codes (code) VALUES (%s)", [lang.alpha_3])

                conn.commit()

    def insert_unit(self, unit: Unit) -> Optional[RowId]:
        with psycopg.connect(f'dbname={self.name} user=postgres') as conn:
            with conn.cursor(row_factory=class_row(BaseTable)) as cur:
                cur.execute("""
                    INSERT INTO units (unit, language_code) VALUES(%(unit)s, %(language_code)s) RETURNING id
                """, {'unit': unit.text,
                      'language_code': unit.language.code})

                row_id = _table_to_id(cur.fetchone())
                if row_id is not None:
                    for definition in unit.definitions:
                        self.insert_definition(definition, row_id, cur)
                    conn.commit()
            return row_id

    def insert_definition(self, definition: Definition, unit_id: RowId, cur: Cursor[BaseTable]) -> Optional[RowId]:
        cur.execute("""
            INSERT INTO definitions (unit_id, part_of_speech, frequency)
                VALUES (%(unit_id)s, %(part_of_speech)s, %(frequency)s) RETURNING id
        """, {'unit_id': unit_id,
              'part_of_speech': definition.part_of_speech,
              'frequency': definition.frequency})

        row_id = _table_to_id(cur.fetchone())

        if row_id is not None:
            if definition.pronunciation is not None:
                pronunciation_id = self.insert_pronunciation(definition.pronunciation, cur)
                if pronunciation_id is not None:
                    cur.execute("""
                        UPDATE definitions
                            SET pronunciation_id = %(pronunciation_id)s
                            WHERE id = %(id)s
                    """, {'pronunciation_id': pronunciation_id,
                          'id': row_id})
            for meaning in definition.meanings:
                self.insert_meaning(meaning, row_id, cur)
            for form in definition.forms:
                self.insert_form(form, row_id, cur)

        return row_id

    def insert_pronunciation(self, pronunciation: Pronunciation, cur: Cursor[BaseTable]) -> Optional[RowId]:
        row_id = self.select_pronunciation(pronunciation, cur)
        if row_id is None:
            cur.execute("""
                INSERT INTO pronunciations (transcription, pronunciation_file)
                    VALUES (%(transcription)s, %(pronunciation_file)s) RETURNING id
            """, {'transcription': pronunciation.transcription,
                  'pronunciation_file': pronunciation.pronunciation_file})
            row_id = _table_to_id(cur.fetchone())

        return row_id

    def insert_meaning(self, meaning: Meaning, definition_id: RowId, cur: Cursor[BaseTable]) -> Optional[RowId]:
        cur.execute("""
            INSERT INTO meanings (definition_id, meaning)
                VALUES (%(definition_id)s, %(meaning)s) RETURNING id
        """, {'definition_id': definition_id,
              'meaning': meaning.text})
        row_id = _table_to_id(cur.fetchone())
        if row_id is not None:
            for style in meaning.styles:
                self.insert_style(style, row_id, cur)
            for grammatical_feature in meaning.grammatical_features:
                self.insert_grammatical_feature(grammatical_feature, row_id, cur)
        return row_id

    def insert_style(self, style: Style, meaning_id: RowId, cur: Cursor[BaseTable]) -> Optional[RowId]:
        cur.execute("""
            INSERT INTO styles (meaning_id, style)
                VALUES (%(meaning_id)s, %(style)s) RETURNING id
        """, {'meaning_id': meaning_id,
              'style': style.text})
        return _table_to_id(cur.fetchone())

    def insert_grammatical_feature(self, feature: GrammaticalFeature, meaning_id: RowId, cur: Cursor[BaseTable]) -> Optional[RowId]:
        cur.execute("""
            INSERT INTO grammatical_features (meaning_id, feature)
                VALUES (%(meaning_id)s, %(feature)s) RETURNING id
        """, {'meaning_id': meaning_id,
              'feature': feature.text})
        return _table_to_id(cur.fetchone())

    def insert_form(self, form: Form, definition_id: RowId, cur: Cursor[BaseTable]) -> Optional[RowId]:
        cur.execute("""
            INSERT INTO forms (definition_id, name, form)
                VALUES (%(definition_id)s, %(name)s, %(form)s) RETURNING id
        """, {'definition_id': definition_id,
              'name': form.name,
              'form': form.text})
        row_id = _table_to_id(cur.fetchone())
        if row_id is not None:
            if form.pronunciation is not None:
                pronunciation_id = self.insert_pronunciation(form.pronunciation, cur)
                if pronunciation_id is not None:
                    cur.execute("""
                        UPDATE forms
                            SET pronunciation_id = %(pronunciation_id)s
                            WHERE id = %(id)s
                        """, {'pronunciation_id': pronunciation_id,
                              'id': row_id})

        return row_id

    def select_pronunciation(self, pronunciation: Pronunciation, cur: Cursor[BaseTable]) -> Optional[RowId]:
        cur.execute("""
            SELECT id FROM pronunciations WHERE
                transcription IS NOT DISTINCT FROM %(transcription)s AND
                pronunciation_file IS NOT DISTINCT FROM %(pronunciation_file)s
            """, {'transcription': pronunciation.transcription,
                  'pronunciation_file': pronunciation.pronunciation_file})
        return _table_to_id(cur.fetchone())

    def select_unit(self, unit: Unit, cur: Cursor[BaseTable]) -> Optional[RowId]:
        cur.execute("""
            SELECT id FROM units WHERE
                unit = %(unit)s AND
                language_code = %(language_code)s
            """, {'unit': unit.text,
                  'language_code': unit.language.code})
        return _table_to_id(cur.fetchone())
