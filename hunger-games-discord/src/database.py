from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from sqlite3 import Error, Connection, Cursor, connect, Row
from typing import Iterator


class Database:
    ROOT: Path = Path(__file__).resolve().parent.parent

    def __init__(self) -> None:
        DB: Path = self.ROOT / ".data"
        DB.mkdir(parents=True, exist_ok=True)
        self.conn: Connection = connect(DB / "database.sqlite")
        self.conn.row_factory = Row
        self.conn.executescript("PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON;")
        with open(f"{self.ROOT / "src" / "data" / "ddl.sql"}", "r") as f:
            self.conn.executescript(f.read())

    @contextmanager
    def get_cursor(self) -> Iterator[Cursor]:
        cursor: Cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Error:
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def backup(self) -> None:
        TS: str = datetime.now().strftime("%d%m%Y_%H%M%S")
        BACKUP_DIR: Path = self.ROOT / ".backups"
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP: Path = BACKUP_DIR / f"{TS}.sqlite"
        self.conn.execute(f"VACUUM INTO '{BACKUP.as_posix()}'")

    def upsert(
        self, data: dict, conflict_cols: list[str] = ["id"], user: bool = True
    ) -> dict | None:
        try:
            table: str = "users" if user else "tributes"
            cols: str = ", ".join(data.keys())
            placeholder: str = ", ".join(["?"] * len(data))
            c_cols: str = ", ".join(conflict_cols)
            update_placeholder: str = ", ".join(
                [f"{c} = excluded.{c}" for c in data.keys()]
            )
            sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholder}) ON CONFLICT ({c_cols}) DO UPDATE SET {update_placeholder} RETURNING *;"

            with self.get_cursor() as c:
                row = c.execute(sql, list(data.values())).fetchone()
            return dict(row) if row else None
        except Error as e:
            raise Exception(f"Error creating in {table}: {e}")

    def close(self) -> None:
        self.conn.close()
