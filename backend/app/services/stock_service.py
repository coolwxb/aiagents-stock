"""
股票分析服务
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.stock import StockAnalysis
from app.schemas.stock import (
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    StockAnalyzeRequest,
    StockAnalyzeResponse,
)

from app.agents.ai_agents import StockAnalysisAgents  # type: ignore  # noqa: E402
from app.utils.pdf_generator import create_pdf_report  # type: ignore  # noqa: E402  # noqa: E402
from app.core.progress_tracker import get_progress_tracker, TaskStatus  # type: ignore  # noqa: E402
from app.data.stock_data import StockDataFetcher  # type: ignore  # noqa: E402
from app.data.data_source import DataSourceManager, init_source_manager as get_data_source_manager  # type: ignore  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_ANALYSTS = {
    "technical": True,
    "fundamental": True,
    "fund_flow": True,
    "risk": True,
    "sentiment": False,
    "news": False,
}

FLOAT_PATTERN = re.compile(r"-?\d+\.?\d*")


class StockService:
    """股票分析服务类，复用原有Streamlit分析流水线"""

    def __init__(self, db: Session, data_source_manager: DataSourceManager = None):
        self.db = db
        # 如果传入了 data_source_manager，使用它；否则从数据库配置加载
        if data_source_manager is None:
            try:
                from app.services.config_service import ConfigService
                config_service = ConfigService(db)
                config = config_service._load_config()
                self.data_source_manager = get_data_source_manager(config)
            except Exception as e:
                logger.warning(f"从数据库加载配置失败，使用默认数据源: {e}")
                self.data_source_manager = get_data_source_manager()
        else:
            self.data_source_manager = data_source_manager

    async def analyze_stock_with_progress(self, task_id: str, request: StockAnalyzeRequest):
        """带进度追踪的股票分析"""
        tracker = get_progress_tracker()
        
        try:
            tracker.update_progress(task_id, 0, "开始分析...", TaskStatus.RUNNING)
            
            # 处理分析师配置
            if request.analysts:
                agent_config = {k: v for k, v in request.analysts.items() if k in DEFAULT_ANALYSTS}
                for key in DEFAULT_ANALYSTS:
                    if key not in agent_config:
                        agent_config[key] = DEFAULT_ANALYSTS[key]
            elif request.agents:
                agent_config = self._build_agent_config(request.agents)
            else:
                agent_config = DEFAULT_ANALYSTS.copy()
            
            tracker.update_progress(task_id, 5, "准备分析师团队...")
            
            # 执行分析
            analysis_result = await asyncio.to_thread(
                self._run_single_analysis_with_progress,
                task_id,
                request.stock_code,
                request.period,
                agent_config,
            )
            
            if not analysis_result.get("success"):
                error_msg = analysis_result.get("error", "未知错误")
                tracker.fail_task(task_id, error_msg)
                return
            
            tracker.update_progress(task_id, 95, "保存分析结果...")
            record = self._persist_analysis("single", analysis_result)
            response = self._build_response(analysis_result, record)
            
            # 完成任务
            tracker.complete_task(task_id, response.dict())
            
        except Exception as exc:
            logger.error(f"分析失败: {exc}")
            tracker.fail_task(task_id, str(exc))

    async def analyze_stock(self, request: StockAnalyzeRequest) -> StockAnalyzeResponse:
        """单股分析"""
        # 处理分析师配置，兼容analysts字典和agents列表
        if request.analysts:
            # 前端发送的analysts字典格式
            agent_config = {k: v for k, v in request.analysts.items() if k in DEFAULT_ANALYSTS}
            # 填充默认值
            for key in DEFAULT_ANALYSTS:
                if key not in agent_config:
                    agent_config[key] = DEFAULT_ANALYSTS[key]
        elif request.agents:
            # 后端使用的agents列表格式
            agent_config = self._build_agent_config(request.agents)
        else:
            # 默认配置
            agent_config = DEFAULT_ANALYSTS.copy()
        
        analysis_result = await asyncio.to_thread(
            self._run_single_analysis,
            request.stock_code,
            request.period,
            agent_config,
        )

        if not analysis_result.get("success"):
            error_msg = analysis_result.get("error", "未知错误")
            raise ValueError(f"分析失败: {error_msg}")

        record = self._persist_analysis("single", analysis_result)
        response = self._build_response(analysis_result, record)
        return response

    async def batch_analyze(self, request: BatchAnalyzeRequest) -> BatchAnalyzeResponse:
        """批量分析"""
        if not request.stock_codes:
            raise ValueError("stock_codes 不能为空")

        success_results: List[StockAnalyzeResponse] = []
        failed_records: List[Dict[str, Any]] = []

        for code in request.stock_codes:
            try:
                result = await self.analyze_stock(
                    StockAnalyzeRequest(
                        stock_code=code,
                        period=request.period,
                        agents=request.agents,
                    )
                )
                success_results.append(result)
            except Exception as exc:  # noqa: BLE001
                logger.warning("批量分析失败 %s: %s", code, exc)
                failed_records.append({"stock_code": code, "error": str(exc)})

        return BatchAnalyzeResponse(
            total=len(request.stock_codes),
            success=len(success_results),
            failed=len(failed_records),
            results=success_results,
            failed_stocks=failed_records,
        )

    async def get_history(
        self,
        stock_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询历史记录"""
        if page < 1 or page_size < 1:
            raise ValueError("page 与 page_size 必须为正整数")

        query = self.db.query(StockAnalysis)
        if stock_code:
            query = query.filter(StockAnalysis.stock_code == stock_code)

        total = query.count()
        records = (
            query.order_by(StockAnalysis.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items: List[Dict[str, Any]] = []
        for record in records:
            try:
                payload = json.loads(record.analysis_result) if record.analysis_result else {}
            except json.JSONDecodeError:
                payload = {}
            items.append(
                {
                    "id": record.id,
                    "stock_code": record.stock_code,
                    "stock_name": record.stock_name,
                    "rating": record.rating,
                    "confidence_level": record.confidence_level,
                    "entry_range": record.entry_range,
                    "take_profit": record.take_profit,
                    "stop_loss": record.stop_loss,
                    "target_price": record.target_price,
                    "analysis_type": record.analysis_type,
                    "created_at": record.created_at,
                    "analysis_result": payload,
                }
            )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    async def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """获取股票信息"""
        fetcher = StockDataFetcher(data_source_manager_instance=self.data_source_manager)
        info = await asyncio.to_thread(fetcher.get_stock_info, stock_code)
        if isinstance(info, dict) and info.get("error"):
            raise ValueError(info["error"])
        return info

    async def generate_pdf(self, analysis_id: int) -> Dict[str, Any]:
        """生成PDF报告"""
        record = self.db.query(StockAnalysis).filter(StockAnalysis.id == analysis_id).first()
        if not record:
            raise ValueError(f"未找到分析记录: {analysis_id}")

        try:
            payload = json.loads(record.analysis_result) if record.analysis_result else {}
        except json.JSONDecodeError:
            payload = {}

        stock_info = payload.get("stock_info", {})
        agents_results = payload.get("agents_results", {})
        discussion_result = payload.get("discussion_result", "")
        final_decision = payload.get("final_decision", {})

        pdf_bytes = await asyncio.to_thread(
            create_pdf_report,
            stock_info,
            agents_results,
            discussion_result,
            final_decision,
        )

        filename = f"股票分析报告_{record.stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return {
            "filename": filename,
            "content": base64.b64encode(pdf_bytes).decode("utf-8"),
            "size": len(pdf_bytes),
        }

    # ------------------------------------------------------------------
    # 内部工具方法
    # ------------------------------------------------------------------

    def _run_single_analysis_with_progress(
        self,
        task_id: str,
        stock_code: str,
        period: str,
        agent_config: Dict[str, bool],
    ) -> Dict[str, Any]:
        """同步运行一次股票分析，带进度追踪"""
        tracker = get_progress_tracker()
        
        tracker.update_progress(task_id, 10, f"获取{stock_code}股票信息...")
        fetcher, stock_info, stock_data, indicators = self._prepare_stock_data(stock_code, period)
        
        tracker.update_progress(task_id, 20, "获取财务数据...")
        financial_data = self._safe_call(fetcher.get_financial_data, stock_code)

        quarterly_data = None
        if agent_config.get("fundamental") and fetcher._is_chinese_stock(stock_code):
            tracker.update_progress(task_id, 25, "获取季报数据...")
            quarterly_data = self._safe_import_and_call(
                module_name="quarterly_report_data",
                class_name="QuarterlyReportDataFetcher",
                method="get_quarterly_reports",
                args=(stock_code,),
                init_kwargs={"data_source_manager_instance": self.data_source_manager}
            )

        fund_flow_data = None
        if agent_config.get("fund_flow") and fetcher._is_chinese_stock(stock_code):
            tracker.update_progress(task_id, 30, "获取资金流向数据...")
            fund_flow_data = self._safe_import_and_call(
                module_name="fund_flow_akshare",
                class_name="FundFlowAkshareDataFetcher",
                method="get_fund_flow_data",
                args=(stock_code,),
                init_kwargs={"data_source_manager_instance": self.data_source_manager}
            )

        sentiment_data = None
        if agent_config.get("sentiment") and fetcher._is_chinese_stock(stock_code):
            tracker.update_progress(task_id, 35, "获取市场情绪数据...")
            sentiment_data = self._safe_import_and_call(
                module_name="market_sentiment_data",
                class_name="MarketSentimentDataFetcher",
                method="get_market_sentiment_data",
                args=(stock_code, stock_data),
                init_kwargs={"data_source_manager_instance": self.data_source_manager}
            )

        news_data = None
        if agent_config.get("news") and fetcher._is_chinese_stock(stock_code):
            tracker.update_progress(task_id, 40, "获取新闻公告数据...")
            news_data = self._safe_import_and_call(
                module_name="qstock_news_data",
                class_name="QStockNewsDataFetcher",
                method="get_stock_news",
                args=(stock_code,),
            )

        risk_data = None
        if agent_config.get("risk") and fetcher._is_chinese_stock(stock_code):
            tracker.update_progress(task_id, 45, "获取风险指标数据...")
            risk_data = self._safe_call(fetcher.get_risk_data, stock_code)

        tracker.update_progress(task_id, 50, "AI分析师团队分析中...")
        agents = StockAnalysisAgents(model="deepseek-chat")
        agents_results = agents.run_multi_agent_analysis(
            stock_info,
            stock_data,
            indicators,
            financial_data,
            fund_flow_data,
            sentiment_data,
            news_data,
            quarterly_data,
            risk_data,
            enabled_analysts=agent_config,
        )
        
        tracker.update_progress(task_id, 80, "团队讨论中...")
        discussion_result = agents.conduct_team_discussion(agents_results, stock_info)
        
        tracker.update_progress(task_id, 90, "生成投资决策...")
        final_decision = agents.make_final_decision(discussion_result, stock_info, indicators)

        return {
            "symbol": stock_code,
            "success": True,
            "stock_info": stock_info,
            "indicators": indicators,
            "agents_results": agents_results,
            "discussion_result": discussion_result,
            "final_decision": final_decision,
            "saved_to_db": False,
        }

    def _run_single_analysis(
        self,
        stock_code: str,
        period: str,
        agent_config: Dict[str, bool],
    ) -> Dict[str, Any]:
        """同步运行一次股票分析，供线程池调用"""
        fetcher, stock_info, stock_data, indicators = self._prepare_stock_data(stock_code, period)

        financial_data = self._safe_call(fetcher.get_financial_data, stock_code)

        quarterly_data = None
        if agent_config.get("fundamental") and fetcher._is_chinese_stock(stock_code):
            quarterly_data = self._safe_import_and_call(
                module_name="quarterly_report_data",
                class_name="QuarterlyReportDataFetcher",
                method="get_quarterly_reports",
                args=(stock_code,),
                init_kwargs={"data_source_manager_instance": self.data_source_manager}
            )

        fund_flow_data = None
        if agent_config.get("fund_flow") and fetcher._is_chinese_stock(stock_code):
            fund_flow_data = self._safe_import_and_call(
                module_name="fund_flow_akshare",
                class_name="FundFlowAkshareDataFetcher",
                method="get_fund_flow_data",
                args=(stock_code,),
                init_kwargs={"data_source_manager_instance": self.data_source_manager}
            )

        sentiment_data = None
        if agent_config.get("sentiment") and fetcher._is_chinese_stock(stock_code):
            sentiment_data = self._safe_import_and_call(
                module_name="market_sentiment_data",
                class_name="MarketSentimentDataFetcher",
                method="get_market_sentiment_data",
                args=(stock_code, stock_data),
                init_kwargs={"data_source_manager_instance": self.data_source_manager}
            )

        news_data = None
        if agent_config.get("news") and fetcher._is_chinese_stock(stock_code):
            news_data = self._safe_import_and_call(
                module_name="qstock_news_data",
                class_name="QStockNewsDataFetcher",
                method="get_stock_news",
                args=(stock_code,),
            )

        risk_data = None
        if agent_config.get("risk") and fetcher._is_chinese_stock(stock_code):
            risk_data = self._safe_call(fetcher.get_risk_data, stock_code)

        agents = StockAnalysisAgents(model="deepseek-chat")
        agents_results = agents.run_multi_agent_analysis(
            stock_info,
            stock_data,
            indicators,
            financial_data,
            fund_flow_data,
            sentiment_data,
            news_data,
            quarterly_data,
            risk_data,
            enabled_analysts=agent_config,
        )
        discussion_result = agents.conduct_team_discussion(agents_results, stock_info)
        final_decision = agents.make_final_decision(discussion_result, stock_info, indicators)

        return {
            "symbol": stock_code,
            "success": True,
            "stock_info": stock_info,
            "indicators": indicators,
            "agents_results": agents_results,
            "discussion_result": discussion_result,
            "final_decision": final_decision,
            "saved_to_db": False,
        }

    def _prepare_stock_data(
        self,
        stock_code: str,
        period: str,
    ) -> Tuple[StockDataFetcher, Dict[str, Any], Any, Dict[str, Any]]:
        fetcher = StockDataFetcher(data_source_manager_instance=self.data_source_manager)
        stock_info = fetcher.get_stock_info(stock_code)
        if isinstance(stock_info, dict) and stock_info.get("error"):
            raise ValueError(stock_info["error"])

        stock_data = fetcher.get_stock_data(stock_code, period)
        if stock_data is None or (isinstance(stock_data, dict) and stock_data.get("error")):
            raise ValueError(f"{stock_code} 无法获取历史数据")

        print(f"[indicators] 计算技术指标中...")
        stock_data_with_indicators = fetcher.calculate_technical_indicators(stock_data)
        indicators = fetcher.get_latest_indicators(stock_data_with_indicators)
        return fetcher, stock_info, stock_data_with_indicators, indicators

    def _persist_analysis(self, analysis_type: str, result: Dict[str, Any]) -> StockAnalysis:
        final_decision = result.get("final_decision", {}) or {}
        stock_info = result.get("stock_info", {}) or {}

        rating = final_decision.get("rating") or "未知"
        confidence = self._extract_float(final_decision.get("confidence_level"), default=0.0)
        take_profit = self._extract_float(final_decision.get("take_profit"))
        stop_loss = self._extract_float(final_decision.get("stop_loss"))
        target_price = self._extract_float(final_decision.get("target_price"))

        record = StockAnalysis(
            stock_code=stock_info.get("symbol", ""),
            stock_name=stock_info.get("name", ""),
            analysis_type=analysis_type,
            analysis_result=json.dumps(result, ensure_ascii=False, default=str),
            rating=rating,
            confidence_level=confidence,
            entry_range=final_decision.get("entry_range", ""),
            take_profit=take_profit,
            stop_loss=stop_loss,
            target_price=target_price,
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        result["saved_to_db"] = True
        result["record_id"] = record.id

        return record

    def _build_response(
        self,
        result: Dict[str, Any],
        record: StockAnalysis,
    ) -> StockAnalyzeResponse:
        final_decision = result.get("final_decision", {}) or {}
        return StockAnalyzeResponse(
            stock_code=record.stock_code,
            stock_name=record.stock_name or result.get("stock_info", {}).get("name", ""),
            rating=final_decision.get("rating", "未知"),
            confidence_level=record.confidence_level or 0.0,
            entry_range=final_decision.get("entry_range", "N/A"),
            take_profit=record.take_profit or 0.0,
            stop_loss=record.stop_loss or 0.0,
            target_price=record.target_price or 0.0,
            analysis_result=result,
            created_at=record.created_at or datetime.utcnow(),
        )

    @staticmethod
    def _build_agent_config(agent_list: Optional[List[str]]) -> Dict[str, bool]:
        if not agent_list:
            return DEFAULT_ANALYSTS.copy()

        normalized = {item.lower() for item in agent_list if item}
        config = {key: False for key in DEFAULT_ANALYSTS}
        alias_map = {
            "technical": "technical",
            "fundamental": "fundamental",
            "fund_flow": "fund_flow",
            "fundflow": "fund_flow",
            "risk": "risk",
            "risk_management": "risk",
            "sentiment": "sentiment",
            "news": "news",
        }
        for alias, target in alias_map.items():
            if alias in normalized and target in config:
                config[target] = True
        return config

    @staticmethod
    def _extract_float(value: Any, default: Optional[float] = None) -> Optional[float]:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        matches = FLOAT_PATTERN.findall(str(value))
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return default
        return default

    @staticmethod
    def _safe_call(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.debug("辅助数据获取失败: %s", exc)
            return None

    def _safe_import_and_call(
        self,
        module_name: str,
        class_name: str,
        method: str,
        args: Tuple[Any, ...],
        init_kwargs: Dict[str, Any] = None,
    ):
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            # 使用 init_kwargs 初始化类（支持传递 data_source_manager）
            instance = cls(**init_kwargs) if init_kwargs else cls()
            return getattr(instance, method)(*args)
        except Exception as exc:  # noqa: BLE001
            logger.debug("模块 %s.%s 调用失败: %s", module_name, class_name, exc)
            return None
