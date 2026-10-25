"""SQLite persistence helpers for the student API."""

import sqlite3
from pathlib import Path
from typing import Iterator

DATABASE_PATH = Path(__file__).resolve().parent.parent / "students.db"


def connect(database_path: Path | str = DATABASE_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path | str = DATABASE_PATH) -> None:
    with connect(database_path) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                course TEXT,
                address TEXT,
                CHECK (email IS NOT NULL OR phone IS NOT NULL)
            )"""
        )


def get_connection(database_path: Path | str = DATABASE_PATH) -> Iterator[sqlite3.Connection]:
    connection = connect(database_path)
    try:
        yield connection
    finally:
        connection.close()
