"""Initial application schema.

Revision ID: 20260628_0001
Revises:
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


revision = "20260628_0001"
down_revision = None
branch_labels = None
depends_on = None


vehicle_segment = postgresql.ENUM(
    "TWO_WHEELER",
    "THREE_WHEELER",
    "FOUR_WHEELER",
    "TRUCK",
    "BUS",
    name="vehicle_segment",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    vehicle_segment.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("auth_provider", sa.String(length=30), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("segment", vehicle_segment, nullable=False),
        sa.Column("category", sa.String(length=10), nullable=False),
        sa.Column("wheel_type", sa.String(length=20)),
        sa.Column("brand", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("approx_price_inr", sa.Integer(), nullable=False),
        sa.Column("range_km", sa.Integer(), nullable=False),
        sa.Column("battery_kwh", sa.Numeric(6, 2), nullable=False),
        sa.Column("top_speed_kmh", sa.Integer()),
        sa.Column("motor_kw", sa.Numeric(6, 2)),
        sa.Column("charging_time_ac_hrs", sa.Numeric(4, 1)),
        sa.Column("charging_time_dc_min", sa.Integer()),
        sa.Column("monthly_cost_inr", sa.Integer()),
        sa.Column("safety_rating", sa.Integer()),
        sa.Column("brake_type", sa.String(length=50)),
        sa.Column("fame2_subsidy_inr", sa.Integer()),
        sa.Column("state_subsidy_inr", sa.Integer()),
        sa.Column("warranty_years", sa.Integer()),
        sa.Column("ip_rating", sa.String(length=10)),
        sa.Column("connected_features", sa.Boolean()),
        sa.Column("regenerative_braking", sa.Boolean()),
        sa.Column("overall_rating", sa.Numeric(3, 1)),
        sa.Column("charging_type", sa.String(length=20)),
        sa.Column("vehicle_type", sa.String(length=30)),
        sa.Column("market_status", sa.String(length=20)),
        sa.Column("launch_year", sa.Integer()),
        sa.Column("image_url", sa.Text()),
        sa.Column("extra_info", postgresql.JSONB()),
        sa.Column("embedding", Vector(384)),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_vehicles_id"), "vehicles", ["id"], unique=False)

    op.create_table(
        "charging_stations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=100)),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("connector_types", sa.String(length=255)),
        sa.Column("fast_charging_available", sa.Boolean()),
        sa.Column("power_kw", sa.Numeric(6, 2)),
        sa.Column("status", sa.String(length=50)),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_charging_stations_id"), "charging_stations", ["id"], unique=False)

    op.create_table(
        "knowledge_articles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=255)),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384)),
    )
    op.create_index(op.f("ix_knowledge_articles_id"), "knowledge_articles", ["id"], unique=False)

    op.create_table(
        "subsidy_rules",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("segment", sa.String(length=50), nullable=False),
        sa.Column("subsidy_per_kwh", sa.Integer()),
        sa.Column("max_subsidy", sa.Integer()),
        sa.Column("flat_subsidy", sa.Integer()),
        sa.Column("road_tax_waiver", sa.Boolean()),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_subsidy_rules_id"), "subsidy_rules", ["id"], unique=False)
    op.create_index(op.f("ix_subsidy_rules_state"), "subsidy_rules", ["state"], unique=False)

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("title", sa.String(length=200)),
        sa.Column("last_vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id")),
        sa.Column("expertise_level", sa.String(length=20)),
        sa.Column("lessons_learned", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_chat_sessions_id"), "chat_sessions", ["id"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_chat_messages_id"), "chat_messages", ["id"], unique=False)
    op.create_index(op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"], unique=False)

    op.create_table(
        "chat_feedback",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_chat_feedback_id"), "chat_feedback", ["id"], unique=False)
    op.create_index(op.f("ix_chat_feedback_session_id"), "chat_feedback", ["session_id"], unique=False)

    op.create_table(
        "saved_comparisons",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vehicle_ids", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=100)),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_saved_comparisons_id"), "saved_comparisons", ["id"], unique=False)
    op.create_index(op.f("ix_saved_comparisons_user_id"), "saved_comparisons", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_saved_comparisons_user_id"), table_name="saved_comparisons")
    op.drop_index(op.f("ix_saved_comparisons_id"), table_name="saved_comparisons")
    op.drop_table("saved_comparisons")

    op.drop_index(op.f("ix_chat_feedback_session_id"), table_name="chat_feedback")
    op.drop_index(op.f("ix_chat_feedback_id"), table_name="chat_feedback")
    op.drop_table("chat_feedback")

    op.drop_index(op.f("ix_chat_messages_session_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_id"), table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index(op.f("ix_chat_sessions_id"), table_name="chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_index(op.f("ix_subsidy_rules_state"), table_name="subsidy_rules")
    op.drop_index(op.f("ix_subsidy_rules_id"), table_name="subsidy_rules")
    op.drop_table("subsidy_rules")

    op.drop_index(op.f("ix_knowledge_articles_id"), table_name="knowledge_articles")
    op.drop_table("knowledge_articles")

    op.drop_index(op.f("ix_charging_stations_id"), table_name="charging_stations")
    op.drop_table("charging_stations")

    op.drop_index(op.f("ix_vehicles_id"), table_name="vehicles")
    op.drop_table("vehicles")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    vehicle_segment.drop(op.get_bind(), checkfirst=True)
