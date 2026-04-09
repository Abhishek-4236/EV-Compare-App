from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from database import Base
from pgvector.sqlalchemy import Vector

EMBEDDING_DIM = 384

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
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
    embedding = Column(Vector(EMBEDDING_DIM))
    created_at = Column(TIMESTAMP, server_default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, index=True)
    last_vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
