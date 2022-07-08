"""create address to users

Revision ID: 85d9d8d1fce6
Revises: 751c5edb37fb
Create Date: 2022-06-14 08:28:23.155925

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '85d9d8d1fce6'
down_revision = '751c5edb37fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('address_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'address_users_fk',
        source_table='users',
        referent_table='address',
        local_cols=['address_id'],
        remote_cols=['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('address_users_fk', table_name='users')
    op.drop_column('users', 'address_id')
