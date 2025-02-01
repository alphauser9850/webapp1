"""Add name field to User model

Revision ID: 28ecbbb974e3
Revises: 64be6422aad9
Create Date: 2025-01-31 12:28:37.318042

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28ecbbb974e3'
down_revision = '64be6422aad9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('name')

    # ### end Alembic commands ###
