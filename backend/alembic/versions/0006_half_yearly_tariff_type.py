"""half-yearly tariff type

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-07 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enums are stored as VARCHAR + CHECK (native_enum=False), so a new value means a new CHECK
CONSTRAINT = 'tarifftype'
OLD_TYPES = ('single_visit', 'monthly', 'yearly', 'visit_pack')
NEW_TYPES = ('single_visit', 'monthly', 'half_yearly', 'yearly', 'visit_pack')


def _type_check(types: tuple[str, ...]) -> str:
    return 'type IN (' + ', '.join(f"'{t}'" for t in types) + ')'


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f('ck_tariff_plans_tarifftype'), 'tariff_plans', type_='check')
    op.create_check_constraint(CONSTRAINT, 'tariff_plans', _type_check(NEW_TYPES))


def downgrade() -> None:
    """Downgrade schema. Half-yearly tariffs (and their memberships) must be removed first."""
    op.drop_constraint(op.f('ck_tariff_plans_tarifftype'), 'tariff_plans', type_='check')
    op.create_check_constraint(CONSTRAINT, 'tariff_plans', _type_check(OLD_TYPES))
