"""
板块相关模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.sql import func
from app.database import Base


class Sector(Base):
    """板块信息模型"""
    __tablename__ = "sectors"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    sector_code = Column(String(50), unique=True, nullable=False, index=True, comment="板块代码")
    sector_name = Column(String(100), nullable=False, comment="板块名称")
    category = Column(String(50), comment="板块类别(行业/概念/地域等)")
    description = Column(Text, comment="板块描述")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")
    
    __table_args__ = (
        Index('idx_sector_code', 'sector_code'),
        Index('idx_sector_name', 'sector_name'),
    )


class StockInstrument(Base):
    """股票合约基础信息模型(精简版-仅A股相关字段)"""
    __tablename__ = "stock_instrument"
    
    # 主键字段
    合约代码 = Column(String(20), primary_key=True, nullable=False, comment="合约代码（纯数字），如 000001")
    市场代码 = Column(String(10), primary_key=True, nullable=False, comment="合约市场代码，如 SH、SZ")
    
    # 基本信息
    合约名称 = Column(String(100), comment="合约名称")
    拼音简写 = Column(String(50), comment="合约名称的拼音简写")
    交易所代码 = Column(String(20), comment="交易所代码")
    
    # 日期信息
    IPO日期 = Column(String(20), comment="IPO日期（股票）")
    退市日期 = Column(String(20), comment="退市日或者到期日")
    
    # 价格信息
    前收盘价 = Column(Float, comment="前收盘价格")
    涨停价 = Column(Float, comment="当日涨停价")
    跌停价 = Column(Float, comment="当日跌停价")
    最小变价单位 = Column(Float, comment="最小变价单位")
    
    # 股本信息
    流通股本 = Column(Float, comment="流通股本")
    总股本 = Column(Float, comment="总股本")
    
    # 交易限制
    市价单最大下单量 = Column(Integer, comment="市价单最大下单量")
    市价单最小下单量 = Column(Integer, comment="市价单最小下单量")
    限价单最大下单量 = Column(Integer, comment="限价单最大下单量")
    限价单最小下单量 = Column(Integer, comment="限价单最小下单量")
    
    # 状态信息
    合约停牌状态 = Column(Integer, comment="合约停牌状态")
    是否可交易 = Column(Integer, comment="合约是否可交易")
    
    # 分类信息
    证券分类 = Column(String(50), comment="证券分类")
    证券属性 = Column(String(50), comment="证券属性")
    港股通标识 = Column(Integer, comment="标识港股是否为沪港通或深港通标的证券")
    
    # 其他信息
    注册资本 = Column(Float, comment="注册资本（单位:百万）")
    
    # 时间戳
    创建时间 = Column(DateTime, server_default=func.now(), comment="记录创建时间")
    更新时间 = Column(DateTime, onupdate=func.now(), comment="记录更新时间")
    
    __table_args__ = (
        Index('idx_contract_code', '合约代码'),
        Index('idx_contract_name', '合约名称'),
        Index('idx_market_code', '市场代码'),
    )


class SectorStock(Base):
    """板块-股票关系模型"""
    __tablename__ = "sector_stocks"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    sector_code = Column(String(50), nullable=False, comment="板块代码")
    合约代码 = Column(String(20), nullable=False, comment="合约代码")
    市场代码 = Column(String(10), nullable=False, comment="市场代码")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    __table_args__ = (
        Index('idx_sector_code', 'sector_code'),
        Index('idx_contract_code', '合约代码'),
        Index('idx_sector_stock', 'sector_code', '合约代码', '市场代码', unique=True),
    )
