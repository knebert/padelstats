"""players and teams table

Revision ID: c268d12a73ce
Revises: 
Create Date: 2019-08-01 13:45:04.719490

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c268d12a73ce'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('player',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('firstname', sa.String(length=32), nullable=True),
    sa.Column('lastname', sa.String(length=32), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_firstname'), 'player', ['firstname'], unique=False)
    op.create_index(op.f('ix_player_lastname'), 'player', ['lastname'], unique=False)
    op.create_table('team',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('teamname', sa.String(length=64), nullable=True),
    sa.Column('player1_id', sa.Integer(), nullable=True),
    sa.Column('player2_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['player1_id'], ['player.id'], ),
    sa.ForeignKeyConstraint(['player2_id'], ['player.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_teamname'), 'team', ['teamname'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_team_teamname'), table_name='team')
    op.drop_table('team')
    op.drop_index(op.f('ix_player_lastname'), table_name='player')
    op.drop_index(op.f('ix_player_firstname'), table_name='player')
    op.drop_table('player')
    # ### end Alembic commands ###
