import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text

def add_columns():
    with engine.connect() as connection:
        try:
            connection.execute(text("ALTER TABLE chat_sessions ADD COLUMN user_id INTEGER;"))
            print("Added user_id column")
        except Exception as e:
            print(f"Error adding user_id: {e}")
            
        try:
            connection.execute(text("ALTER TABLE chat_sessions ADD COLUMN title VARCHAR(200) DEFAULT 'New Chat';"))
            print("Added title column")
        except Exception as e:
            print(f"Error adding title: {e}")
        
        connection.commit()
        print("Schema update complete")

if __name__ == "__main__":
    add_columns()
