"""Create subscription and notification

Revision ID: afef77490ce3
Revises: 
Create Date: 2022-06-30 22:15:56.266140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afef77490ce3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notifications',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('order_ref', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('subscriptions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('price_threshold', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('subscriptions')
    op.drop_table('notifications')
    # ### end Alembic commands ###
