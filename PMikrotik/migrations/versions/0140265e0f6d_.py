"""empty message

Revision ID: 0140265e0f6d
Revises: af28933928df
Create Date: 2023-11-06 18:55:35.689546

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0140265e0f6d'
down_revision = 'af28933928df'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('white_list')
    op.drop_table('black_list')
    op.drop_table('address')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('address',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('ip', sa.VARCHAR(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('black_list',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('ip', sa.VARCHAR(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('white_list',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('ip', sa.VARCHAR(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
