import psycopg2
import traceback
import sys
from types import SimpleNamespace
from textwrap import dedent
from src.db import Query, DB


class PostgresQuery(Query):
    pass


class PostgresDB(DB):
    def __init__(self, config: SimpleNamespace) -> psycopg2.extensions.cursor:
        connection = psycopg2.connect(**config.auth, connect_timeout=3)
        connection.autocommit = True
        self.cursor = connection.cursor()

    def execute(self, stmt: str, query: PostgresQuery = None):
        """Execute statement using DB-specific connector
        """
        try:
            self.cursor.execute(stmt)
        except (psycopg2.ProgrammingError, psycopg2.InternalError):
            msg = ""
            if query:
                msg = dedent(f'''
                    ERROR: executing '{query.name}':
                    SQL path "{query.path}"'''
                )
            else:
                msg = "ERROR: executing query:\n\n"
            msg += f"\n\n{stmt}\n\n{traceback.format_exc()}\n"
            sys.stderr.write(msg)
            exit(1)

    def clean_schemas(self, prefix: str):
        """ Drop schemata that have a specific name prefix
        """
        cmd = f"""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name ~ '^{prefix}.*'
        OR    schema_name NOT IN (SELECT table_schema FROM information_schema.tables)
        AND   schema_name ~ '.*_mat$';"""

        self.execute(cmd)
        for schema_name in self.cursor.fetchall():
            self.execute(f"DROP SCHEMA {schema_name[0]} CASCADE;")
