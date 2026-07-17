"""Snowflake connection helper, using PAT (programmatic access token) auth."""

import os

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection() -> snowflake.connector.SnowflakeConnection:
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        token=os.environ["SNOWFLAKE_TOKEN"],
        authenticator="PROGRAMMATIC_ACCESS_TOKEN",
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        role=os.environ["SNOWFLAKE_ROLE"],
    )


def run_query(
    sql: str,
    params: tuple = (),
    conn: snowflake.connector.SnowflakeConnection | None = None,
) -> list[dict]:
    """Run a query and return rows as a list of dicts.

    Pass an existing `conn` to reuse it (skips PAT auth + warehouse resume on
    every call) — essential when running many queries back to back, e.g. a
    portfolio-wide scan. Without one, opens and closes a connection per call,
    which is fine for a single ad hoc query.
    """
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    try:
        cur = conn.cursor(snowflake.connector.DictCursor)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        if owns_conn:
            conn.close()
