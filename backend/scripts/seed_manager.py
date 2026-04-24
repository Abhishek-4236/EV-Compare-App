# backend/scripts/seed_manager.py
import argparse
import os
import re
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path to allow importing backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import Vehicle, ChatMessage, ChatSession, ChatFeedback, KnowledgeArticle
from services.embeddings import embed_text, chunk_text, get_model

# ── Configuration Paths ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
VEHICLE_DATA_PATH = BASE_DIR.parent / "data" / "raw" / "India_EV_All_Segments_Dataset_2026_filled.xlsx"
ARTICLES_DIR = BASE_DIR / "data" / "articles"

def map_segment(category: str) -> str:
    value = (category or "").strip().lower()
    if value == "2w": return "TWO_WHEELER"
    if value == "3w": return "THREE_WHEELER"
    if value == "4w": return "FOUR_WHEELER"
    if value == "truck": return "TRUCK"
    if value == "bus": return "BUS"
    return "FOUR_WHEELER"

# --- Adaptive Mapping & Parsing ---

CANONICAL_MAPPING = {
    "brand": ["Brand", "Manufacturer", "Make"],
    "model": ["Model", "Variant", "Name"],
    "category": ["Category", "Segment"],
    "approx_price_inr": ["Approx_Price_INR", "Price", "Ex-showroom Price", "Price (INR)"],
    "range_km": ["Range_km", "Certified Range", "Range (km)"],
    "battery_kwh": ["Battery_kWh", "Battery Capacity", "Battery (kWh)"],
    "top_speed_kmh": ["Top_Speed", "Top Speed (kmph)", "Max Speed"],
    "motor_kw": ["Motor_Power", "Motor", "Power (kW)"],
    "safety_rating": ["Safety Rating", "Safety_Rating", "NCAP Rating"],
    "warranty_years": ["Vehicle Warranty", "Warranty", "Warranty (Years)"],
    "charging_type": ["Charging_Type", "Charge Type", "Connector"],
    "market_status": ["Market_Status", "Status", "Availability"],
    "vehicle_type": ["Vehicle_Type", "Body Type"],
    "wheel_type": ["Wheel size", "Tyre Size", "Wheels"],
    "launch_year": ["Launch_Year", "Year"],
    "image_url": ["Image_URL", "Photo"],
    "connected_features": ["GPS", "Connected Features", "App Support"],
    "regenerative_braking": ["Regenerative_Braking", "Regen"],
}

def smart_parse_value(val, target_type=str):
    if pd.isna(val) or str(val).lower() == 'nan':
        return None
    
    val_str = str(val).strip()
    
    if target_type in (int, float):
        # Extract first numeric-looking thing
        # Handles "8 Years", "₹16.5L", "106.4 kW"
        val_str = val_str.replace(',', '')
        if 'L' in val_str.upper() and target_type == int:
             # Handle Lakh notation if needed, but usually prices are raw ints in this sheet
             pass
        
        match = re.search(r'(\d+(\.\d+)?)', val_str)
        if match:
            num = float(match.group(1))
            return int(num) if target_type == int else num
        return 0 if target_type == int else 0.0

    if target_type == bool:
        v = val_str.lower()
        if v in ('yes', 'true', '1', 'available', 'y'): return True
        if v in ('no', 'false', '0', 'n', 'not applicable'): return False
        return False

    return val_str

def get_column_map(df_cols):
    """Matches Excel columns to our DB fields using fuzzy canonical list."""
    mapping = {}
    found_cols = set()
    
    for db_field, synonyms in CANONICAL_MAPPING.items():
        for syn in synonyms:
            # Case insensitive & strip match
            matches = [c for c in df_cols if c.strip().lower() == syn.lower()]
            if matches:
                mapping[db_field] = matches[0]
                found_cols.add(matches[0])
                break
    
    # Identify leftovers for 'extra_info'
    extra_cols = [c for c in df_cols if c not in found_cols]
    return mapping, extra_cols

