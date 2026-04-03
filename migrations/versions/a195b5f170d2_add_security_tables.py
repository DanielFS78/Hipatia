"""add_security_tables

Revision ID: a195b5f170d2
Revises: c1444b2546d3
Create Date: 2026-02-15 15:13:38.733337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a195b5f170d2'
down_revision: Union[str, Sequence[str], None] = 'c1444b2546d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
