"""
添加监控任务策略字段

Revision ID: 002
Revises: 001
Create Date: 2025-12-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """添加strategy字段"""
    op.add_column(
        'monitor_tasks',
        sa.Column('strategy', sa.String(length=20), nullable=True, server_default='GS')
    )


def downgrade():
    """删除strategy字段"""
    op.drop_column('monitor_tasks', 'strategy')

