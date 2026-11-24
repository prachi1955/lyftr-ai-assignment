import os
import aiosqlite

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Convert sqlite:///./app.db -> ./app.db
# Later Docker will use sqlite:////data/app.db -> /data/app.db
def get_database_path():
    if DATABASE_URL.startswith("sqlite:///"):
        return DATABASE_URL.replace("sqlite:///", "", 1)
    return DATABASE_URL


async def init_db():
    db_path = get_database_path()

    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)

        await db.commit()
from datetime import datetime, timezone
import json


async def save_message(session_id, role, content, metadata=None):
    db_path = get_database_path()

    metadata_json = json.dumps(metadata) if metadata is not None else None
    created_at = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO messages (
                session_id,
                role,
                content,
                metadata,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                metadata_json,
                created_at
            )
        )

        await db.commit()
async def get_messages(session_id):
    db_path = get_database_path()

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT role, content, metadata
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,)
        )

        rows = await cursor.fetchall()

        messages = []

        for row in rows:
            message = {
                "role": row["role"],
                "content": row["content"]
            }

            if row["metadata"]:
                message["metadata"] = json.loads(row["metadata"])

            messages.append(message)

        return messages