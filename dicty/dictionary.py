from psycopg.rows import class_row

from .database import Database
from .scraper import Scraper
from .scraper.website import Selectors
from .scraper.website.collins import Collins
from .database.unit import Language
from .database.rows import BaseRow, UnitRow, RowId
from .utils import add_tabs, not_none


class Dictionary:
    def __init__(self) -> None:
        self.db = Database('dictionary', 'user=postgres')
        self.scraper = Scraper(headless=True)
        self.create_websites()

    def create_websites(self) -> None:
        self.websites = [
            Collins(
                'Collins English Dictionary',
                'english',
                10,
                Language(name='English'),
                Selectors(
                    load_persuader='//div[@class="dictionaries dictionary"]',
                    search_field='//div[@class="search-input-container"]//input[@class="search-input autoc-input"]'
                )
            )
        ]

    def run(self) -> None:
        site = self.websites[0]
        with self.db.connect() as conn:
            while True:
                search_text = input()
                cur = conn.cursor(row_factory=class_row(BaseRow))
                unit_id = self.db.select_unit_id(cur, UnitRow(id=RowId(0), unit=search_text, language_code=site.language.code))
                is_not_found = unit_id is None

                if is_not_found:
                    unit = self.scraper.get_unit(search_text, site)
                else:
                    cur.close()
                    unit = not_none(self.db.get_unit(conn, not_none(unit_id)))
                if is_not_found:
                    self.db.insert_unit(cur, unit)
                    conn.commit()
                print(f'From {site.name}:\n')
                print(add_tabs(str(unit)))
                print()
