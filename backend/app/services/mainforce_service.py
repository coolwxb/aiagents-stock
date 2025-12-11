#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股服务模块

注意：此模块依赖以下外部模块（需要从old目录迁移或实现）：
- main_force_selector: 主力资金数据选择器
- stock_data: 股票数据获取
- ai_agents: AI分析智能体
- deepseek_client: DeepSeek API客户端
"""

import asyncio
import time
import logging
import concurrent.futures
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.db.main_force_batch_db import MainForceBatchDatabase
from app.schemas.stock import (
    MainforceAnalyzeRequest,
    MainforceAnalyzeResponse,
    MainforceBatchAnalyzeRequest,
    MainforceBatchAnalyzeResponse
)

logger = logging.getLogger(__name__)


class MainforceService:
    """主力选股服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.batch_db = MainForceBatchDatabase()
    
    async def analyze_mainforce(self, request: MainforceAnalyzeRequest) -> MainforceAnalyzeResponse:
        """
        主力选股分析
        
        Args:
            request: 分析请求参数
            
        Returns:
            分析结果
        """
        try:
            # 在线程池中运行同步分析
            result = await asyncio.to_thread(
                self._run_mainforce_analysis,
                request
            )
            return result
        except Exception as e:
            logger.error(f"主力选股分析失败: {e}")
            return MainforceAnalyzeResponse(
                success=False,
                total_stocks=0,
                filtered_stocks=0,
                final_recommendations=[],
                params=request.model_dump(),
                error=str(e)
            )
    
    def _run_mainforce_analysis(self, request: MainforceAnalyzeRequest) -> MainforceAnalyzeResponse:
        """
        执行主力选股分析（同步）
        
        尝试从backend/app/services/mainforce目录导入分析器，
        如果失败则尝试从old目录导入
        """
        try:
            # 首先尝试从backend目录导入
            analyzer = None
            try:
                from app.services.mainforce.main_force_analysis import MainForceAnalyzer
                analyzer = MainForceAnalyzer(model=request.model)
                logger.info("使用backend目录的MainForceAnalyzer")
            except ImportError as e:
                logger.warning(f"无法从backend导入MainForceAnalyzer: {e}")
                
                # 尝试从old目录导入
                import sys
                import os
                old_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'old')
                if old_path not in sys.path:
                    sys.path.insert(0, old_path)
                
                try:
                    from main_force_analysis import MainForceAnalyzer
                    analyzer = MainForceAnalyzer(model=request.model)
                    logger.info("使用old目录的MainForceAnalyzer")
                except ImportError as e2:
                    logger.error(f"无法导入MainForceAnalyzer: {e2}")
                    return MainforceAnalyzeResponse(
                        success=False,
                        total_stocks=0,
                        filtered_stocks=0,
                        final_recommendations=[],
                        params=request.model_dump(),
                        error=f"分析模块未就绪: {e2}"
                    )
            
            # 运行分析
            result = analyzer.run_full_analysis(
                start_date=request.start_date,
                days_ago=request.days_ago,
                final_n=request.final_n,
                max_range_change=request.max_range_change,
                min_market_cap=request.min_market_cap,
                max_market_cap=request.max_market_cap
            )
            
            # 转换候选股票列表
            candidates = []
            if analyzer.raw_stocks is not None and not analyzer.raw_stocks.empty:
                for _, row in analyzer.raw_stocks.iterrows():
                    candidate = self._convert_stock_row(row)
                    candidates.append(candidate)
            
            # 转换推荐列表
            recommendations = []
            for rec in result.get('final_recommendations', []):
                recommendations.append({
                    'rank': rec.get('rank', 0),
                    'symbol': rec.get('symbol', ''),
                    'name': rec.get('name', ''),
                    'netInflow': self._get_net_inflow(rec.get('stock_data', {})),
                    'changePct': self._get_change_pct(rec.get('stock_data', {})),
                    'marketCap': self._get_market_cap(rec.get('stock_data', {})),
                    'reasons': rec.get('reasons', []),
                    'highlights': rec.get('highlights', ''),
                    'risks': rec.get('risks', ''),
                    'position': rec.get('position', ''),
                    'investmentPeriod': rec.get('investment_period', ''),
                    'tags': self._extract_tags(rec)
                })
            
            # 构建分析师报告
            analyst_reports = {
                'fund_flow': getattr(analyzer, 'fund_flow_analysis', '暂无分析'),
                'industry': getattr(analyzer, 'industry_analysis', '暂无分析'),
                'fundamental': getattr(analyzer, 'fundamental_analysis', '暂无分析')
            }
            
            return MainforceAnalyzeResponse(
                success=result.get('success', False),
                total_stocks=result.get('total_stocks', 0),
                filtered_stocks=result.get('filtered_stocks', 0),
                final_recommendations=recommendations,
                params={
                    **request.model_dump(),
                    'candidates': candidates,
                    'analyst_reports': analyst_reports,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                },
                error=result.get('error')
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return MainforceAnalyzeResponse(
                success=False,
                total_stocks=0,
                filtered_stocks=0,
                final_recommendations=[],
                params=request.model_dump(),
                error=str(e)
            )
    
    def _convert_stock_row(self, row) -> Dict[str, Any]:
        """转换股票行数据为前端格式"""
        result = {
            'symbol': str(row.get('股票代码', '')),
            'name': str(row.get('股票简称', ''))
        }
        
        # 行业
        for col in row.index:
            if '行业' in col:
                result['industry'] = str(row[col])
                break
        
        # 主力资金
        for col in row.index:
            if '主力' in col and ('净流入' in col or '流向' in col):
                try:
                    result['netInflow'] = float(row[col])
                except:
                    result['netInflow'] = 0
                break
        
        # 涨跌幅
        for col in row.index:
            if '涨跌幅' in col:
                try:
                    result['changePct'] = float(row[col])
                except:
                    result['changePct'] = 0
                break
        
        # 市值
        for col in row.index:
            if '总市值' in col:
                try:
                    val = float(row[col])
                    # 转换为亿
                    if val > 1e10:
                        val = val / 1e8
                    result['marketCap'] = val
                except:
                    result['marketCap'] = 0
                break
        
        # 市盈率
        for col in row.index:
            if '市盈率' in col:
                try:
                    result['pe'] = float(row[col])
                except:
                    result['pe'] = 0
                break
        
        # 市净率
        for col in row.index:
            if '市净率' in col:
                try:
                    result['pb'] = float(row[col])
                except:
                    result['pb'] = 0
                break
        
        return result
    
    def _get_net_inflow(self, stock_data: Dict) -> float:
        """获取主力净流入"""
        for key in stock_data:
            if '主力' in key and ('净流入' in key or '流向' in key):
                try:
                    return float(stock_data[key])
                except:
                    pass
        return 0
    
    def _get_change_pct(self, stock_data: Dict) -> float:
        """获取涨跌幅"""
        for key in stock_data:
            if '涨跌幅' in key:
                try:
                    return float(stock_data[key])
                except:
                    pass
        return 0
    
    def _get_market_cap(self, stock_data: Dict) -> float:
        """获取市值"""
        for key in stock_data:
            if '总市值' in key:
                try:
                    val = float(stock_data[key])
                    if val > 1e10:
                        val = val / 1e8
                    return val
                except:
                    pass
        return 0
    
    def _extract_tags(self, rec: Dict) -> List[str]:
        """提取标签"""
        tags = []
        stock_data = rec.get('stock_data', {})
        
        # 从行业提取
        for key in stock_data:
            if '行业' in key:
                industry = str(stock_data[key])
                if industry and industry != 'nan':
                    tags.append(industry)
                break
        
        return tags[:3]  # 最多3个标签
    
    async def batch_analyze(self, request: MainforceBatchAnalyzeRequest) -> MainforceBatchAnalyzeResponse:
        """
        批量分析
        
        Args:
            request: 批量分析请求
            
        Returns:
            批量分析结果
        """
        try:
            result = await asyncio.to_thread(
                self._run_batch_analysis,
                request
            )
            return result
        except Exception as e:
            return MainforceBatchAnalyzeResponse(
                total=len(request.stock_codes),
                success=0,
                failed=len(request.stock_codes),
                elapsed_time=0,
                analysis_mode=request.analysis_mode,
                results=[]
            )
    
    def _run_batch_analysis(self, request: MainforceBatchAnalyzeRequest) -> MainforceBatchAnalyzeResponse:
        """
        执行批量分析（同步）
        
        尝试导入分析函数，优先使用backend目录，失败则尝试old目录
        """
        start_time = time.time()
        results = []
        
        # 分析师配置
        enabled_analysts_config = {
            'technical': True,
            'fundamental': True,
            'fund_flow': True,
            'risk': True,
            'sentiment': False,
            'news': False
        }
        
        stock_codes = request.stock_codes
        analysis_mode = request.analysis_mode
        max_workers = request.max_workers
        selected_model = request.model
        
        # 尝试导入分析函数
        analyze_func = None
        
        # 首先尝试从backend导入（如果已实现）
        try:
            from app.services.stock_service import analyze_single_stock_for_batch
            analyze_func = analyze_single_stock_for_batch
            logger.info("使用backend目录的analyze_single_stock_for_batch")
        except ImportError:
            pass
        
        # 如果backend没有，尝试从old目录导入
        if analyze_func is None:
            try:
                import sys
                import os
                old_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'old')
                if old_path not in sys.path:
                    sys.path.insert(0, old_path)
                
                from app import analyze_single_stock_for_batch
                analyze_func = analyze_single_stock_for_batch
                logger.info("使用old目录的analyze_single_stock_for_batch")
            except ImportError as e:
                logger.error(f"无法导入analyze_single_stock_for_batch: {e}")
        
        # 如果都导入失败，返回错误
        if analyze_func is None:
            return MainforceBatchAnalyzeResponse(
                total=len(stock_codes),
                success=0,
                failed=len(stock_codes),
                elapsed_time=0,
                analysis_mode=analysis_mode,
                results=[{
                    'symbol': code,
                    'success': False,
                    'error': '分析模块未就绪，请确保相关依赖已安装'
                } for code in stock_codes]
            )
        
        if analysis_mode == "sequential":
            # 顺序分析
            for code in stock_codes:
                try:
                    result = analyze_func(
                        symbol=code,
                        period='1y',
                        enabled_analysts_config=enabled_analysts_config,
                        selected_model=selected_model
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"分析股票 {code} 失败: {e}")
                    results.append({
                        'symbol': code,
                        'success': False,
                        'error': str(e)
                    })
        else:
            # 并行分析
            def analyze_one(code):
                try:
                    return analyze_func(
                        symbol=code,
                        period='1y',
                        enabled_analysts_config=enabled_analysts_config,
                        selected_model=selected_model
                    )
                except Exception as e:
                    logger.error(f"分析股票 {code} 失败: {e}")
                    return {'symbol': code, 'success': False, 'error': str(e)}
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(analyze_one, code): code for code in stock_codes}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        code = futures[future]
                        results.append({'symbol': code, 'success': False, 'error': str(e)})
        
        elapsed_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get('success', False))
        failed_count = len(results) - success_count
        
        # 保存到历史记录
        try:
            self.batch_db.save_batch_analysis(
                batch_count=len(stock_codes),
                analysis_mode=analysis_mode,
                success_count=success_count,
                failed_count=failed_count,
                total_time=elapsed_time,
                results=results
            )
        except Exception as e:
            print(f"保存历史记录失败: {e}")
        
        return MainforceBatchAnalyzeResponse(
            total=len(results),
            success=success_count,
            failed=failed_count,
            elapsed_time=elapsed_time,
            analysis_mode=analysis_mode,
            results=results
        )
    
    async def get_history(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        获取历史记录
        
        Args:
            page: 页码
            page_size: 每页数量
            
        Returns:
            历史记录列表
        """
        try:
            # 获取所有历史记录
            all_history = self.batch_db.get_all_history(limit=100)
            
            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            items = all_history[start:end]
            
            # 转换格式
            formatted_items = []
            for item in items:
                formatted_items.append({
                    'id': item['id'],
                    'summary': f"分析了 {item['batch_count']} 只股票，成功 {item['success_count']} 只",
                    'range': item['analysis_date'],
                    'created_at': item['created_at'],
                    'success': item['success_count'],
                    'duration': f"{item['total_time']/60:.1f} 分钟",
                    'batch_count': item['batch_count'],
                    'analysis_mode': item['analysis_mode'],
                    'failed_count': item['failed_count'],
                    'total_time': item['total_time'],
                    'results': item.get('results', [])
                })
            
            # 获取统计信息
            stats = self.batch_db.get_statistics()
            
            return {
                'items': formatted_items,
                'total': len(all_history),
                'page': page,
                'page_size': page_size,
                'statistics': stats
            }
        except Exception as e:
            return {
                'items': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'error': str(e)
            }
    
    async def get_history_detail(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        获取历史记录详情
        
        Args:
            record_id: 记录ID
            
        Returns:
            记录详情
        """
        return self.batch_db.get_record_by_id(record_id)
    
    async def delete_history(self, record_id: int) -> bool:
        """
        删除历史记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否删除成功
        """
        return self.batch_db.delete_record(record_id)
