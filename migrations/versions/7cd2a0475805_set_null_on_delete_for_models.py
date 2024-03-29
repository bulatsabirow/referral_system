"""= Set null on delete for models

Revision ID: 7cd2a0475805
Revises: 615d01317a26
Create Date: 2024-03-14 14:24:46.077748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7cd2a0475805"
down_revision: Union[str, None] = "615d01317a26"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("referral_code", "referrer_id", existing_type=sa.INTEGER(), nullable=True)
    op.drop_constraint("referral_code_referrer_id_fkey", "referral_code", type_="foreignkey")
    op.create_foreign_key(None, "referral_code", "user", ["referrer_id"], ["id"], ondelete="SET NULL")
    op.drop_constraint("user_referrer_id_fkey", "user", type_="foreignkey")
    op.create_foreign_key(None, "user", "referral_code", ["referrer_id"], ["id"], ondelete="SET NULL")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "user", type_="foreignkey")
    op.create_foreign_key("user_referrer_id_fkey", "user", "referral_code", ["referrer_id"], ["id"])
    op.drop_constraint(None, "referral_code", type_="foreignkey")
    op.create_foreign_key("referral_code_referrer_id_fkey", "referral_code", "user", ["referrer_id"], ["id"])
    op.alter_column("referral_code", "referrer_id", existing_type=sa.INTEGER(), nullable=False)
    # ### end Alembic commands ###
