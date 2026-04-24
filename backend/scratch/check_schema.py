import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text, inspect

def check_and_fix():
    inspector = inspect(engine)
    
    # Get current columns
    cols = [c['name'] for c in inspector.get_columns('vehicles')]
    print(f"Current columns: {cols}")
    
    if 'extra_info' not in cols:
        print("Column 'extra_info' missing — adding it now...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE vehicles ADD COLUMN extra_info JSONB;"))
            conn.commit()
        print("✅ Column added.")
    else:
        print("✅ Column already present.")
    
    # Verify
    inspector2 = inspect(engine)
    cols2 = [c['name'] for c in inspector2.get_columns('vehicles')]
    print(f"Columns after fix: {cols2}")

if __name__ == "__main__":
    check_and_fix()
