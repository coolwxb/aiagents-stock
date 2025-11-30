#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend API接口测试脚本
测试迁移后的各个API接口功能
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:9529"
API_PREFIX = "/api/v1"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_prefix = API_PREFIX
        self.passed = 0
        self.failed = 0
        
    def test_api(self, name, method, endpoint, data=None, expected_code=200):
        """测试API接口"""
        url = f"{self.base_url}{endpoint}"
        print(f"\n{'='*80}")
        print(f"测试: {name}")
        print(f"URL: {url}")
        print(f"方法: {method}")
        
        try:
            if method == "GET":
                response = requests.get(url, params=data, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            else:
                print(f"❌ 不支持的方法: {method}")
                self.failed += 1
                return False
            
            print(f"状态码: {response.status_code}")
            
            # 解析响应
            try:
                resp_data = response.json()
                print(f"响应数据: {json.dumps(resp_data, ensure_ascii=False, indent=2)[:500]}...")
            except:
                print(f"响应内容: {response.text[:200]}...")
                resp_data = {}
            
            # 检查状态码
            if response.status_code == expected_code:
                # 检查响应格式
                if isinstance(resp_data, dict) and 'code' in resp_data:
                    if resp_data['code'] == 200:
                        print(f"✅ 测试通过")
                        self.passed += 1
                        return True
                    else:
                        print(f"⚠️ 业务错误: {resp_data.get('msg', '未知错误')}")
                        self.failed += 1
                        return False
                else:
                    print(f"✅ 测试通过（非标准响应格式）")
                    self.passed += 1
                    return True
            else:
                print(f"❌ 状态码不匹配，期望: {expected_code}")
                self.failed += 1
                return False
                
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时")
            self.failed += 1
            return False
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            self.failed += 1
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("开始测试Backend API接口")
        print("="*80)
        
        # 1. 测试根路径和健康检查
        self.test_api("根路径", "GET", "/")
        self.test_api("健康检查", "GET", "/health")
        
        # 2. 测试股票分析API
        print("\n\n" + "="*80)
        print("📈 股票分析模块测试")
        print("="*80)
        
        # 获取股票信息
        self.test_api(
            "获取股票信息",
            "GET",
            f"{API_PREFIX}/stock/info/000001"
        )
        
        # 3. 测试主力选股API
        print("\n\n" + "="*80)
        print("💰 主力选股模块测试")
        print("="*80)
        
        # 获取历史记录
        self.test_api(
            "获取主力选股历史记录",
            "GET",
            f"{API_PREFIX}/mainforce/history"
        )
        
        # 主力选股分析（简化参数）
        self.test_api(
            "主力选股分析",
            "POST",
            f"{API_PREFIX}/mainforce/analyze",
            data={
                "days_ago": 30,
                "final_n": 3,
                "max_range_change": 30.0,
                "min_market_cap": 50.0,
                "max_market_cap": 5000.0,
                "model": "deepseek-chat"
            }
        )
        
        # 4. 测试龙虎榜API
        print("\n\n" + "="*80)
        print("🐉 龙虎榜模块测试")
        print("="*80)
        
        # 获取龙虎榜历史
        self.test_api(
            "获取龙虎榜历史记录",
            "GET",
            f"{API_PREFIX}/longhubang/history"
        )
        
        # 5. 测试板块策略API
        print("\n\n" + "="*80)
        print("📊 板块策略模块测试")
        print("="*80)
        
        # 获取板块策略历史
        self.test_api(
            "获取板块策略历史记录",
            "GET",
            f"{API_PREFIX}/sector/history"
        )
        
        # 6. 测试监控API
        print("\n\n" + "="*80)
        print("👀 监控模块测试")
        print("="*80)
        
        # 获取监控任务列表
        self.test_api(
            "获取监控任务列表",
            "GET",
            f"{API_PREFIX}/monitor/tasks"
        )
        
        # 7. 测试组合管理API
        print("\n\n" + "="*80)
        print("💼 组合管理模块测试")
        print("="*80)
        
        # 获取组合列表
        self.test_api(
            "获取组合列表",
            "GET",
            f"{API_PREFIX}/portfolio/list"
        )
        
        # 8. 打印测试总结
        print("\n\n" + "="*80)
        print("📊 测试总结")
        print("="*80)
        print(f"✅ 通过: {self.passed}")
        print(f"❌ 失败: {self.failed}")
        print(f"总计: {self.passed + self.failed}")
        print(f"通过率: {self.passed/(self.passed+self.failed)*100:.1f}%")
        print("="*80 + "\n")
        
        return self.passed, self.failed


if __name__ == "__main__":
    tester = APITester()
    passed, failed = tester.run_all_tests()
    
    # 返回退出码
    exit(0 if failed == 0 else 1)
