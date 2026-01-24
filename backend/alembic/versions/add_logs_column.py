"""Add logs to analysis_sessions

Revision ID: add_logs_column
Revises: 79f2c1963c5c
Create Date: 2026-01-24 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_logs_column'
down_revision: Union[str, None] = '79f2c1963c5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('analysis_sessions', sa.Column('logs', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('analysis_sessions', 'logs')
