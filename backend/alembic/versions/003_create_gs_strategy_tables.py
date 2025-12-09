"""
创建GS策略相关表

Revision ID: 003
Revises: 002
Create Date: 2025-12-09
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """创建GS策略相关表"""
    # 创建股票池表
    op.create_table(
        'gs_stock_pool',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, comment='主键ID'),
        sa.Column('stock_code', sa.String(length=20), nullable=False, unique=True, comment='股票代码'),
        sa.Column('stock_name', sa.String(length=100), nullable=True, comment='股票名称'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    )
    op.create_index('ix_gs_stock_pool_id', 'gs_stock_pool', ['id'])
    op.create_index('ix_gs_stock_pool_stock_code', 'gs_stock_pool', ['stock_code'], unique=True)
    
    # 创建监控任务表
    op.create_table(
        'gs_monitor_tasks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, comment='主键ID'),
        sa.Column('stock_pool_id', sa.Integer(), sa.ForeignKey('gs_stock_pool.id'), nullable=True, comment='股票池ID'),
        sa.Column('stock_code', sa.String(length=20), nullable=False, comment='股票代码'),
        sa.Column('stock_name', sa.String(length=100), nullable=True, comment='股票名称'),
        sa.Column('interval', sa.Integer(), default=300, comment='监测间隔(秒)'),
        sa.Column('status', sa.String(length=20), default='stopped', comment='状态: running/stopped'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='监控启动时间'),
        sa.Column('execution_count', sa.Integer(), default=0, comment='策略执行次数'),
        sa.Column('last_signal', sa.String(length=20), nullable=True, comment='最后信号: buy/sell/hold'),
        sa.Column('last_signal_time', sa.DateTime(), nullable=True, comment='最后信号时间'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    )
    op.create_index('ix_gs_monitor_tasks_id', 'gs_monitor_tasks', ['id'])
    op.create_index('ix_gs_monitor_tasks_stock_code', 'gs_monitor_tasks', ['stock_code'])
    op.create_index('ix_gs_monitor_tasks_status', 'gs_monitor_tasks', ['status'])
    op.create_index('ix_gs_monitor_tasks_stock_status', 'gs_monitor_tasks', ['stock_code', 'status'])
    
    # 创建交易历史表
    op.create_table(
        'gs_trade_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, comment='主键ID'),
        sa.Column('monitor_id', sa.Integer(), sa.ForeignKey('gs_monitor_tasks.id'), nullable=True, comment='监控任务ID'),
        sa.Column('stock_code', sa.String(length=20), nullable=False, comment='股票代码'),
        sa.Column('stock_name', sa.String(length=100), nullable=True, comment='股票名称'),
        # 买入信息
        sa.Column('buy_price', sa.Float(), nullable=True, comment='买入价格'),
        sa.Column('buy_quantity', sa.Integer(), nullable=True, comment='买入数量'),
        sa.Column('buy_time', sa.DateTime(), nullable=True, comment='买入时间'),
        sa.Column('buy_order_id', sa.String(length=50), nullable=True, comment='买入订单ID'),
        # 卖出信息
        sa.Column('sell_price', sa.Float(), nullable=True, comment='卖出价格'),
        sa.Column('sell_quantity', sa.Integer(), nullable=True, comment='卖出数量'),
        sa.Column('sell_time', sa.DateTime(), nullable=True, comment='卖出时间'),
        sa.Column('sell_order_id', sa.String(length=50), nullable=True, comment='卖出订单ID'),
        # 盈亏信息
        sa.Column('profit_loss', sa.Float(), nullable=True, comment='盈亏金额'),
        sa.Column('profit_loss_pct', sa.Float(), nullable=True, comment='盈亏百分比'),
        # 状态
        sa.Column('status', sa.String(length=20), nullable=True, comment='状态: open(持仓中)/closed(已平仓)'),
        sa.Column('trade_details', sa.Text(), nullable=True, comment='交易详情(JSON格式)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    )
    op.create_index('ix_gs_trade_history_id', 'gs_trade_history', ['id'])
    op.create_index('ix_gs_trade_history_stock_code', 'gs_trade_history', ['stock_code'])


def downgrade():
    """删除GS策略相关表"""
    # 删除交易历史表
    op.drop_index('ix_gs_trade_history_stock_code', table_name='gs_trade_history')
    op.drop_index('ix_gs_trade_history_id', table_name='gs_trade_history')
    op.drop_table('gs_trade_history')
    
    # 删除监控任务表
    op.drop_index('ix_gs_monitor_tasks_stock_status', table_name='gs_monitor_tasks')
    op.drop_index('ix_gs_monitor_tasks_status', table_name='gs_monitor_tasks')
    op.drop_index('ix_gs_monitor_tasks_stock_code', table_name='gs_monitor_tasks')
    op.drop_index('ix_gs_monitor_tasks_id', table_name='gs_monitor_tasks')
    op.drop_table('gs_monitor_tasks')
    
    # 删除股票池表
    op.drop_index('ix_gs_stock_pool_stock_code', table_name='gs_stock_pool')
    op.drop_index('ix_gs_stock_pool_id', table_name='gs_stock_pool')
    op.drop_table('gs_stock_pool')
