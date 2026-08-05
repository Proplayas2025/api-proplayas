"""rename research_work to research_line, drop duplicate node_members columns

Revision ID: b454f3accad1
Revises: 55ede1e8efab
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b454f3accad1'
down_revision: Union[str, None] = '55ede1e8efab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'research_work', new_column_name='research_line')

    # `node_members.research_line`/`work_area` eran copias de `users.research_line`/
    # `users.expertise_area` tomadas solo al registrar al miembro; se desincronizaban
    # si el usuario editaba su perfil después. Ahora se lee siempre desde `users`.
    op.drop_column('node_members', 'research_line')
    op.drop_column('node_members', 'work_area')


def downgrade() -> None:
    op.add_column('node_members', sa.Column('work_area', sa.String(length=255), nullable=True))
    op.add_column('node_members', sa.Column('research_line', sa.Text(), nullable=True))

    op.alter_column('users', 'research_line', new_column_name='research_work')
