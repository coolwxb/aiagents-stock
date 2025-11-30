"""
主力选股服务
"""
import asyncio
import json
import logging
import time
import sys
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from app.schemas.stock import (
    MainforceAnalyzeRequest,
    MainforceAnalyzeResponse,
    MainforceBatchAnalyzeRequest,
    MainforceBatchAnalyzeResponse
)

logger = logging.getLogger(__name__)


class MainforceService:
    """主力选股服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_mainforce(
        self, 
        request: MainforceAnalyzeRequest
    ) -> MainforceAnalyzeResponse:
        """主力选股分析"""
        try:
            # 在线程池中执行分析
            result = await asyncio.to_thread(
                self._run_mainforce_analysis,
                request
            )
            
            return MainforceAnalyzeResponse(**result)
            
        except Exception as e:
            logger.error(f"主力选股分析失败: {str(e)}", exc_info=True)
            return MainforceAnalyzeResponse(
                success=False,
                total_stocks=0,
                filtered_stocks=0,
                final_recommendations=[],
                params=request.dict(),
                error=str(e)
            )
    
    def _run_mainforce_analysis(self, request: MainforceAnalyzeRequest) -> Dict[str, Any]:
        """同步执行主力选股分析"""
        # 使用backend内部的主力选股分析器
        from app.services.mainforce_analyzer import MainForceAnalyzer
        
        analyzer = MainForceAnalyzer(model=request.model)
        
        result = analyzer.run_full_analysis(
            start_date=request.start_date,
            days_ago=request.days_ago,
            final_n=request.final_n,
            max_range_change=request.max_range_change,
            min_market_cap=request.min_market_cap,
            max_market_cap=request.max_market_cap
        )
        
        return result
    
    async def batch_analyze(
        self,
        request: MainforceBatchAnalyzeRequest
    ) -> MainforceBatchAnalyzeResponse:
        """批量分析"""
        if not request.stock_codes:
            raise ValueError("stock_codes 不能为空")
        
        try:
            # 在线程池中执行批量分析
            result = await asyncio.to_thread(
                self._run_batch_analysis,
                request
            )
            
            # 保存到历史记录
            try:
                await asyncio.to_thread(
                    self._save_batch_history,
                    request,
                    result
                )
            except Exception as e:
                logger.warning(f"保存批量分析历史失败: {str(e)}")
            
            return MainforceBatchAnalyzeResponse(**result)
            
        except Exception as e:
            logger.error(f"批量分析失败: {str(e)}", exc_info=True)
            raise
    
    def _run_batch_analysis(self, request: MainforceBatchAnalyzeRequest) -> Dict[str, Any]:
        """同步执行批量分析"""
        # 临时添加项目根目录到路径
        project_root = Path(__file__).parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # 导入统一分析函数（位于项目根目录app.py）
        from app import analyze_single_stock_for_batch
        
        # 配置分析师参数
        enabled_analysts_config = {
            'technical': True,
            'fundamental': True,
            'fund_flow': True,
            'risk': True,
            'sentiment': False,
            'news': False
        }
        
        results = []
        start_time = time.time()
        
        if request.analysis_mode == "sequential":
            # 顺序分析
            for code in request.stock_codes:
                try:
                    result = analyze_single_stock_for_batch(
                        symbol=code,
                        period='1y',
                        enabled_analysts_config=enabled_analysts_config,
                        selected_model=request.model
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"分析 {code} 失败: {str(e)}")
                    results.append({
                        "symbol": code,
                        "success": False,
                        "error": str(e)
                    })
        else:
            # 并行分析
            def analyze_one(code):
                try:
                    return analyze_single_stock_for_batch(
                        symbol=code,
                        period='1y',
                        enabled_analysts_config=enabled_analysts_config,
                        selected_model=request.model
                    )
                except Exception as e:
                    logger.error(f"分析 {code} 失败: {str(e)}")
                    return {"symbol": code, "success": False, "error": str(e)}
            
            with ThreadPoolExecutor(max_workers=request.max_workers) as executor:
                futures = {executor.submit(analyze_one, code): code for code in request.stock_codes}
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        code = futures[future]
                        logger.error(f"获取结果失败 {code}: {str(e)}")
                        results.append({"symbol": code, "success": False, "error": str(e)})
        
        elapsed_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get("success", False))
        failed_count = len(results) - success_count
        
        return {
            "total": len(request.stock_codes),
            "success": success_count,
            "failed": failed_count,
            "elapsed_time": elapsed_time,
            "analysis_mode": request.analysis_mode,
            "results": results
        }
    
    def _save_batch_history(
        self,
        request: MainforceBatchAnalyzeRequest,
        result: Dict[str, Any]
    ):
        """保存批量分析历史"""
        try:
            # 使用backend内部的批量分析数据库模块
            from app.db.mainforce_batch_db import batch_db
            
            batch_db.save_batch_analysis(
                batch_count=result['total'],
                analysis_mode=result['analysis_mode'],
                success_count=result['success'],
                failed_count=result['failed'],
                total_time=result['elapsed_time'],
                results=result['results']
            )
        except Exception as e:
            logger.error(f"保存批量分析历史失败: {str(e)}", exc_info=True)
            raise
    
    async def get_history(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """历史记录"""
        try:
            # 使用backend内部的批量分析数据库模块
            from app.db.mainforce_batch_db import batch_db
            
            # 在线程池中执行
            history = await asyncio.to_thread(
                batch_db.get_all_history,
                limit=page_size
            )
            
            # 简单分页（数据库已按created_at DESC排序）
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            items = history[start_idx:end_idx]
            
            return {
                "total": len(history),
                "page": page,
                "page_size": page_size,
                "items": items
            }
        except Exception as e:
            logger.error(f"获取历史记录失败: {str(e)}", exc_info=True)
            raise

