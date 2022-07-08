"""create phone number column for users table

Revision ID: 249389166b0f
Revises: 
Create Date: 2022-06-14 07:59:34.491057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '249389166b0f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'phone_number')
