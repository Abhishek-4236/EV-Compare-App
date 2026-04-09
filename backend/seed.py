# backend/seed.py
import pandas as pd
from database import engine, SessionLocal, Base
from models import Vehicle, ChatMessage, ChatSession
from embeddings import embed_text

# Create tables
Base.metadata.create_all(bind=engine)

# Read Excel
df = pd.read_excel("../India_EV_All_Segments_Dataset_2026.xlsx")

# Clean column names
df.columns = df.columns.str.strip()

db = SessionLocal()

try:
    # Clear existing data to avoid duplicates
    db.query(ChatMessage).delete()
    db.query(ChatSession).delete()
    db.query(Vehicle).delete()
    db.commit()

    inserted = 0
    for _, row in df.iterrows():
        vehicle_text = (
            f"{row['Brand']} {row['Model']}. "
            f"Category {row['Category']}. "
            f"Wheel {row['Wheel_Type']}. "
            f"Price {row['Approx_Price_INR']}. "
            f"Range {row['Range_km']} km. "
            f"Battery {row['Battery_kWh']} kWh. "
            f"Top Speed {row['Top_Speed_kmh']} kmph. "
            f"Charging {row['Charging_Type']}."
        )
        try:
            embedding = embed_text(vehicle_text)
        except Exception:
            embedding = None

        vehicle = Vehicle(
            category=str(row["Category"]).strip(),
            wheel_type=str(row["Wheel_Type"]).strip(),
            brand=str(row["Brand"]).strip(),
            model=str(row["Model"]).strip(),
            approx_price_inr=int(row["Approx_Price_INR"]),
            range_km=int(row["Range_km"]),
            battery_kwh=float(row["Battery_kWh"]),
            top_speed_kmh=int(row["Top_Speed_kmh"]) if pd.notna(row["Top_Speed_kmh"]) else None,
            vehicle_type=str(row["Vehicle_Type"]).strip(),
            charging_type=str(row["Charging_Type"]).strip(),
            market_status=str(row["Market_Status"]).strip(),
            embedding=embedding,
        )
        db.add(vehicle)
        inserted += 1

    db.commit()
    print(f"✅ Successfully inserted {inserted} vehicles into PostgreSQL!")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")

finally:
    db.close()
