"""add apt_number column to address

Revision ID: 63f2cf46f7b9
Revises: 85d9d8d1fce6
Create Date: 2022-06-14 09:29:54.870707

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63f2cf46f7b9'
down_revision = '85d9d8d1fce6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('address', sa.Column('apt_number', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('address', 'apt_number')
