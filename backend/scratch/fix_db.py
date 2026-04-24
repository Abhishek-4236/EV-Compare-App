from database import engine, Base
import models # Important to register models with Base

def recreate_vehicles():
    print("Dropping and recreating vehicles table...")
    # This will ensure the new column extra_info is created
    models.Vehicle.__table__.drop(engine, checkfirst=True)
    Base.metadata.create_all(bind=engine)
    print("[SUCCESS] Table 'vehicles' has been fresh recreated.")

if __name__ == "__main__":
    recreate_vehicles()
