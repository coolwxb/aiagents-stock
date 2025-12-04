"""
数据管理服务
使用 xtquant 获取板块和股票数据并保存到 MySQL
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.sector import Sector, StockInstrument, SectorStock

logger = logging.getLogger(__name__)


class DataManagementService:
    """数据管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self._init_xtquant()
    
    def _init_xtquant(self):
        """初始化 xtquant"""
        try:
            import sys
            import os
            # 添加 xtquant 路径
            xtquant_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                'xtquant'
            )
            if xtquant_path not in sys.path:
                sys.path.insert(0, xtquant_path)
            
            from xtquant import xtdata
            
            # 尝试连接
            xtdata.connect()
            self.xtdata = xtdata
            self.xtquant_available = True
            logger.info("✅ xtquant 初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ xtquant 初始化失败: {e}")
            self.xtdata = None
            self.xtquant_available = False
    
    async def update_sectors(self) -> Dict:
        """
        更新板块数据(从 xtquant 获取)
        
        Returns:
            更新结果统计
        """
        if not self.xtquant_available:
            return {"error": "xtquant 不可用,请检查 QMT 是否已启动"}
        
        try:
            logger.info("开始更新板块数据...")
            
            # 下载板块数据
            self.xtdata.download_sector_data()
            
            # 获取板块列表
            sector_list = self.xtdata.get_sector_list()
            
            if not sector_list:
                return {"error": "未获取到板块数据"}
            
            # 获取板块详细信息
            sector_df = self.xtdata.get_sector_info()
            
            added = 0
            updated = 0
            
            for sector_name in sector_list:
                try:
                    # 从板块信息中获取类别
                    category = ""
                    if not sector_df.empty:
                        sector_info = sector_df[sector_df['sector'] == sector_name]
                        if not sector_info.empty:
                            category = sector_info.iloc[0].get('category', '')
                    
                    # 使用板块名称作为代码(xtquant中没有单独的板块代码)
                    sector_code = sector_name
                    
                    # 检查是否已存在
                    existing = self.db.query(Sector).filter(
                        Sector.sector_code == sector_code
                    ).first()
                    
                    if existing:
                        # 更新
                        existing.sector_name = sector_name
                        existing.category = category
                        updated += 1
                    else:
                        # 新增
                        new_sector = Sector(
                            sector_code=sector_code,
                            sector_name=sector_name,
                            category=category
                        )
                        self.db.add(new_sector)
                        added += 1
                
                except Exception as e:
                    logger.error(f"处理板块 {sector_name} 失败: {e}")
                    continue
            
            self.db.commit()
            logger.info(f"板块数据更新完成: 新增 {added}, 更新 {updated}")
            
            return {
                "success": True,
                "added": added,
                "updated": updated,
                "total": len(sector_list)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新板块数据失败: {e}")
            return {"error": str(e)}
    
    async def update_sector_stocks(self, sector_code: Optional[str] = None) -> Dict:
        """
        更新板块成分股(从 xtquant 获取)
        
        Args:
            sector_code: 板块代码,如果为 None 则更新所有板块
            
        Returns:
            更新结果统计
        """
        if not self.xtquant_available:
            return {"error": "xtquant 不可用,请检查 QMT 是否已启动"}
        
        try:
            logger.info(f"开始更新板块成分股: {sector_code or '所有板块'}")
            
            # 获取要更新的板块列表
            if sector_code:
                sectors = self.db.query(Sector).filter(
                    Sector.sector_code == sector_code
                ).all()
            else:
                sectors = self.db.query(Sector).all()
            
            if not sectors:
                return {"error": "未找到板块数据,请先更新板块"}
            
            total_added = 0
            total_removed = 0
            
            for sector in sectors:
                try:
                    # 获取板块成分股
                    stock_list = self.xtdata.get_stock_list_in_sector(sector.sector_name)
                    
                    if not stock_list:
                        logger.warning(f"板块 {sector.sector_name} 没有成分股")
                        continue
                    
                    # 提取股票代码和市场代码(格式: 000001.SZ -> 合约代码=000001, 市场代码=SZ)
                    new_stocks = set()
                    for stock in stock_list:
                        if '.' in stock:
                            code, market = stock.split('.')
                            new_stocks.add((code, market))
                    
                    # 获取当前数据库中的成分股
                    existing_relations = self.db.query(SectorStock).filter(
                        SectorStock.sector_code == sector.sector_code
                    ).all()
                    
                    existing_stocks = {(r.合约代码, r.市场代码) for r in existing_relations}
                    
                    # 计算需要添加和删除的股票
                    to_add = new_stocks - existing_stocks
                    to_remove = existing_stocks - new_stocks
                    
                    # 删除不再属于该板块的股票
                    if to_remove:
                        for code, market in to_remove:
                            self.db.query(SectorStock).filter(
                                and_(
                                    SectorStock.sector_code == sector.sector_code,
                                    SectorStock.合约代码 == code,
                                    SectorStock.市场代码 == market
                                )
                            ).delete(synchronize_session=False)
                        total_removed += len(to_remove)
                    
                    # 添加新的成分股
                    for code, market in to_add:
                        new_relation = SectorStock(
                            sector_code=sector.sector_code,
                            合约代码=code,
                            市场代码=market
                        )
                        self.db.add(new_relation)
                        total_added += 1
                    
                except Exception as e:
                    logger.error(f"更新板块 {sector.sector_name} 成分股失败: {e}")
                    continue
            
            self.db.commit()
            logger.info(f"板块成分股更新完成: 新增 {total_added}, 删除 {total_removed}")
            
            return {
                "success": True,
                "added": total_added,
                "removed": total_removed,
                "sectors_updated": len(sectors)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新板块成分股失败: {e}")
            return {"error": str(e)}
    
    async def update_stock_info(self, stock_code: Optional[str] = None) -> Dict:
        """
        更新股票合约基本信息(从 xtquant 获取)
        
        Args:
            stock_code: 股票代码(带市场后缀,如 000001.SZ),如果为 None 则更新所有板块成分股
            
        Returns:
            更新结果统计
        """
        if not self.xtquant_available:
            return {"error": "xtquant 不可用,请检查 QMT 是否已启动"}
        
        try:
            logger.info(f"开始更新股票合约信息: {stock_code or '所有成分股'}")
            
            # 获取要更新的股票列表
            if stock_code:
                # 如果指定了股票代码,需要转换格式
                if '.' not in stock_code:
                    stock_code = self._convert_to_xt_code(stock_code)
                stock_codes = [stock_code]
            else:
                # 获取所有板块成分股(去重)
                relations = self.db.query(
                    SectorStock.合约代码, 
                    SectorStock.市场代码
                ).distinct().all()
                stock_codes = [f"{r[0]}.{r[1]}" for r in relations]
            
            if not stock_codes:
                return {"error": "未找到需要更新的股票"}
            
            added = 0
            updated = 0
            failed = 0
            
            for xt_code in stock_codes:
                try:
                    # 获取股票详细信息
                    stock_detail = self.xtdata.get_instrument_detail(xt_code)
                    
                    if not stock_detail:
                        logger.warning(f"未获取到股票 {xt_code} 的信息")
                        failed += 1
                        continue
                    
                    # 拆分代码和市场
                    code, market = xt_code.split('.') if '.' in xt_code else (xt_code, '')
                    
                    # 检查是否已存在
                    existing = self.db.query(StockInstrument).filter(
                        and_(
                            StockInstrument.合约代码 == code,
                            StockInstrument.市场代码 == market
                        )
                    ).first()
                    
                    # 准备数据(仅A股相关字段)
                    instrument_data = {
                        '合约代码': code,
                        '市场代码': market,
                        '合约名称': stock_detail.get('InstrumentName'),
                        '拼音简写': stock_detail.get('PYShort'),
                        '交易所代码': stock_detail.get('ExchangeID'),
                        'IPO日期': stock_detail.get('ListDate'),
                        '退市日期': stock_detail.get('ExpireDate'),
                        '前收盘价': stock_detail.get('PreClosePrice'),
                        '涨停价': stock_detail.get('UpperLimitPrice'),
                        '跌停价': stock_detail.get('LowerLimitPrice'),
                        '最小变价单位': stock_detail.get('PriceTick'),
                        '流通股本': stock_detail.get('CirculatingShare'),
                        '总股本': stock_detail.get('TotalShare'),
                        '市价单最大下单量': stock_detail.get('MaxMarketOrderVolume'),
                        '市价单最小下单量': stock_detail.get('MinMarketOrderVolume'),
                        '限价单最大下单量': stock_detail.get('MaxLimitOrderVolume'),
                        '限价单最小下单量': stock_detail.get('MinLimitOrderVolume'),
                        '合约停牌状态': stock_detail.get('SuspendFlag'),
                        '是否可交易': 1 if stock_detail.get('IsTrading') else 0,
                        '证券分类': stock_detail.get('SecurityType'),
                        '证券属性': stock_detail.get('SecurityAttribute'),
                        '港股通标识': stock_detail.get('StockConnectFlag'),
                        '注册资本': stock_detail.get('RegisteredCapital')
                    }
                    
                    if existing:
                        # 更新
                        for key, value in instrument_data.items():
                            if value is not None and key not in ['合约代码', '市场代码']:
                                setattr(existing, key, value)
                        updated += 1
                    else:
                        # 新增
                        new_instrument = StockInstrument(**instrument_data)
                        self.db.add(new_instrument)
                        added += 1
                
                except Exception as e:
                    logger.error(f"更新股票 {xt_code if 'xt_code' in locals() else stock_code} 信息失败: {e}")
                    failed += 1
                    continue
            
            self.db.commit()
            logger.info(f"股票合约信息更新完成: 新增 {added}, 更新 {updated}, 失败 {failed}")
            
            return {
                "success": True,
                "added": added,
                "updated": updated,
                "failed": failed,
                "total": len(stock_codes)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新股票合约信息失败: {e}")
            return {"error": str(e)}
    
    def _convert_to_xt_code(self, stock_code: str) -> str:
        """
        转换股票代码为 xtquant 格式
        
        Args:
            stock_code: 6位股票代码
            
        Returns:
            xtquant 格式代码 (如: 000001.SZ)
        """
        if '.' in stock_code:
            return stock_code
        
        if stock_code.startswith('6'):
            return f"{stock_code}.SH"
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            return f"{stock_code}.SZ"
        elif stock_code.startswith('8') or stock_code.startswith('4'):
            return f"{stock_code}.BJ"
        else:
            return f"{stock_code}.SH"
    
    async def get_sectors(self, page: int = 1, page_size: int = 20, category: Optional[str] = None) -> Dict:
        """
        获取板块列表
        
        Args:
            page: 页码
            page_size: 每页数量
            category: 板块类别筛选
            
        Returns:
            板块列表和总数
        """
        try:
            query = self.db.query(Sector)
            
            if category:
                query = query.filter(Sector.category == category)
            
            total = query.count()
            
            sectors = query.offset((page - 1) * page_size).limit(page_size).all()
            
            return {
                "success": True,
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": [
                    {
                        "id": s.id,
                        "sector_code": s.sector_code,
                        "sector_name": s.sector_name,
                        "category": s.category,
                        "created_at": s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else None,
                        "updated_at": s.updated_at.strftime('%Y-%m-%d %H:%M:%S') if s.updated_at else None
                    }
                    for s in sectors
                ]
            }
        except Exception as e:
            logger.error(f"获取板块列表失败: {e}")
            return {"error": str(e)}
    
    async def get_stocks(self, page: int = 1, page_size: int = 20, sector_code: Optional[str] = None) -> Dict:
        """
        获取股票合约列表
        
        Args:
            page: 页码
            page_size: 每页数量
            sector_code: 板块代码筛选
            
        Returns:
            股票列表和总数
        """
        try:
            query = self.db.query(StockInstrument)
            
            if sector_code:
                # 连接查询获取指定板块的股票
                query = query.join(
                    SectorStock,
                    and_(
                        StockInstrument.合约代码 == SectorStock.合约代码,
                        StockInstrument.市场代码 == SectorStock.市场代码
                    )
                ).filter(SectorStock.sector_code == sector_code)
            
            total = query.count()
            
            stocks = query.offset((page - 1) * page_size).limit(page_size).all()
            
            return {
                "success": True,
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": [
                    {
                        "合约代码": s.合约代码,
                        "市场代码": s.市场代码,
                        "合约名称": s.合约名称,
                        "拼音简写": s.拼音简写,
                        "IPO日期": s.IPO日期,
                        "退市日期": s.退市日期,
                        "流通股本": s.流通股本,
                        "总股本": s.总股本,
                        "证券分类": s.证券分类,
                        "证券属性": s.证券属性,
                        "是否可交易": s.是否可交易,
                        "前收盘价": s.前收盘价,
                        "涨停价": s.涨停价,
                        "跌停价": s.跌停价,
                        "港股通标识": s.港股通标识,
                        "创建时间": s.创建时间.strftime('%Y-%m-%d %H:%M:%S') if s.创建时间 else None,
                        "更新时间": s.更新时间.strftime('%Y-%m-%d %H:%M:%S') if s.更新时间 else None
                    }
                    for s in stocks
                ]
            }
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return {"error": str(e)}
