"""empty message

Revision ID: af28933928df
Revises: 
Create Date: 2023-09-29 09:51:39.267063

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af28933928df'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('adress')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('adress',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('ip', sa.VARCHAR(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
