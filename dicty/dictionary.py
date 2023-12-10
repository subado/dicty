import psycopg
from psycopg import sql


class Dictionary:
    def __init__(self):
        self.dbname = 'dictionary'
        self.create_database()

    def create_database(self):
        with psycopg.connect("dbname=postgres user=postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT datname FROM pg_catalog.pg_database
                    WHERE lower(datname)=lower(%s)
                            """, [self.dbname])
                if cur.fetchone() is None:
                    cur.execute(sql.SQL("CREATE DATABASE {}")
                                .format(sql.Identifier(self.dbname)))
