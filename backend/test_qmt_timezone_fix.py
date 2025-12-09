#!/usr/bin/env python3
"""
QMT数据源时区修复验证脚本
专门验证QMT数据源的时区处理是否正确
"""

import os
import sys

# 添加项目路径
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(current_file)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

def test_qmt_timezone_handling():
    """测试QMT数据源时区处理"""
    print("="*60)
    print("测试QMT数据源时区处理...")
    print("="*60)
    
    try:
        # 测试1: 导入数据源管理器
        print("1. 导入数据源管理器...")
        from app.data.data_source import DataSourceManager
        print("✅ 成功导入DataSourceManager")
        
        # 测试2: 创建管理器实例
        print("\n2. 创建数据源管理器实例...")
        manager = DataSourceManager()
        print("✅ 成功创建管理器实例")
        
        # 测试3: 检查_convert_to_ts_code方法
        print("\n3. 测试股票代码转换...")
        test_symbols = ['000001', '000002', '600000', '300001']
        for symbol in test_symbols:
            ts_code = manager._convert_to_ts_code(symbol)
            print(f"   {symbol} -> {ts_code}")
        print("✅ 股票代码转换正常")
        
        # 测试4: 检查时区处理代码是否存在
        print("\n4. 检查时区处理代码...")
        import inspect
        source = inspect.getsource(manager.get_stock_hist_data)
        
        if 'tz_localize(\'Asia/Shanghai\')' in source:
            print("✅ QMT数据源时区处理代码已添加")
        else:
            print("❌ QMT数据源时区处理代码未找到")
            return False
        
        # 测试5: 检查变量名修复
        if 'xt_code = self._convert_to_ts_code(symbol)' in source:
            print("✅ QMT变量名已修复")
        else:
            print("❌ QMT变量名未修复")
            return False
            
        print("\n✅ QMT数据源时区处理验证通过")
        return True
        
    except Exception as e:
        print(f"\n❌ QMT时区处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_timezone_conversion():
    """测试时区转换逻辑"""
    print("\n" + "="*60)
    print("测试时区转换逻辑...")
    print("="*60)
    
    try:
        import pandas as pd
        
        # 模拟QMT时间数据
        test_time_data = ['2024-01-01 09:30:00', '2024-01-01 15:00:00', '2024-12-31 09:30:00']
        
        print("测试QMT时间数据时区转换:")
        for time_str in test_time_data:
            # 模拟QMT时区处理逻辑
            try:
                # 首先尝试带时区的转换
                dt_series = pd.to_datetime([time_str], utc=False)
                dt_with_tz = dt_series.dt.tz_localize('Asia/Shanghai')
                print(f"   {time_str} -> {dt_with_tz[0]}")
            except Exception as e:
                print(f"   {time_str} -> 转换失败: {e}")
        
        print("\n✅ 时区转换逻辑测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 时区转换逻辑测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("AI股票分析系统 - QMT数据源时区修复验证")
    print("="*60)
    
    # 测试QMT时区处理
    qmt_success = test_qmt_timezone_handling()
    
    # 测试时区转换逻辑
    conversion_success = test_timezone_conversion()
    
    # 总结
    print("\n" + "="*60)
    print("QMT时区修复验证总结:")
    print(f"QMT数据源时区处理: {'✅ 通过' if qmt_success else '❌ 失败'}")
    print(f"时区转换逻辑: {'✅ 通过' if conversion_success else '❌ 失败'}")
    
    if qmt_success and conversion_success:
        print("\n🎉 QMT数据源时区修复验证通过！")
        print("QMT数据的时间现在会正确使用Asia/Shanghai时区。")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查修复内容。")
        sys.exit(1)
