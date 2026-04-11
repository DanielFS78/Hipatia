"""
Nombre del Módulo: migrations.versions.a195b5f170d2_add_security_tables

Descripción: Funciones puras de apoyo (sin estado de proceso): ``upgrade``, ``downgrade``. Integración típica con: ``alembic``, ``sqlalchemy``.
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
