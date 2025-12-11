"""
智策板块服务
整合数据获取、AI分析、定时任务和历史报告管理
"""
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

# 添加old目录到路径以导入原有模块
OLD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'old')
if OLD_PATH not in sys.path:
    sys.path.insert(0, OLD_PATH)

logger = logging.getLogger(__name__)


class SectorService:
    """智策板块服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self._data_fetcher = None
        self._engine = None
        self._scheduler = None
        self._database = None
    
    @property
    def data_fetcher(self):
        """延迟加载数据获取器"""
        if self._data_fetcher is None:
            try:
                # 优先尝试从backend/app/data导入
                from app.data.sector_strategy_data import SectorStrategyDataFetcher
                self._data_fetcher = SectorStrategyDataFetcher()
            except ImportError:
                try:
                    # 回退到old目录
                    from sector_strategy_data import SectorStrategyDataFetcher
                    self._data_fetcher = SectorStrategyDataFetcher()
                except ImportError as e:
                    logger.error(f"导入SectorStrategyDataFetcher失败: {e}")
                    raise
        return self._data_fetcher
    
    @property
    def engine(self):
        """延迟加载分析引擎"""
        if self._engine is None:
            try:
                # 优先尝试从backend/app/services/sector导入
                from app.services.sector.sector_strategy_engine import SectorStrategyEngine
                self._engine = SectorStrategyEngine()
            except ImportError:
                try:
                    # 回退到old目录
                    from sector_strategy_engine import SectorStrategyEngine
                    self._engine = SectorStrategyEngine()
                except ImportError as e:
                    logger.error(f"导入SectorStrategyEngine失败: {e}")
                    raise
        return self._engine
    
    @property
    def scheduler(self):
        """延迟加载调度器"""
        if self._scheduler is None:
            try:
                # 优先尝试从backend/app/services/sector导入
                from app.services.sector.sector_strategy_scheduler import sector_strategy_scheduler
                self._scheduler = sector_strategy_scheduler
            except ImportError:
                try:
                    # 回退到old目录
                    from sector_strategy_scheduler import sector_strategy_scheduler
                    self._scheduler = sector_strategy_scheduler
                except ImportError as e:
                    logger.error(f"导入sector_strategy_scheduler失败: {e}")
                    raise
        return self._scheduler
    
    @property
    def database(self):
        """延迟加载数据库"""
        if self._database is None:
            try:
                from app.db.sector_db import SectorStrategyDatabase
                self._database = SectorStrategyDatabase()
            except ImportError as e:
                logger.error(f"导入SectorStrategyDatabase失败: {e}")
                raise
        return self._database
    
    async def analyze_sector(self, model: str = "deepseek-chat") -> Dict[str, Any]:
        """
        执行板块分析
        
        Args:
            model: AI模型名称
            
        Returns:
            分析结果字典
        """
        try:
            logger.info(f"[智策服务] 开始板块分析，模型: {model}")
            
            # 1. 获取数据（带缓存回退）
            data = self.data_fetcher.get_cached_data_with_fallback()
            
            if not data.get("success"):
                return {
                    "success": False,
                    "error": data.get("error", "数据获取失败"),
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # 2. 创建引擎并运行分析
            try:
                from app.services.sector.sector_strategy_engine import SectorStrategyEngine
                engine = SectorStrategyEngine(model=model)
            except ImportError:
                try:
                    from sector_strategy_engine import SectorStrategyEngine
                    engine = SectorStrategyEngine(model=model)
                except ImportError:
                    engine = self.engine
            
            result = engine.run_comprehensive_analysis(data)
            
            # 3. 添加缓存元信息
            if data.get("from_cache") or data.get("cache_warning"):
                result["cache_meta"] = {
                    "from_cache": bool(data.get("from_cache")),
                    "cache_warning": data.get("cache_warning", ""),
                    "data_timestamp": data.get("timestamp")
                }
            
            # 4. 添加数据摘要供前端展示
            result["data_summary"] = {
                "market_overview": data.get("market_overview", {}),
                "sectors_count": len(data.get("sectors", {})),
                "concepts_count": len(data.get("concepts", {}))
            }
            
            logger.info(f"[智策服务] 板块分析完成，成功: {result.get('success')}")
            return result
            
        except Exception as e:
            logger.error(f"[智策服务] 板块分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    async def get_schedule(self) -> Dict[str, Any]:
        """
        获取定时任务状态
        
        Returns:
            定时任务状态字典
        """
        try:
            status = self.scheduler.get_status()
            return {
                "enabled": status.get("running", False),
                "time": status.get("schedule_time", "09:00"),
                "notifyEmail": True,  # 默认开启邮件通知
                "nextRun": status.get("next_run_time", ""),
                "lastRun": status.get("last_run_time", "")
            }
        except Exception as e:
            logger.error(f"[智策服务] 获取定时任务状态失败: {e}")
            return {
                "enabled": False,
                "time": "09:00",
                "notifyEmail": True,
                "nextRun": "",
                "lastRun": ""
            }
    
    async def set_schedule(self, schedule_time: str, enabled: bool = True) -> Dict[str, Any]:
        """
        设置定时任务
        
        Args:
            schedule_time: 定时时间，格式 "HH:MM"
            enabled: 是否启用
            
        Returns:
            操作结果
        """
        try:
            if enabled:
                success = self.scheduler.start(schedule_time)
                if success:
                    logger.info(f"[智策服务] 定时任务已启动: {schedule_time}")
                    return {"success": True, "message": f"定时任务已启动，每天 {schedule_time} 运行"}
                else:
                    return {"success": False, "message": "定时任务启动失败，可能已在运行中"}
            else:
                success = self.scheduler.stop()
                if success:
                    logger.info("[智策服务] 定时任务已停止")
                    return {"success": True, "message": "定时任务已停止"}
                else:
                    return {"success": False, "message": "定时任务停止失败"}
        except Exception as e:
            logger.error(f"[智策服务] 设置定时任务失败: {e}")
            return {"success": False, "message": str(e)}
    
    async def delete_schedule(self, schedule_id: int) -> Dict[str, Any]:
        """
        删除定时任务（停止调度器）
        
        Args:
            schedule_id: 任务ID（当前实现中未使用，仅停止调度器）
            
        Returns:
            操作结果
        """
        try:
            success = self.scheduler.stop()
            return {"success": success, "message": "定时任务已删除" if success else "删除失败"}
        except Exception as e:
            logger.error(f"[智策服务] 删除定时任务失败: {e}")
            return {"success": False, "message": str(e)}
    
    async def trigger_analysis(self) -> Dict[str, Any]:
        """
        手动触发一次分析
        
        Returns:
            操作结果
        """
        try:
            logger.info("[智策服务] 手动触发分析")
            self.scheduler.manual_run()
            return {"success": True, "message": "分析任务已触发"}
        except Exception as e:
            logger.error(f"[智策服务] 手动触发分析失败: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_history(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        获取历史报告列表
        
        Args:
            page: 页码
            page_size: 每页数量
            
        Returns:
            历史报告列表
        """
        try:
            # 计算偏移量
            offset = (page - 1) * page_size
            limit = page_size
            
            # 获取报告列表
            reports_df = self.database.get_analysis_reports(limit=limit + offset)
            
            if reports_df.empty:
                return {"items": [], "total": 0, "page": page, "page_size": page_size}
            
            # 转换为列表格式
            items = []
            for idx, row in reports_df.iterrows():
                if idx < offset:
                    continue
                if len(items) >= page_size:
                    break
                
                # 解析analysis_content以获取完整数据
                analysis_content = None
                try:
                    if row.get('analysis_content'):
                        analysis_content = json.loads(row['analysis_content'])
                except:
                    pass
                
                items.append({
                    "id": row.get('id'),
                    "created_at": row.get('created_at', ''),
                    "data_date_range": row.get('data_date_range', ''),
                    "summary": row.get('summary', '智策板块分析报告'),
                    "confidence_score": row.get('confidence_score', 0.75),
                    "risk_level": row.get('risk_level', '中等'),
                    "market_outlook": row.get('market_outlook', '谨慎乐观'),
                    "analysis_content": analysis_content
                })
            
            return {
                "items": items,
                "total": len(reports_df),
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"[智策服务] 获取历史报告失败: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "error": str(e)}
    
    async def get_report_detail(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        获取报告详情
        
        Args:
            report_id: 报告ID
            
        Returns:
            报告详情
        """
        try:
            report = self.database.get_analysis_report(report_id)
            return report
        except Exception as e:
            logger.error(f"[智策服务] 获取报告详情失败: {e}")
            return None
    
    async def delete_report(self, report_id: int) -> bool:
        """
        删除报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            是否删除成功
        """
        try:
            return self.database.delete_analysis_report(report_id)
        except Exception as e:
            logger.error(f"[智策服务] 删除报告失败: {e}")
            return False
    
    async def generate_pdf(self, report_id: int) -> Dict[str, Any]:
        """
        生成PDF报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            PDF生成结果
        """
        try:
            # 获取报告详情
            report = self.database.get_analysis_report(report_id)
            
            if not report:
                return {"success": False, "error": "报告不存在"}
            
            # 解析分析内容
            analysis_content = report.get('analysis_content_parsed') or {}
            
            # 尝试导入PDF生成器
            try:
                from sector_strategy_pdf import SectorStrategyPDFGenerator
                generator = SectorStrategyPDFGenerator()
                pdf_path = generator.generate_pdf(analysis_content)
                
                return {
                    "success": True,
                    "pdf_path": pdf_path,
                    "message": "PDF生成成功"
                }
            except ImportError:
                logger.warning("[智策服务] PDF生成器未安装，返回Markdown格式")
                # 回退到Markdown格式
                markdown_content = self._generate_markdown_report(analysis_content)
                return {
                    "success": True,
                    "markdown": markdown_content,
                    "message": "PDF生成器未安装，返回Markdown格式"
                }
                
        except Exception as e:
            logger.error(f"[智策服务] 生成PDF失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_markdown_report(self, result_data: dict) -> str:
        """生成Markdown格式报告"""
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        
        markdown_content = f"""# 智策板块策略分析报告

**AI驱动的多维度板块投资决策支持系统**

---

## 📊 报告信息

- **生成时间**: {current_time}
- **分析周期**: 当日市场数据
- **AI模型**: DeepSeek Multi-Agent System

> ⚠️ 本报告由AI系统自动生成，仅供参考，不构成投资建议。

---

"""
        
        # 核心预测
        predictions = result_data.get('final_predictions', {})
        
        if predictions:
            markdown_content += "## 🎯 核心预测\n\n"
            
            # 板块多空
            long_short = predictions.get('long_short', {})
            bullish = long_short.get('bullish', [])
            bearish = long_short.get('bearish', [])
            
            if bullish:
                markdown_content += "### 🟢 看多板块\n\n"
                for idx, item in enumerate(bullish, 1):
                    markdown_content += f"{idx}. **{item.get('sector', 'N/A')}** (信心度: {item.get('confidence', 0)}/10)\n"
                    markdown_content += f"   - 理由: {item.get('reason', 'N/A')}\n\n"
            
            if bearish:
                markdown_content += "### 🔴 看空板块\n\n"
                for idx, item in enumerate(bearish, 1):
                    markdown_content += f"{idx}. **{item.get('sector', 'N/A')}** (信心度: {item.get('confidence', 0)}/10)\n"
                    markdown_content += f"   - 理由: {item.get('reason', 'N/A')}\n\n"
        
        # 综合研判
        comprehensive_report = result_data.get('comprehensive_report', '')
        if comprehensive_report:
            markdown_content += "## 📊 综合研判\n\n"
            markdown_content += f"{comprehensive_report}\n\n"
        
        markdown_content += "\n---\n\n*报告由智策AI系统自动生成*\n"
        
        return markdown_content
