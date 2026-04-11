import os
import sys
import pandas as pd
from pathlib import Path

# Add backend dir to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, SessionLocal, Base
from models import Vehicle
from services.data_cleaning import clean_column_names, transform_row
from embeddings import embed_text

def run_import():
    data_path = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "India_EV_All_Segments_Dataset_2026.xlsx"
    
    if not data_path.exists():
        print(f"Dataset not found at {data_path}. Ensure it is placed there.")
        return

    print("Reading Excel...")
    df = pd.read_excel(data_path)
    df = clean_column_names(df)
    
    required = ["brand", "model", "approx_price_inr", "range_km", "battery_kwh"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")

    db = SessionLocal()
    
    try:
        Base.metadata.create_all(bind=engine)
        
        print("Clearing existing vehicles... (In production, we would soft-delete or merge)")
        db.query(Vehicle).delete()
        db.commit()

        inserted = 0
        for _, row in df.iterrows():
            transformed = transform_row(row)
            
            # Simple embedding logic
            vehicle_text = (
                f"{transformed['brand']} {transformed['model']}. "
                f"Category {transformed['category']}. "
                f"Price {transformed['approx_price_inr']}. "
                f"Range {transformed['range_km']} km. "
                f"Battery {transformed['battery_kwh']} kWh. "
                f"Charging {transformed['charging_type']}."
            )
            
            try:
                embedding = embed_text(vehicle_text)
            except Exception:
                embedding = None

            vehicle = Vehicle(
                **transformed,
                embedding=embedding
            )
            db.add(vehicle)
            inserted += 1

        db.commit()
        print(f"[SUCCESS] Successfully inserted {inserted} vehicles into PostgreSQL!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error importing data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_import()
