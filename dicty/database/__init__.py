import psycopg
from psycopg import sql
import pycountry


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
                        unit_id SERIAL PRIMARY KEY,
                        unit text UNIQUE NOT NULL,
                        language_code char({lang_code_len}) REFERENCES languages_codes NOT NULL
                    );

                    CREATE TABLE pronunciations (
                        transcription text,
                        pronunciation_file text
                    );

                    CREATE TABLE definitions (
                        definition_id SERIAL PRIMARY KEY,
                        unit_id integer REFERENCES units NOT NULL,
                        definition text NOT NULL,
                        part_of_speech text
                    ) INHERITS (pronunciations);

                    CREATE TABLE styles (
                        style_id SERIAL PRIMARY KEY,
                        definition_id integer REFERENCES definitions NOT NULL,
                        style text NOT NULL
                    );

                    CREATE TABLE forms (
                        form_id SERIAL PRIMARY KEY,
                        definition_id integer REFERENCES definitions NOT NULL,
                        name text NOT NULL,
                        form text NOT NULL
                    ) INHERITS (pronunciations);

                    CREATE TABLE grammatical_features (
                        feature_id SERIAL PRIMARY KEY,
                        definition_id integer REFERENCES definitions NOT NULL,
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
