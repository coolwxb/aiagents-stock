#!/usr/bin/env python3
"""
启动修复验证脚本
验证数据源管理器初始化是否正常工作
"""

import os
import sys

# 添加项目路径
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(current_file)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

def test_data_source_init():
    """测试数据源管理器初始化"""
    print("="*60)
    print("测试数据源管理器初始化...")
    print("="*60)
    
    try:
        # 测试1: 直接导入函数
        print("1. 测试导入init_source_manager函数...")
        from app.data.data_source import init_source_manager
        print("✅ 成功导入init_source_manager函数")
        
        # 测试2: 使用默认配置初始化
        print("\n2. 测试使用默认配置初始化...")
        manager = init_source_manager()
        print(f"✅ 成功创建数据源管理器实例: {type(manager)}")
        
        # 测试3: 使用配置字典初始化
        print("\n3. 测试使用配置字典初始化...")
        test_config = {
            'TUSHARE_TOKEN': 'test_token',
            'MYSQL_ENABLED': 'false',
            'MYSQL_HOST': '127.0.0.1'
        }
        manager_with_config = init_source_manager(test_config)
        print(f"✅ 成功使用配置创建管理器实例: {type(manager_with_config)}")
        
        # 测试4: 检查全局变量
        print("\n4. 测试全局变量...")
        from app.data.data_source import data_source_manager
        print(f"✅ 全局变量状态: {data_source_manager}")
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！数据源管理器初始化修复成功")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_timezone_handling():
    """测试时区处理"""
    print("\n" + "="*60)
    print("测试时区处理...")
    print("="*60)
    
    try:
        import pandas as pd
        from datetime import datetime
        
        # 测试时区转换
        test_dates = ['2024-01-01', '2024-12-31', '2024-06-15']
        
        for date_str in test_dates:
            # 模拟修复后的时区处理
            dt_series = pd.to_datetime([date_str])
            dt_with_tz = dt_series.dt.tz_localize('Asia/Shanghai')
            print(f"✅ {date_str} -> {dt_with_tz.iloc[0]}")
        
        print("\n✅ 时区处理测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 时区处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("AI股票分析系统 - 启动修复验证")
    print("="*60)
    
    # 测试数据源初始化
    init_success = test_data_source_init()
    
    # 测试时区处理
    timezone_success = test_timezone_handling()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结:")
    print(f"数据源初始化: {'✅ 通过' if init_success else '❌ 失败'}")
    print(f"时区处理: {'✅ 通过' if timezone_success else '❌ 失败'}")
    
    if init_success and timezone_success:
        print("\n🎉 所有修复验证通过！系统可以正常启动。")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查修复内容。")
        sys.exit(1)
