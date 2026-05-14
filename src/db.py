import os
import shutil
import sqlite3
from pathlib import Path

# Project root: parent of `src/` — default DB at <root>/data/users.db.
# On Render, set DATA_DIR to a persistent disk mount (e.g. /var/data) so logins survive restarts.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = Path(__file__).resolve().parent

_data_dir = os.environ.get("DATA_DIR", "").strip()
if _data_dir:
    DB_PATH = Path(_data_dir).resolve() / "users.db"
else:
    DB_PATH = _PROJECT_ROOT / "data" / "users.db"

_LEGACY_DB_PATH = _SRC_DIR / "data" / "users.db"

_legacy_copy_done = False


def _migrate_legacy_db_if_needed() -> None:
    """If tokens were stored under src/data/, copy that file to project data/ once."""
    global _legacy_copy_done
    if _legacy_copy_done:
        return
    _legacy_copy_done = True
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        return
    if _LEGACY_DB_PATH.exists():
        shutil.copy2(_LEGACY_DB_PATH, DB_PATH)


def get_db_path() -> str:
    """Absolute path to the SQLite file (for debugging or external tools)."""
    return str(DB_PATH.resolve())


def get_conn():
    _migrate_legacy_db_if_needed()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    _migrate_legacy_db_if_needed()
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id          INTEGER PRIMARY KEY,
                access_token         TEXT NOT NULL,
                refresh_token        TEXT NOT NULL,
                expires_at           INTEGER,
                selected_device_id   TEXT
            )
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "selected_device_id" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN selected_device_id TEXT")


def save_user(telegram_id, access_token, refresh_token, expires_at):
    tid = int(telegram_id)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (telegram_id, access_token, refresh_token, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                access_token  = excluded.access_token,
                refresh_token = excluded.refresh_token,
                expires_at    = excluded.expires_at
            """,
            (tid, access_token, refresh_token, expires_at),
        )


def get_user(telegram_id):
    tid = int(telegram_id)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (tid,)
        ).fetchone()
        return dict(row) if row else None


def delete_user(telegram_id):
    tid = int(telegram_id)
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE telegram_id = ?", (tid,))


def update_selected_device(telegram_id, device_id):
    tid = int(telegram_id)
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET selected_device_id = ? WHERE telegram_id = ?",
            (device_id, tid),
        )
