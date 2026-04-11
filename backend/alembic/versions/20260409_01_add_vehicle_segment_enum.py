"""add vehicle segment enum column

Revision ID: 20260409_01
Revises:
Create Date: 2026-04-09 23:25:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260409_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


vehicle_segment_enum = sa.Enum(
    "TWO_WHEELER",
    "THREE_WHEELER",
    "FOUR_WHEELER",
    "TRUCK",
    "BUS",
    name="vehicle_segment",
)


def upgrade() -> None:
    bind = op.get_bind()
    vehicle_segment_enum.create(bind, checkfirst=True)
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("vehicles")}

    if "segment" not in columns:
        op.add_column(
            "vehicles",
            sa.Column("segment", vehicle_segment_enum, nullable=True),
        )

    op.execute(
        """
        UPDATE vehicles
        SET segment = CASE
            WHEN lower(category) = '2w' THEN 'TWO_WHEELER'::vehicle_segment
            WHEN lower(category) = '3w' THEN 'THREE_WHEELER'::vehicle_segment
            WHEN lower(category) = '4w' THEN 'FOUR_WHEELER'::vehicle_segment
            WHEN lower(category) = 'truck' THEN 'TRUCK'::vehicle_segment
            WHEN lower(category) = 'bus' THEN 'BUS'::vehicle_segment
            ELSE 'FOUR_WHEELER'::vehicle_segment
        END
        WHERE segment IS NULL
        """
    )

    op.alter_column(
        "vehicles",
        "segment",
        existing_type=vehicle_segment_enum,
        nullable=False,
        server_default="FOUR_WHEELER",
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("vehicles")}
    if "segment" in columns:
        op.drop_column("vehicles", "segment")
    vehicle_segment_enum.drop(bind, checkfirst=True)
