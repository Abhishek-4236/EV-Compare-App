from database import engine
from sqlalchemy import text

def force_drop():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS chat_feedback CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS vehicles CASCADE;"))
        conn.commit()
    print("Force dropped tables.")

if __name__ == "__main__":
    force_drop()
