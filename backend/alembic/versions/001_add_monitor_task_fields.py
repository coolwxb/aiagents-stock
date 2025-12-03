"""添加监控任务的进场区间、止盈止损和量化配置字段

Revision ID: 001
Revises: 
Create Date: 2025-12-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加新字段"""
    # 进场区间
    op.add_column('monitor_tasks', sa.Column('entry_min', sa.Float(), nullable=True))
    op.add_column('monitor_tasks', sa.Column('entry_max', sa.Float(), nullable=True))
    
    # 止盈止损
    op.add_column('monitor_tasks', sa.Column('take_profit', sa.Float(), nullable=True))
    op.add_column('monitor_tasks', sa.Column('stop_loss', sa.Float(), nullable=True))
    
    # 通知设置
    op.add_column('monitor_tasks', sa.Column('notification_enabled', sa.Boolean(), nullable=True, server_default='0'))
    
    # 量化配置（JSON格式存储）
    op.add_column('monitor_tasks', sa.Column('quant_config', sa.Text(), nullable=True))


def downgrade():
    """回滚删除字段"""
    op.drop_column('monitor_tasks', 'quant_config')
    op.drop_column('monitor_tasks', 'notification_enabled')
    op.drop_column('monitor_tasks', 'stop_loss')
    op.drop_column('monitor_tasks', 'take_profit')
    op.drop_column('monitor_tasks', 'entry_max')
    op.drop_column('monitor_tasks', 'entry_min')
