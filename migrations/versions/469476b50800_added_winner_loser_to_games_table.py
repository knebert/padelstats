"""added winner, loser to games table

Revision ID: 469476b50800
Revises: 2cc4f3daac97
Create Date: 2019-08-10 14:17:13.452345

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '469476b50800'
down_revision = '2cc4f3daac97'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game', sa.Column('loser_team_id', sa.Integer(), nullable=True))
    op.add_column('game', sa.Column('winner_team_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'game', 'team', ['loser_team_id'], ['id'])
    op.create_foreign_key(None, 'game', 'team', ['winner_team_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'game', type_='foreignkey')
    op.drop_constraint(None, 'game', type_='foreignkey')
    op.drop_column('game', 'winner_team_id')
    op.drop_column('game', 'loser_team_id')
    # ### end Alembic commands ###