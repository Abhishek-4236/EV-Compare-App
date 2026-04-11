# backend/migrate_db.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    if not DATABASE_URL:
        print("DATABASE_URL not found")
        return

    engine = create_engine(DATABASE_URL)
    commands = [
        "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS expertise_level VARCHAR(20) DEFAULT 'Novice';",
        "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS lessons_learned TEXT;"
    ]

    with engine.connect() as conn:
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                conn.commit()
                print(f"Executed: {cmd[:50]}...")
            except Exception as e:
                print(f"Error executing {cmd}: {e}")

if __name__ == "__main__":
    migrate()
