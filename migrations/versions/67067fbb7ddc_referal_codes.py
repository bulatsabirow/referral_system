"""+ referal codes

Revision ID: 67067fbb7ddc
Revises: 4d3b17ef270b
Create Date: 2024-03-13 18:25:34.862654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67067fbb7ddc'
down_revision: Union[str, None] = '4d3b17ef270b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('referral_code',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('referrer_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
    sa.Column('expired_at', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['referrer_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('referral_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('referral_code_id', sa.Integer(), nullable=False),
    sa.Column('referral_id', sa.Integer(), nullable=False),
    sa.CheckConstraint('referral_code_id != referral_id', name='check_referral_and_referrer_and_not_the_same_person'),
    sa.ForeignKeyConstraint(['referral_code_id'], ['referral_code.id'], ),
    sa.ForeignKeyConstraint(['referral_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('referral_user')
    op.drop_table('referral_code')
    # ### end Alembic commands ###
