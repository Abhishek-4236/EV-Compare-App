import enum
from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base
from pgvector.sqlalchemy import Vector

EMBEDDING_DIM = 384


class VehicleSegment(str, enum.Enum):
    TWO_WHEELER = "TWO_WHEELER"
    THREE_WHEELER = "THREE_WHEELER"
    FOUR_WHEELER = "FOUR_WHEELER"
    TRUCK = "TRUCK"
    BUS = "BUS"

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    segment = Column(Enum(VehicleSegment, name="vehicle_segment"), nullable=False, default=VehicleSegment.FOUR_WHEELER)
    category = Column(String(10), nullable=False)
    wheel_type = Column(String(20))
    brand = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    approx_price_inr = Column(Integer, nullable=False)
    range_km = Column(Integer, nullable=False)
    battery_kwh = Column(Numeric(6, 2), nullable=False)
    top_speed_kmh = Column(Integer)
    motor_kw = Column(Numeric(6, 2))
    charging_time_ac_hrs = Column(Numeric(4, 1))
    charging_time_dc_min = Column(Integer)
    monthly_cost_inr = Column(Integer)
    safety_rating = Column(Integer)
    brake_type = Column(String(50))
    fame2_subsidy_inr = Column(Integer, default=0)
    state_subsidy_inr = Column(Integer, default=0)
    warranty_years = Column(Integer)
    ip_rating = Column(String(10))
    connected_features = Column(Boolean, default=False)
    regenerative_braking = Column(Boolean, default=False)
    overall_rating = Column(Numeric(3, 1))
    charging_type = Column(String(20))
    vehicle_type = Column(String(30))
    market_status = Column(String(20), default="Available")
    launch_year = Column(Integer)
    image_url = Column(Text)
    extra_info = Column(JSONB, nullable=True)
    embedding = Column(Vector(EMBEDDING_DIM))
    created_at = Column(TIMESTAMP, server_default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(200), default="New Chat")
    last_vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    expertise_level = Column(String(20), default="Novice")
    lessons_learned = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 = helpful, -1 = not helpful
    note = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    auth_provider = Column(String(30), nullable=False, default="email")
    role = Column(String(20), nullable=False, default="user") # user, admin, guest
    created_at = Column(TIMESTAMP, server_default=func.now())

class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(100))
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    address = Column(Text)
    connector_types = Column(String(255))
    fast_charging_available = Column(Boolean, default=False)
    power_kw = Column(Numeric(6, 2))
    status = Column(String(50), default="Operational")
    created_at = Column(TIMESTAMP, server_default=func.now())

class SavedComparison(Base):
    __tablename__ = "saved_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vehicle_ids = Column(String(255), nullable=False) # Store as comma-separated IDs
    name = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

class SubsidyRule(Base):
    __tablename__ = "subsidy_rules"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(50), nullable=False, index=True)
    segment = Column(String(50), nullable=False) # e.g. TWO_WHEELER
    subsidy_per_kwh = Column(Integer, default=0)
    max_subsidy = Column(Integer, default=0)
    flat_subsidy = Column(Integer, default=0)
    road_tax_waiver = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    source = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

