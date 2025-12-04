"""
QMT服务测试脚本
验证QMT交易接口功能（从数据库加载配置）
"""
import sys
import os

# 添加backend路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 添加项目根目录到路径（用于导入xtquant）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.services.qmt_service import qmt_service
from app.database import SessionLocal

def test_qmt_service():
    """测试QMT服务"""
    print("=" * 60)
    print("QMT服务测试（从数据库加载配置）")
    print("=" * 60)
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 1. 加载配置
        print("\n[1] 从数据库加载QMT配置:")
        qmt_service.load_config(db)
        print(f"  - MINIQMT_ENABLED: {qmt_service.enabled}")
        print(f"  - MINIQMT_ACCOUNT_ID: {qmt_service.account_id}")
        print(f"  - MINIQMT_ACCOUNT_TYPE: {qmt_service.account_type}")
        print(f"  - MINIQMT_USERDATA_PATH: {qmt_service.userdata_path}")
        
        # 2. 检查服务状态
        print("\n[2] 服务状态:")
        print(f"  - QMT启用: {qmt_service.enabled}")
        print(f"  - 连接状态: {qmt_service.is_connected()}")
        
        # 3. 尝试连接（如果启用）
        if qmt_service.enabled:
            print("\n[3] 尝试连接QMT:")
            success, msg = qmt_service.connect()
            print(f"  - 连接结果: {success}")
            print(f"  - 消息: {msg}")
            
            if success:
                # 4. 获取账户信息
                print("\n[4] 账户信息:")
                account_info = qmt_service.get_account_info()
                for key, value in account_info.items():
                    print(f"  - {key}: {value}")
                
                # 5. 获取持仓
                print("\n[5] 持仓信息:")
                positions = qmt_service.get_all_positions()
                print(f"  - 持仓数量: {len(positions)}")
                if positions:
                    for idx, pos in enumerate(positions[:3], 1):  # 只显示前3个
                        print(f"\n  持仓 {idx}:")
                        print(f"    股票代码: {pos.get('stock_code')}")
                        print(f"    股票名称: {pos.get('stock_name')}")
                        print(f"    持仓数量: {pos.get('quantity')}")
                        print(f"    成本价: {pos.get('cost_price'):.2f}")
                        print(f"    当前价: {pos.get('current_price'):.2f}")
                        print(f"    盈亏: {pos.get('profit_loss'):.2f}")
                        print(f"    盈亏率: {pos.get('profit_loss_pct'):.2f}%")
        else:
            print("\n[3] QMT未启用，跳过连接测试")
            print("\n提示: 要启用QMT，请在【环境配置】页面中设置:")
            print("  1. 启用MiniQMT量化交易 = True")
            print("  2. MiniQMT账户ID = 你的账户ID")
            print("  3. MiniQMT用户数据目录 = QMT用户数据路径")
        
        # 6. 测试模拟模式
        print("\n[6] 模拟模式测试:")
        account_info = qmt_service.get_account_info()
        print(f"  - 连接状态: {account_info.get('connected')}")
        print(f"  - 可用资金: {account_info.get('available_cash')}")
        print(f"  - 总资产: {account_info.get('total_value')}")
        
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_qmt_service()
