"""empty message

Revision ID: 07b5165f4e84
Revises: 
Create Date: 2022-06-28 16:14:01.535301

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07b5165f4e84'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tasks',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('execution_type', sa.Enum('once', 'periodic', name='executiontype'), server_default='once', nullable=False),
    sa.Column('status', sa.Enum('active', 'inactive', name='taskstatus'), server_default='active', nullable=False),
    sa.Column('sense_metric', sa.String(), nullable=True),
    sa.Column('sense_mode', sa.Enum('single', 'max', 'min', 'average', name='sensemode'), nullable=True),
    sa.Column('sense_sample_rate', sa.Float(), nullable=True),
    sa.Column('sense_n_samples', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('task_results',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('device_id', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'done', name='resultstatus'), server_default='pending', nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('task_results')
    op.drop_table('tasks')
    # ### end Alembic commands ###