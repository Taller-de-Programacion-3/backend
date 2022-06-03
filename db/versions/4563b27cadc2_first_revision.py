"""First revision

Revision ID: 4563b27cadc2
Revises:
Create Date: 2022-06-02 22:59:27.484692

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4563b27cadc2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tasks',
        sa.Column('name', sa.TEXT)
    )


def downgrade():
    op.drop_table('tasks')
