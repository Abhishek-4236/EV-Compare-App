from database import SessionLocal
from models import Vehicle
from embeddings import embed_text, vehicle_to_text

db = SessionLocal()

try:
    vehicles = db.query(Vehicle).all()
    updated = 0
    for v in vehicles:
        try:
            v.embedding = embed_text(vehicle_to_text(v))
            updated += 1
        except Exception:
            v.embedding = None
    db.commit()
    print(f"Updated embeddings for {updated} vehicles.")
finally:
    db.close()
