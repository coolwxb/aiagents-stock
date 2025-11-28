#coding=utf-8
"""
xtpythonclient 存根模块
用于在 macOS 等非 Windows 平台上提供兼容性支持
注意：此模块仅提供接口存根，实际功能需要在 Windows 平台上使用原生 .pyd 扩展模块
"""

import sys
import platform

# 检查是否为 Windows 平台
if platform.system() == 'Windows':
    # 在 Windows 平台上，尝试导入真正的模块
    try:
        # 尝试导入不同 Python 版本的 .pyd 文件
        import importlib.util
        import os
        
        python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
        pyd_file = f"xtpythonclient.{python_version}-win_amd64.pyd"
        pyd_path = os.path.join(os.path.dirname(__file__), pyd_file)
        
        if os.path.exists(pyd_path):
            spec = importlib.util.spec_from_file_location("xtpythonclient", pyd_path)
            if spec and spec.loader:
                _real_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(_real_module)
                # 将真实模块的所有内容复制到当前模块
                for attr in dir(_real_module):
                    if not attr.startswith('_'):
                        setattr(sys.modules[__name__], attr, getattr(_real_module, attr))
    except Exception as e:
        print(f"警告: 无法加载 xtpythonclient 原生模块: {e}")
        print("将使用存根实现，功能可能受限")

# 如果不在 Windows 平台或导入失败，使用存根实现
if platform.system() != 'Windows' or 'XtQuantAsyncClient' not in dir(sys.modules[__name__]):
    # 存根类定义
    class XtQuantAsyncClient:
        """XtQuantAsyncClient 存根类"""
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "xtpythonclient 模块在非 Windows 平台上不可用。\n"
                "此功能需要在 Windows 平台上使用原生 .pyd 扩展模块。\n"
                "请确保在 Windows 平台上运行，或联系开发者获取 macOS/Linux 版本支持。"
            )
        
        def nextSeq(self):
            raise RuntimeError("xtpythonclient 在非 Windows 平台上不可用")
    
    # 请求类存根
    class SubscribeReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class UnsubscribeReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class OrderStockReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strStockCode = None
            self.m_nOrderType = None
            self.m_nOrderSide = None
            self.m_nPriceType = None
            self.m_dPrice = None
            self.m_nVolume = None
            self.m_strStrategyName = None
            self.m_strOrderRemark = None
    
    class CancelOrderStockReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_nOrderID = None
            self.m_strOrderSysID = None
            self.m_nMarket = None
    
    class QueryAccountInfosReq:
        def __init__(self):
            pass
    
    class QueryAccountStatusReq:
        def __init__(self):
            pass
    
    class QueryStockAssetReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryStockOrdersReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_nOrderID = None
            self.m_bCanCancel = None
    
    class QueryStockTradesReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryStockPositionsReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strStockCode = None
    
    class QueryCreditDetailReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryStkCompactsReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryCreditSubjectsReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryCreditSloCodeReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryCreditAssureReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryNewPurchaseLimitReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryIPODataReq:
        def __init__(self):
            self.m_strIPOType = None
    
    class TransferParam:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_dAmount = None
            self.m_nTransferType = None
    
    class QueryComFundReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryComPositionReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strInstrumentID = None
    
    class SmtQueryQuoterReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strStockCode = None
    
    class SmtNegotiateOrderReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strStockCode = None
            self.m_nOrderSide = None
            self.m_nVolume = None
            self.m_dPrice = None
            self.m_strStrategyName = None
            self.m_strOrderRemark = None
    
    class SmtAppointmentOrderReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strStockCode = None
            self.m_nOrderSide = None
            self.m_nVolume = None
            self.m_dPrice = None
            self.m_strStrategyName = None
            self.m_strOrderRemark = None
    
    class SmtAppointmentCancelReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_nOrderID = None
    
    class SmtQueryOrderReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_nOrderID = None
    
    class SmtQueryCompactReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_nCompactID = None
    
    class SmtCompactRenewalReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_nCompactID = None
            self.m_nRenewalDays = None
    
    class SmtCompactReturnReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_nCompactID = None
            self.m_nVolume = None
    
    class QueryPositionStatisticsReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class BankTransferReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strBankID = None
            self.m_dAmount = None
            self.m_nTransferType = None
            self.m_strPassword = None
            self.m_strFundPassword = None
    
    class QueryBankInfoReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class QueryBankAmountReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strBankID = None
    
    class QueryBankTransferStreamReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strBankID = None
    
    class QuerySecuAccountReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
    
    class CtpInternalTransferReq:
        def __init__(self):
            self.m_nAccountType = None
            self.m_strAccountID = None
            self.m_strTargetAccountID = None
            self.m_dAmount = None
            self.m_nTransferType = None

