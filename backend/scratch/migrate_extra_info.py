from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS extra_info JSONB;"))
        conn.commit()
    print("✅ Migration done: extra_info column added (or already existed).")

if __name__ == "__main__":
    migrate()
