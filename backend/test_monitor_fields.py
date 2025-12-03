"""
测试监控任务创建和查询 - 验证所有字段保存成功
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.monitor_service import MonitorService

def test_create_and_query():
    """测试创建任务并查询所有字段"""
    db: Session = SessionLocal()
    
    try:
        service = MonitorService(db)
        
        # 1. 创建测试任务
        print("=" * 60)
        print("测试1: 创建监控任务")
        print("=" * 60)
        
        task_data = {
            'symbol': '600519.SH',
            'name': '贵州茅台',
            'status': 'running',
            'check_interval': 15,
            'entry_min': 1800.50,
            'entry_max': 1950.80,
            'take_profit': 2100.00,
            'stop_loss': 1750.00,
            'notification_enabled': True,
            'quant_enabled': True,
            'quant_config': {
                'max_position_pct': 20,
                'auto_stop_loss': True,
                'auto_take_profit': True
            }
        }
        
        print(f"\n发送数据:")
        print(json.dumps(task_data, indent=2, ensure_ascii=False))
        
        # 使用异步方法的同步调用
        import asyncio
        created_task = asyncio.run(service.create_task(task_data))
        
        print(f"\n✅ 任务创建成功！ID: {created_task['id']}")
        print(f"\n返回数据:")
        print(json.dumps(created_task, indent=2, ensure_ascii=False))
        
        # 2. 查询任务验证
        print("\n" + "=" * 60)
        print("测试2: 查询任务验证所有字段")
        print("=" * 60)
        
        tasks = asyncio.run(service.get_tasks())
        
        if tasks:
            latest_task = tasks[0]
            print(f"\n查询到的任务数据:")
            print(json.dumps(latest_task, indent=2, ensure_ascii=False))
            
            # 验证字段
            print("\n" + "=" * 60)
            print("字段验证:")
            print("=" * 60)
            
            checks = [
                ('股票代码', latest_task.get('stock_code'), '600519.SH'),
                ('股票名称', latest_task.get('stock_name'), '贵州茅台'),
                ('进场最低价', latest_task.get('entry_min'), 1800.50),
                ('进场最高价', latest_task.get('entry_max'), 1950.80),
                ('止盈价位', latest_task.get('take_profit'), 2100.00),
                ('止损价位', latest_task.get('stop_loss'), 1750.00),
                ('通知开关', latest_task.get('notification_enabled'), True),
                ('自动交易', latest_task.get('auto_trade'), True),
            ]
            
            all_pass = True
            for name, actual, expected in checks:
                status = "✅" if actual == expected else "❌"
                print(f"{status} {name}: {actual} (期望: {expected})")
                if actual != expected:
                    all_pass = False
            
            # 验证量化配置
            quant_config = latest_task.get('quant_config')
            if quant_config:
                print(f"✅ 量化配置: {json.dumps(quant_config, ensure_ascii=False)}")
                if (quant_config.get('max_position_pct') == 20 and
                    quant_config.get('auto_stop_loss') == True and
                    quant_config.get('auto_take_profit') == True):
                    print("  ✅ 量化配置所有字段正确")
                else:
                    print("  ❌ 量化配置字段不匹配")
                    all_pass = False
            else:
                print("❌ 量化配置: 未保存")
                all_pass = False
            
            print("\n" + "=" * 60)
            if all_pass:
                print("🎉 所有测试通过！前后端参数保存完整")
            else:
                print("⚠️  部分测试未通过，请检查上述标记")
            print("=" * 60)
        else:
            print("❌ 未查询到任务")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_create_and_query()
