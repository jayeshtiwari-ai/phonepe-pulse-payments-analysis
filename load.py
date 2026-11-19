"""
load.py - PhonePe Pulse Database Loader
Loads clean DataFrames into MySQL (with automated fallback to SQLite) using SQLAlchemy.
Enforces Composite Primary Keys, builds (state, year, quarter) indexes, and verifies row counts.
"""

import os
import re
from typing import Dict, Tuple
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import dotenv

# Load environment credentials from .env
dotenv.load_dotenv()


def get_db_engine() -> Tuple[Engine, str]:
    """
    Creates SQLAlchemy database engine.
    Attempts MySQL first using credentials from .env; falls back to SQLite if unavailable.
    """
    db_type = os.getenv("DB_TYPE", "mysql").lower()
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "phonepe_pulse")

    if db_type == "mysql":
        try:
            print(f"Attempting connection to MySQL at {host}:{port} as user '{user}'...")
            # First connect to server root to ensure target database exists
            root_engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}", isolation_level="AUTOCOMMIT")
            with root_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            root_engine.dispose()

            # Now connect to target database
            db_engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}")
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Successfully connected to MySQL database '{db_name}'.")
            return db_engine, "MySQL"
        except Exception as e:
            print(f"MySQL connection failed ({e}). Falling back to SQLite...")

    # Fallback to SQLite
    sqlite_file = "phonepe_pulse.db"
    print(f"Initializing SQLite database at '{sqlite_file}'...")
    sqlite_engine = create_engine(f"sqlite:///{sqlite_file}")
    return sqlite_engine, "SQLite"


def init_schema(engine: Engine, schema_file: str = "schema.sql", db_dialect: str = "MySQL"):
    """Executes schema.sql statements to create tables and indexes."""
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found at {schema_file}")

    with open(schema_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Pre-drop all tables to guarantee a clean, idempotent slate
    table_names = [
        "agg_transaction", "agg_user", "agg_user_device", "agg_insurance",
        "map_transaction", "map_user", "map_insurance",
        "top_transaction", "top_user", "top_insurance"
    ]

    with engine.connect() as conn:
        for tbl in table_names:
            conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
        conn.commit()

        # Split SQL into individual statements and strip comments
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
        for stmt in statements:
            cleaned_stmt = re.sub(r"--.*$", "", stmt, flags=re.MULTILINE).strip()
            if not cleaned_stmt:
                continue
            if cleaned_stmt.upper().startswith("CREATE INDEX") and db_dialect == "SQLite":
                sqlite_stmt = re.sub(r"CREATE INDEX", "CREATE INDEX IF NOT EXISTS", cleaned_stmt, flags=re.IGNORECASE)
                conn.execute(text(sqlite_stmt))
            else:
                conn.execute(text(cleaned_stmt))
        conn.commit()
    print("Database schema and indexes initialized successfully.")


def load_all_tables(engine: Engine, data_dir: str = "data_clean") -> Dict[str, Tuple[int, int, bool]]:
    """Loads all CSVs from data_clean into database tables and verifies row counts."""
    tables = [
        "agg_transaction",
        "agg_user",
        "agg_user_device",
        "agg_insurance",
        "map_transaction",
        "map_user",
        "map_insurance",
        "top_transaction",
        "top_user",
        "top_insurance"
    ]

    results = {}
    print("\nLoading tables into database...")
    print("-" * 60)

    for table_name in tables:
        csv_path = os.path.join(data_dir, f"{table_name}.csv")
        if not os.path.exists(csv_path):
            print(f"Warning: {csv_path} not found. Skipping.")
            continue

        df = pd.read_csv(csv_path)
        csv_rows = len(df)

        # Append data to the pre-created schema table
        df.to_sql(table_name, con=engine, if_exists="append", index=False, chunksize=2000)

        # Verify DB row count
        with engine.connect() as conn:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            db_rows = res.scalar()

        is_match = (csv_rows == db_rows)
        results[table_name] = (csv_rows, db_rows, is_match)
        print(f" -> {table_name:<18} loaded: {db_rows:,} rows (CSV: {csv_rows:,}) [{'MATCH' if is_match else 'MISMATCH'}]")

    print("-" * 60)
    return results


def print_load_summary(results: Dict[str, Tuple[int, int, bool]], db_dialect: str):
    """Prints a comparison table of CSV vs DB row counts."""
    print("\n" + "=" * 75)
    print(f"DATABASE LOAD VERIFICATION SUMMARY ({db_dialect})")
    print("=" * 75)
    print(f"{'TABLE NAME':<20} | {'CSV ROWS':<12} | {'DB ROWS':<12} | {'STATUS':<15}")
    print("-" * 75)

    all_matched = True
    total_csv = 0
    total_db = 0

    for table_name, (csv_count, db_count, match) in results.items():
        total_csv += csv_count
        total_db += db_count
        status = "PASS (Match)" if match else "FAIL (Mismatch)"
        if not match:
            all_matched = False
        print(f"{table_name:<20} | {csv_count:<12,} | {db_count:<12,} | {status:<15}")

    print("-" * 75)
    print(f"{'TOTAL':<20} | {total_csv:<12,} | {total_db:<12,} | {'ALL PASSED' if all_matched else 'SOME FAILED'}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    engine, dialect = get_db_engine()
    init_schema(engine, "schema.sql", dialect)
    load_results = load_all_tables(engine)
    print_load_summary(load_results, dialect)