def seed_vehicles(db: Session, force: bool = False):
    if not VEHICLE_DATA_PATH.exists():
        print(f"Error: Vehicle data not found at {VEHICLE_DATA_PATH}")
        return

    if force:
        print("Clearing existing vehicle-related data...")
        # Clear children first to satisfy FKs if any (ChatMessage refers to Vehicle)
        db.query(ChatMessage).delete()
        db.query(ChatFeedback).delete()
        db.query(ChatSession).delete()
        db.query(Vehicle).delete()
        db.commit()

    df = pd.read_excel(VEHICLE_DATA_PATH)
    col_map, extra_cols = get_column_map(df.columns.tolist())
    
    print(f"Mapped {len(col_map)} canonical columns. Found {len(extra_cols)} extra attributes.")

    texts_to_embed = []
    rows_processed = []

    for _, row in df.iterrows():
        data = {}
        # Populate canonical fields
        data['brand'] = smart_parse_value(row.get(col_map.get('brand', ''))) or "Unknown"
        data['model'] = smart_parse_value(row.get(col_map.get('model', ''))) or "Unknown"
        data['category'] = smart_parse_value(row.get(col_map.get('category', ''))) or "4W"
        
        # Numeric fields
        data['approx_price_inr'] = smart_parse_value(row.get(col_map.get('approx_price_inr', '')), int) or 0
        data['range_km'] = smart_parse_value(row.get(col_map.get('range_km', '')), int) or 0
        data['battery_kwh'] = smart_parse_value(row.get(col_map.get('battery_kwh', '')), float) or 0.0
        data['top_speed_kmh'] = smart_parse_value(row.get(col_map.get('top_speed_kmh', '')), int)
        data['motor_kw'] = smart_parse_value(row.get(col_map.get('motor_kw', '')), float)
        data['safety_rating'] = smart_parse_value(row.get(col_map.get('safety_rating', '')), int)
        data['warranty_years'] = smart_parse_value(row.get(col_map.get('warranty_years', '')), int)
        data['launch_year'] = smart_parse_value(row.get(col_map.get('launch_year', '')), int)
        
        # Bool/Str
        data['connected_features'] = smart_parse_value(row.get(col_map.get('connected_features', '')), bool)
        data['regenerative_braking'] = smart_parse_value(row.get(col_map.get('regenerative_braking', '')), bool)
        data['charging_type'] = smart_parse_value(row.get(col_map.get('charging_type', '')))
        data['market_status'] = smart_parse_value(row.get(col_map.get('market_status', ''))) or "Available"
        data['vehicle_type'] = smart_parse_value(row.get(col_map.get('vehicle_type', '')))
        data['wheel_type'] = smart_parse_value(row.get(col_map.get('wheel_type', '')))
        data['image_url'] = smart_parse_value(row.get(col_map.get('image_url', '')))

        # Overflow for dynamic 'extra_info'
        extra_data = {}
        for c in extra_cols:
            val = row.get(c)
            if not pd.isna(val):
                extra_data[c] = str(val)
        data['extra_info'] = extra_data

        # Text for RAG embedding
        summary = f"{data['brand']} {data['model']}. {data['category']} {data['vehicle_type']}. " \
                  f"Range: {data['range_km']}km, Battery: {data['battery_kwh']}kWh, " \
                  f"Price: ₹{data['approx_price_inr']}. Status: {data['market_status']}."
        
        texts_to_embed.append(summary)
        rows_processed.append(data)

    print(f"Generating embeddings for {len(texts_to_embed)} vehicles...")
    try:
        embed_model = get_model()
        embeddings = embed_model.encode(texts_to_embed, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
    except Exception as e:
        print(f"Warning: Failed to generate embeddings: {e}")
        embeddings = [None] * len(texts_to_embed)

    for i, data in enumerate(rows_processed):
        vehicle = Vehicle(
            segment=map_segment(data['category']),
            category=data['category'],
            wheel_type=data['wheel_type'],
            brand=data['brand'],
            model=data['model'],
            approx_price_inr=data['approx_price_inr'],
            range_km=data['range_km'],
            battery_kwh=data['battery_kwh'],
            top_speed_kmh=data['top_speed_kmh'],
            motor_kw=data['motor_kw'],
            safety_rating=data['safety_rating'],
            warranty_years=data['warranty_years'],
            connected_features=data['connected_features'],
            regenerative_braking=data['regenerative_braking'],
            charging_type=data['charging_type'],
            vehicle_type=data['vehicle_type'],
            market_status=data['market_status'],
            launch_year=data['launch_year'],
            image_url=data['image_url'],
            extra_info=data['extra_info'],
            embedding=embeddings[i].tolist() if embeddings[i] is not None else None
        )
        db.add(vehicle)

    db.commit()
    print(f"Successfully seeded {len(rows_processed)} vehicles using Adaptive Engine.")

def seed_articles(db: Session, force: bool = False):
    if not ARTICLES_DIR.exists():
        print(f"Error: Articles directory not found at {ARTICLES_DIR}")
        return

    if force:
        print("Clearing existing knowledge articles...")
        db.query(KnowledgeArticle).delete()
        db.commit()

    extensions = ("*.md", "*.txt")
    files = []
    for ext in extensions:
        files.extend(list(ARTICLES_DIR.glob(ext)))

    count = 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if len(content.strip().split('\n')) <= 1:
                continue

            title = path.stem.replace("_", " ").title()
            source = str(path.name)

            chunks = chunk_text(content, max_chars=1000)
            for idx, chunk in enumerate(chunks):
                embedding = embed_text(chunk)
                article = KnowledgeArticle(
                    title=f"{title} (part {idx+1})" if len(chunks) > 1 else title,
                    source=source,
                    content=chunk,
                    embedding=embedding,
                )
                db.add(article)
                count += 1
        except Exception as e:
            print(f"Error seeding article {path.name}: {e}")
            db.rollback()

    db.commit()
    print(f"Successfully seeded {count} article chunks.")

def main():
    parser = argparse.ArgumentParser(description="Unified Database Seeding Manager")
    parser.add_argument("--all", action="store_true", help="Seed everything")
    parser.add_argument("--vehicles", action="store_true", help="Seed vehicles only")
    parser.add_argument("--articles", action="store_true", help="Seed knowledge articles only")
    parser.add_argument("--force", action="store_true", help="Clear existing data before seeding")
    parser.add_argument("--init", action="store_true", help="Initialize tables before seeding")
    
    args = parser.parse_args()

    if args.init:
        print("Initializing database tables...")
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if args.all or args.vehicles:
            seed_vehicles(db, force=args.force)
        
        if args.all or args.articles:
            seed_articles(db, force=args.force)
            
        if not (args.all or args.vehicles or args.articles):
            parser.print_help()
    finally:
        db.close()

if __name__ == "__main__":
    main()
