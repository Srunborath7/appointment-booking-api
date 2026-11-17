"""create_room_table

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-17 08:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rooms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('room_number', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('room_type', sa.String(length=50), server_default='consultation', nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('floor', sa.String(length=50), nullable=True),
        sa.Column('building', sa.String(length=100), nullable=True),
        sa.Column('capacity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='available', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rooms_room_number'), 'rooms', ['room_number'], unique=True)
    op.create_index(op.f('ix_rooms_room_type'), 'rooms', ['room_type'], unique=False)
    op.create_index(op.f('ix_rooms_department'), 'rooms', ['department'], unique=False)
    op.create_index(op.f('ix_rooms_status'), 'rooms', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_rooms_status'), table_name='rooms')
    op.drop_index(op.f('ix_rooms_department'), table_name='rooms')
    op.drop_index(op.f('ix_rooms_room_type'), table_name='rooms')
    op.drop_index(op.f('ix_rooms_room_number'), table_name='rooms')
    op.drop_table('rooms')
