"""Added APIToken table

Revision ID: b02906dea3b0
Revises: 25cf8a00d471
Create Date: 2016-04-15 21:14:15.920732

"""

# revision identifiers, used by Alembic.
revision = 'b02906dea3b0'
down_revision = '25cf8a00d471'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tb_api_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('tb_user.id'), nullable=False),
    sa.Column('token', sa.String(length=255), nullable=False),
    sa.Column('salt', sa.String(length=32), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tb_api_tokens')
    ### end Alembic commands ###
