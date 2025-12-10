"""
QMT API 客户端工具类
用于调用远程QMT服务的各个API接口
"""
import requests
from typing import Dict, List, Optional, Any


class QMTClient:
    """QMT API 客户端"""
    
    def __init__(self, base_url: str = "http://82.156.239.131:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_prefix = "/api/v1/qmt"
        self.timeout = 30
    
    def _url(self, path: str) -> str:
        return f"{self.base_url}{self.api_prefix}{path}"
    
    def _get(self, path: str, params: dict = None) -> Any:
        """GET请求"""
        resp = requests.get(self._url(path), params=params, timeout=self.timeout)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == 200:
            return result.get("data")
        raise Exception(result.get("message", "请求失败"))
    
    def _post(self, path: str, json_data: dict = None, params: dict = None) -> Any:
        """POST请求"""
        resp = requests.post(self._url(path), json=json_data, params=params, timeout=self.timeout)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == 200:
            return result.get("data")
        raise Exception(result.get("message", "请求失败"))

    # ==================== 连接管理 ====================
    
    def get_status(self) -> Dict:
        """获取QMT连接状态"""
        return self._get("/status")
    
    def connect(self) -> Dict:
        """连接到MiniQMT"""
        return self._post("/connect")
    
    def disconnect(self) -> Dict:
        """断开QMT连接"""
        return self._post("/disconnect")

    # ==================== 账户信息 ====================
    
    def get_account(self) -> Dict:
        """获取账户信息"""
        return self._get("/account")

    # ==================== 持仓管理 ====================
    
    def get_positions(self) -> List[Dict]:
        """获取所有持仓"""
        return self._get("/positions")
    
    def get_position(self, stock_code: str) -> Optional[Dict]:
        """获取指定股票持仓"""
        return self._get(f"/positions/{stock_code}")

    # ==================== 交易接口 ====================
    
    def buy(self, stock_code: str, quantity: int, price: float = 0, order_type: str = "market") -> Dict:
        """买入股票"""
        return self._post("/buy", {
            "stock_code": stock_code,
            "quantity": quantity,
            "price": price,
            "order_type": order_type
        })
    
    def sell(self, stock_code: str, quantity: int, price: float = 0, order_type: str = "market") -> Dict:
        """卖出股票"""
        return self._post("/sell", {
            "stock_code": stock_code,
            "quantity": quantity,
            "price": price,
            "order_type": order_type
        })

    # ==================== 委托查询 ====================
    
    def get_orders(self, cancelable_only: bool = False) -> List[Dict]:
        """
        查询当日所有委托
        
        Args:
            cancelable_only: 是否只返回可撤单的委托
        
        Returns:
            委托列表
        """
        return self._get("/orders", {"cancelable_only": cancelable_only})
    
    def get_cancelable_orders(self) -> List[Dict]:
        """查询当日可撤委托"""
        return self._get("/orders/cancelable")
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """根据订单编号查询委托"""
        return self._get(f"/orders/{order_id}")
    
    def get_orders_by_stock(self, stock_code: str) -> List[Dict]:
        """查询指定股票的所有委托"""
        return self._get(f"/orders/stock/{stock_code}")
    
    def get_pending_orders(self) -> List[Dict]:
        """查询未完成的委托（非最终状态）"""
        return self._get("/orders/pending")
    
    def get_orders_summary(self) -> Dict:
        """获取委托汇总信息"""
        return self._get("/orders/summary")
    
    def cancel_order(self, order_id: int) -> Dict:
        """撤销委托"""
        return self._post(f"/orders/{order_id}/cancel")
    
    def cancel_all_orders(self) -> Dict:
        """撤销所有可撤委托"""
        return self._post("/orders/cancel-all")
    
    def cancel_orders_by_stock(self, stock_code: str) -> Dict:
        """撤销指定股票的所有可撤委托"""
        return self._post(f"/orders/stock/{stock_code}/cancel")
    
    def has_pending_orders(self, stock_code: str) -> bool:
        """
        检查指定股票是否有未完成的委托
        
        Args:
            stock_code: 股票代码
        
        Returns:
            是否有未完成委托
        """
        try:
            orders = self.get_orders_by_stock(stock_code)
            if not orders:
                return False
            # 检查是否有非最终状态的委托
            for order in orders:
                if not order.get('is_final', False):
                    return True
            return False
        except Exception:
            return False

    # ==================== 实时行情 ====================
    
    def get_quote_stats(self) -> Dict:
        """获取全推数据统计"""
        return self._get("/quote/stats")
    
    def get_quote(self, stock_code: str) -> Optional[Dict]:
        """获取单只股票行情"""
        return self._get(f"/quote/{stock_code}")
    
    def get_quotes_batch(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """批量获取行情"""
        return self._post("/quote/batch", {"stock_codes": stock_codes})
    
    def get_all_quotes(self, limit: int = 100) -> Dict:
        """获取所有行情数据"""
        return self._get("/quote", {"limit": limit})

    # ==================== 股票基础信息 ====================
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """获取股票完整基础信息"""
        return self._get(f"/info/{stock_code}")
    
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict]:
        """获取股票简化基础信息"""
        return self._get(f"/info/{stock_code}/basic")
    
    def get_stocks_info_batch(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """批量获取股票基础信息"""
        return self._post("/info/batch", {"stock_codes": stock_codes})

    # ==================== 财务数据 ====================
    
    def get_financial(self, stock_code: str, report_type: str = "Income",
                      start_date: str = "", end_date: str = "") -> Optional[Dict]:
        """获取财务数据"""
        params = {"report_type": report_type}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._get(f"/financial/{stock_code}", params)
    
    def download_financial(self, stock_code: str, report_type: str = "Income",
                           start_date: str = "", end_date: str = "") -> Dict:
        """下载财务数据"""
        params = {"report_type": report_type}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._post(f"/financial/{stock_code}/download", params=params)
    
    def get_financial_fields(self, report_type: str) -> Dict:
        """获取财务数据字段说明"""
        return self._get(f"/financial/fields/{report_type}")

    # ==================== 历史K线数据 ====================
    
    def get_stock_hist_data(self, stock_code: str, period: str = "1d",
                            start_date: str = "", end_date: str = "",
                            count: int = 200) -> Optional[Dict]:
        """
        获取股票历史K线数据
        
        Args:
            stock_code: 股票代码
            period: K线周期（1m/5m/15m/30m/60m/1d/1w/1M）
            start_date: 开始日期（格式：20240101）
            end_date: 结束日期（格式：20241231）
            count: 获取数量
        
        Returns:
            K线数据字典，包含 date/open/high/low/close/volume/amount 列表
        """
        import pandas as pd
        
        params = {"period": period, "count": count}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        data = self._get(f"/kline/{stock_code}", params)
        
        if data is None:
            return None
        
        # 转换为DataFrame格式以兼容现有代码
        return pd.DataFrame(data)


# 默认客户端实例
qmt_client = QMTClient()


if __name__ == "__main__":
    # 测试示例
    client = QMTClient()
    
    print("=== 测试QMT客户端 ===")
    
    # 获取状态
    try:
        status = client.get_status()
        print(f"连接状态: {status}")
    except Exception as e:
        print(f"获取状态失败: {e}")
    
    # 获取行情
    try:
        quote = client.get_quote("600519")
        print(f"茅台行情: {quote}")
    except Exception as e:
        print(f"获取行情失败: {e}")
