"""
智瞰龙虎综合分析引擎
整合数据获取、AI分析、结果生成的核心引擎
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import time
import logging

# 尝试多种导入方式以兼容不同运行环境
try:
    # FastAPI 环境 - 绝对导入
    from app.data.longhubang_data import LonghubangDataFetcher
    from app.db.longhubang_db import LonghubangDatabase
    from app.agents.longhubang_agents import LonghubangAgents
    from app.services.longhubang.longhubang_scoring import LonghubangScoring
except ImportError:
    try:
        # Streamlit 环境 - 相对导入
        from data.longhubang_data import LonghubangDataFetcher
        from db.longhubang_db import LonghubangDatabase
        from agents.longhubang_agents import LonghubangAgents
        from longhubang_scoring import LonghubangScoring
    except ImportError:
        # 直接运行时的导入
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from data.longhubang_data import LonghubangDataFetcher
        from db.longhubang_db import LonghubangDatabase
        from agents.longhubang_agents import LonghubangAgents
        from longhubang_scoring import LonghubangScoring


class LonghubangService:
    """龙虎榜综合分析引擎"""
    
    def __init__(self, model="deepseek-chat", db_path=None):
        """
        初始化分析引擎
        
        Args:
            model: AI模型名称
            db_path: 数据库路径，默认使用统一的sqlite_db目录
        """
        self.data_fetcher = LonghubangDataFetcher()
        self.database = LonghubangDatabase(db_path)
        self.agents = LonghubangAgents(model=model)
        self.scoring = LonghubangScoring()
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        self.logger.info("[智瞰龙虎] 分析引擎初始化完成")
    
    def run_comprehensive_analysis(self, date=None, days=1) -> Dict[str, Any]:
        """
      完整的龙虎榜分析流  运行程
        
        Args:
            date: 指定日期，格式 YYYY-MM-DD，默认为昨日
            days: 分析最近几天的数据，默认1天
            
        Returns:
            完整的分析结果
        """
        self.logger.info("=" * 60)
        self.logger.info("🚀 智瞰龙虎综合分析系统启动")
        self.logger.info("=" * 60)
        
        results = {
            "success": False,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "data_info": {},
            "agents_analysis": {},
            "final_report": {},
            "recommended_stocks": []
        }
        
        try:
            # 阶段1: 获取龙虎榜数据
            self.logger.info("[阶段1] 获取龙虎榜数据...")
            self.logger.info("-" * 60)
            
            if date:
                data_list = [self.data_fetcher.get_longhubang_data(date)]
                data_list = data_list[0].get('data', []) if data_list[0] else []
            else:
                data_list = self.data_fetcher.get_recent_days_data(days)
            
            if not data_list:
                self.logger.error("未获取到龙虎榜数据")
                results["error"] = "未获取到龙虎榜数据"
                return results

            self.logger.info(f"成功获取 {len(data_list)} 条龙虎榜记录")
            
            # 阶段2: 保存数据到数据库
            self.logger.info("[阶段2] 保存数据到数据库...")
            self.logger.info("-" * 60)
            saved_count = self.database.save_longhubang_data(data_list)
            self.logger.info(f"保存 {saved_count} 条记录")
            
            # 阶段3: 数据分析和统计
            self.logger.info("[阶段3] 数据分析和统计...")
            self.logger.info("-" * 60)
            summary = self.data_fetcher.analyze_data_summary(data_list)
            formatted_data = self.data_fetcher.format_data_for_ai(data_list, summary)
            
            results["data_info"] = {
                "total_records": summary.get('total_records', 0),
                "total_stocks": summary.get('total_stocks', 0),
                "total_youzi": summary.get('total_youzi', 0),
                "summary": summary
            }
            self.logger.info("数据统计完成")
            
            # 阶段3.5: AI智能评分排名
            self.logger.info("[阶段3.5] AI智能评分排名...")
            self.logger.info("-" * 60)
            scoring_df = self.scoring.score_all_stocks(data_list)
            # 转换为可序列化格式以避免UI/存储类型问题
            scoring_ranking_data: List[Dict[str, Any]] = []
            try:
                if scoring_df is not None and hasattr(scoring_df, 'to_dict'):
                    scoring_ranking_data = scoring_df.to_dict('records')
                    self.logger.info(f"完成 {len(scoring_ranking_data)} 只股票的智能评分排名")
                else:
                    self.logger.warning("评分结果为空或格式不支持转换")
            except Exception as e:
                self.logger.exception(f"评分排名数据转换失败: {e}", exc_info=True)
                scoring_ranking_data = []
            results["scoring_ranking"] = scoring_ranking_data
            
            # 阶段4: AI分析师团队分析
            self.logger.info("[阶段4] AI分析师团队工作中...")
            self.logger.info("-" * 60)
            
            agents_results = {}
            
            # 1. 游资行为分析师
            self.logger.info("1/5 游资行为分析师...")
            youzi_result = self.agents.youzi_behavior_analyst(formatted_data, summary)
            agents_results["youzi"] = youzi_result
            
            # 2. 个股潜力分析师
            self.logger.info("2/5 个股潜力分析师...")
            stock_result = self.agents.stock_potential_analyst(formatted_data, summary)
            agents_results["stock"] = stock_result
            
            # 3. 题材追踪分析师
            self.logger.info("3/5 题材追踪分析师...")
            theme_result = self.agents.theme_tracker_analyst(formatted_data, summary)
            agents_results["theme"] = theme_result
            
            # 4. 风险控制专家
            self.logger.info("4/5 风险控制专家...")
            risk_result = self.agents.risk_control_specialist(formatted_data, summary)
            agents_results["risk"] = risk_result
            
            # 5. 首席策略师综合
            self.logger.info("5/5 首席策略师综合分析...")
            all_analyses = [youzi_result, stock_result, theme_result, risk_result]
            chief_result = self.agents.chief_strategist(all_analyses)
            agents_results["chief"] = chief_result
            
            results["agents_analysis"] = agents_results
            self.logger.info("所有AI分析师分析完成")
            
            # 阶段5: 提取推荐股票
            self.logger.info("[阶段5] 提取推荐股票...")
            self.logger.info("-" * 60)
            recommended_stocks = self._extract_recommended_stocks(
                chief_result.get('analysis', ''),
                stock_result.get('analysis', ''),
                summary
            )
            results["recommended_stocks"] = recommended_stocks
            self.logger.info(f"提取 {len(recommended_stocks)} 只推荐股票")
            
            # 阶段6: 生成最终报告
            self.logger.info("[阶段6] 生成最终报告...")
            self.logger.info("-" * 60)
            final_report = self._generate_final_report(agents_results, summary, recommended_stocks)
            results["final_report"] = final_report
            self.logger.info("最终报告生成完成")
            
            # 阶段7: 保存完整分析报告到数据库
            self.logger.info("[阶段7] 保存完整分析报告...")
            self.logger.info("-" * 60)
            data_date_range = self._get_date_range(data_list)
            
            # 转换评分排名数据为可序列化格式
            # 复用前面转换的评分数据
            # 若前面转换失败，此处不再重复转换，避免错误
            
            # 构建完整的分析内容（结构化）
            full_analysis_content = {
                "agents_analysis": agents_results,
                "data_info": results["data_info"],
                "scoring_ranking": scoring_ranking_data,
                "final_report": final_report,
                "timestamp": results["timestamp"]
            }
            
            report_id = self.database.save_analysis_report(
                data_date_range=data_date_range,
                analysis_content=full_analysis_content,  # 保存完整的结构化数据
                recommended_stocks=recommended_stocks,
                summary=final_report.get('summary', ''),
                full_result=results  # 传入完整结果
            )
            results["report_id"] = report_id
            self.logger.info(f"完整报告已保存 (ID: {report_id})")
            
            results["success"] = True
            
            self.logger.info("=" * 60)
            self.logger.info("✓ 智瞰龙虎综合分析完成！")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.exception(f"分析过程出错: {e}", exc_info=True)
            results["error"] = str(e)

        return results
    
    def _extract_recommended_stocks(self, chief_analysis: str, stock_analysis: str, summary: Dict) -> List[Dict]:
        """
        从AI分析中提取推荐股票
        
        支持解析格式：
        1. 首席分析师 Markdown 表格: | 优先级 | 股票名称 (代码) | 推荐理由 | 确定性评级 | 买入价位区间 | 目标价位 | 止损价位 | 持有周期建议 |
        2. 个股潜力分析师标题格式: #### **1.1 红相股份 (300290)**
        
        Args:
            chief_analysis: 首席策略师分析
            stock_analysis: 个股潜力分析师分析
            summary: 数据摘要
            
        Returns:
            推荐股票列表
        """
        import re
        
        recommended = []
        seen_codes = set()
        
        # 从摘要中获取TOP股票作为基础数据
        top_stocks_map = {}
        if summary.get('top_stocks'):
            for stock in summary['top_stocks']:
                code = stock.get('code', '')
                top_stocks_map[code] = stock
        
        # ========== 方法1: 解析首席分析师的 Markdown 表格 ==========
        if chief_analysis:
            # 匹配表格行: | **1** | **荣科科技 (300290)** | 推荐理由... | **高** | 价位区间 | 目标价 | 止损价 | 周期 |
            table_pattern = r'\|\s*\**(\d+)\**\s*\|\s*\**([^|（(]+)[（(](\d{6})[）)]\**\s*\|\s*([^|]+)\|\s*\**([^|*]+)\**\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|'
            table_matches = re.findall(table_pattern, chief_analysis)
            
            for match in table_matches:
                try:
                    rank = int(match[0])
                    name = match[1].strip(' *')
                    code = match[2]
                    reason = match[3].strip()
                    confidence = match[4].strip()
                    buy_price = match[5].strip()
                    target_price = match[6].strip()
                    stop_loss = match[7].strip()
                    hold_period = match[8].strip()
                    
                    if code not in seen_codes:
                        seen_codes.add(code)
                        base_data = top_stocks_map.get(code, {})
                        net_inflow = base_data.get('net_inflow', 0)
                        
                        # 提取游资和风格信息
                        youzi = ''
                        youzi_style = ''
                        # 从理由中提取游资信息
                        youzi_match = re.search(r'(成都系|苏南帮|量化打板|瑞鹤仙|炒股养家|宁波桑田路|欢乐海岸|深股通|沪股通|机构)', reason)
                        if youzi_match:
                            youzi = youzi_match.group(1)
                            youzi_style = '短线游资' if youzi in ['成都系', '苏南帮', '量化打板', '瑞鹤仙', '炒股养家', '宁波桑田路'] else '机构资金'
                        
                        # 提取标签
                        tags = []
                        tag_keywords = ['AI', '人工智能', '信创', '军工', '国企', '央国企', '数据要素', '华为', '机器人', '医药', '光模块']
                        for kw in tag_keywords:
                            if kw in reason:
                                tags.append(kw)
                        tags = tags[:3]  # 最多3个标签
                        
                        # 提取风险提示
                        risk = ''
                        risk_match = re.search(r'风险[：:在于]([^。]+)', reason)
                        if risk_match:
                            risk = risk_match.group(1).strip()
                        if not risk:
                            risk = '注意仓位控制，严格执行止损'
                        
                        recommended.append({
                            'rank': rank,
                            'code': code,
                            'name': name,
                            'net_inflow': net_inflow,
                            'reason': reason[:200] if len(reason) > 200 else reason,
                            'confidence': confidence,
                            'buy_price': buy_price,
                            'target_price': target_price,
                            'stop_loss': stop_loss,
                            'hold_period': hold_period,
                            'source': 'chief',
                            'youzi': youzi,
                            'youzi_style': youzi_style,
                            'tags': tags,
                            'risk': risk
                        })
                except Exception as e:
                    self.logger.warning(f"解析表格行失败: {e}")
                    continue
        
        # ========== 方法2: 解析个股潜力分析师的标题格式 ==========
        if stock_analysis and len(recommended) < 10:
            # 匹配标题: #### **1.1 红相股份 (300290)**
            title_pattern = r'####\s*\**\d+\.\d+\s+([^（(]+)[（(](\d{6})[）)]'
            title_matches = re.findall(title_pattern, stock_analysis)
            
            for name, code in title_matches:
                name = name.strip(' *')
                if code not in seen_codes:
                    seen_codes.add(code)
                    base_data = top_stocks_map.get(code, {})
                    net_inflow = base_data.get('net_inflow', 0)
                    
                    # 提取该股票的详细信息
                    stock_info = self._extract_stock_detail_from_analyst(stock_analysis, name, code)
                    
                    recommended.append({
                        'rank': len(recommended) + 1,
                        'code': code,
                        'name': name,
                        'net_inflow': net_inflow,
                        'reason': stock_info.get('reason', f'个股潜力分析师推荐'),
                        'confidence': stock_info.get('confidence', '中'),
                        'buy_price': stock_info.get('buy_price', '待定'),
                        'target_price': stock_info.get('target_price', '待定'),
                        'stop_loss': stock_info.get('stop_loss', '待定'),
                        'hold_period': stock_info.get('hold_period', '短线'),
                        'source': 'stock_analyst',
                        'youzi': stock_info.get('youzi', ''),
                        'youzi_style': stock_info.get('youzi_style', ''),
                        'tags': stock_info.get('tags', []),
                        'risk': stock_info.get('risk', '注意仓位控制')
                    })
                    
                    if len(recommended) >= 10:
                        break
        
        # ========== 方法3: 通用正则匹配作为兜底 ==========
        if len(recommended) < 5:
            combined_text = (chief_analysis or '') + '\n' + (stock_analysis or '')
            # 匹配: 股票名称 (代码) 或 股票名称（代码）
            stock_pattern = r'\*{0,2}([^\d\s\(\)（）|*]{2,6})\s*[（(](\d{6})[）)]\*{0,2}'
            matches = re.findall(stock_pattern, combined_text)
            
            for name, code in matches:
                name = name.strip(' *·、，。：:')
                if code not in seen_codes and len(name) >= 2 and len(name) <= 6:
                    seen_codes.add(code)
                    base_data = top_stocks_map.get(code, {})
                    net_inflow = base_data.get('net_inflow', 0)
                    
                    recommended.append({
                        'rank': len(recommended) + 1,
                        'code': code,
                        'name': name,
                        'net_inflow': net_inflow,
                        'reason': f'AI分析师推荐，资金净流入 {net_inflow:,.0f} 元' if net_inflow else 'AI分析师推荐',
                        'confidence': '中',
                        'buy_price': '待定',
                        'target_price': '待定',
                        'stop_loss': '待定',
                        'hold_period': '短线',
                        'source': 'ai_analysis',
                        'youzi': '',
                        'youzi_style': '',
                        'tags': [],
                        'risk': '注意仓位控制'
                    })
                    
                    if len(recommended) >= 10:
                        break
        
        # ========== 补充摘要中的TOP股票 ==========
        if len(recommended) < 5 and summary.get('top_stocks'):
            for stock in summary['top_stocks']:
                code = stock['code']
                if code not in seen_codes:
                    seen_codes.add(code)
                    recommended.append({
                        'rank': len(recommended) + 1,
                        'code': code,
                        'name': stock['name'],
                        'net_inflow': stock['net_inflow'],
                        'reason': f"资金净流入 TOP 股票，净流入 {stock['net_inflow']:,.0f} 元",
                        'confidence': '中',
                        'buy_price': '待定',
                        'target_price': '待定',
                        'stop_loss': '待定',
                        'hold_period': '短线',
                        'source': 'summary',
                        'youzi': '',
                        'youzi_style': '',
                        'tags': [],
                        'risk': '注意仓位控制'
                    })
                    if len(recommended) >= 10:
                        break
        
        # 重新排序
        for idx, stock in enumerate(recommended, 1):
            stock['rank'] = idx
        
        self.logger.info(f"[智瞰龙虎] 从AI分析中提取了 {len(recommended)} 只推荐股票")
        
        return recommended
    
    def _extract_stock_detail_from_analyst(self, text: str, stock_name: str, stock_code: str) -> Dict:
        """
        从个股潜力分析师文本中提取单只股票的详细信息
        
        Args:
            text: 分析师完整文本
            stock_name: 股票名称
            stock_code: 股票代码
            
        Returns:
            包含详细信息的字典
        """
        import re
        
        info = {
            'reason': '',
            'confidence': '中',
            'buy_price': '待定',
            'target_price': '待定',
            'stop_loss': '待定',
            'hold_period': '短线',
            'youzi': '',
            'youzi_style': '',
            'tags': [],
            'risk': '注意仓位控制'
        }
        
        # 查找该股票的分析段落（从标题到下一个标题或分隔线）
        pattern = rf'####\s*\**\d+\.\d+\s+{re.escape(stock_name)}\s*[（(]{stock_code}[）)].*?(?=####|\Z|---)'
        match = re.search(pattern, text, re.DOTALL)
        
        if not match:
            return info
        
        section = match.group(0)
        
        # 提取上涨逻辑作为推荐理由
        logic_match = re.search(r'\*\*上涨逻辑[：:]\*\*([^*]+)', section)
        if logic_match:
            info['reason'] = logic_match.group(1).strip()[:200]
        else:
            # 尝试提取资金面描述
            fund_match = re.search(r'\*\*资金面[（(][^)）]+[)）][：:]\*\*([^*]+)', section)
            if fund_match:
                info['reason'] = fund_match.group(1).strip()[:200]
        
        # 提取确定性
        conf_match = re.search(r'\*\*([高中低]+)确定性', section)
        if conf_match:
            info['confidence'] = conf_match.group(1)
        
        # 提取买入价位
        buy_match = re.search(r'\*\*买入价位[：:]\*\*\s*([^\n*]+)', section)
        if buy_match:
            info['buy_price'] = buy_match.group(1).strip()
        else:
            # 尝试其他格式
            buy_match2 = re.search(r'高开[在]?(\d+%?)[以]?内|平开|小幅[高低]开', section)
            if buy_match2:
                info['buy_price'] = buy_match2.group(0)
        
        # 提取止损价位
        stop_match = re.search(r'\*\*止损位[：:]\*\*\s*([^\n*]+)', section)
        if stop_match:
            info['stop_loss'] = stop_match.group(1).strip()
        
        # 提取目标价位
        target_match = re.search(r'\+(\d+%?至\+?\d+%?)', section)
        if target_match:
            info['target_price'] = target_match.group(1)
        
        # 提取持有周期
        if '超短线' in section or '1-3天' in section:
            info['hold_period'] = '超短线(1-3天)'
        elif '短线' in section or '3-5天' in section:
            info['hold_period'] = '短线(3-5天)'
        elif '波段' in section:
            info['hold_period'] = '波段'
        
        # 提取游资信息
        youzi_keywords = ['成都系', '苏南帮', '量化打板', '瑞鹤仙', '炒股养家', '宁波桑田路', '欢乐海岸', '深股通', '沪股通', '机构专用']
        for kw in youzi_keywords:
            if kw in section:
                info['youzi'] = kw
                info['youzi_style'] = '短线游资' if kw in ['成都系', '苏南帮', '量化打板', '瑞鹤仙', '炒股养家', '宁波桑田路'] else '机构资金'
                break
        
        # 提取标签
        tag_keywords = ['AI', '人工智能', '信创', '军工', '国企', '央国企', '数据要素', '华为', '机器人', '医药', '光模块', '电网', '物联网']
        for kw in tag_keywords:
            if kw in section and kw not in info['tags']:
                info['tags'].append(kw)
        info['tags'] = info['tags'][:3]
        
        # 提取风险提示
        risk_match = re.search(r'风险[在于提示：:]+([^。\n]+)', section)
        if risk_match:
            info['risk'] = risk_match.group(1).strip()
        
        return info
    
    def _generate_final_report(self, agents_results: Dict, summary: Dict, 
                               recommended_stocks: List[Dict]) -> Dict:
        """
        生成最终报告
        
        Args:
            agents_results: 所有分析师的分析结果
            summary: 数据摘要
            recommended_stocks: 推荐股票列表
            
        Returns:
            最终报告字典
        """
        report = {
            'title': '智瞰龙虎榜综合分析报告',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': '',
            'data_overview': {
                'total_records': summary.get('total_records', 0),
                'total_stocks': summary.get('total_stocks', 0),
                'total_youzi': summary.get('total_youzi', 0),
                'total_net_inflow': summary.get('total_net_inflow', 0)
            },
            'recommended_stocks_count': len(recommended_stocks),
            'agents_count': len(agents_results)
        }
        
        # 生成摘要
        summary_parts = []
        summary_parts.append(f"本次分析共涵盖 {summary.get('total_records', 0)} 条龙虎榜记录")
        summary_parts.append(f"涉及 {summary.get('total_stocks', 0)} 只股票")
        summary_parts.append(f"涉及 {summary.get('total_youzi', 0)} 个游资席位")
        summary_parts.append(f"共推荐 {len(recommended_stocks)} 只潜力股票")
        
        report['summary'] = "，".join(summary_parts) + "。"
        
        return report
    
    def _get_date_range(self, data_list: List[Dict]) -> str:
        """
        获取数据的日期范围
        
        Args:
            data_list: 数据列表
            
        Returns:
            日期范围字符串
        """
        if not data_list:
            return "未知"
        
        dates = []
        for record in data_list:
            date = record.get('rq') or record.get('日期')
            if date:
                dates.append(date)
        
        if not dates:
            return "未知"
        
        dates = sorted(set(dates))
        if len(dates) == 1:
            return dates[0]
        else:
            return f"{dates[0]} 至 {dates[-1]}"
    
    def get_historical_reports(self, limit=10):
        """
        获取历史分析报告
        
        Args:
            limit: 返回数量
            
        Returns:
            报告列表
        """
        return self.database.get_analysis_reports(limit)
    
    def get_report_detail(self, report_id):
        """
        获取报告详情
        
        Args:
            report_id: 报告ID
            
        Returns:
            报告详情
        """
        return self.database.get_analysis_report(report_id)
    
    def get_statistics(self):
        """
        获取数据库统计信息
        
        Returns:
            统计信息
        """
        return self.database.get_statistics()
    
    def get_top_youzi(self, start_date=None, end_date=None, limit=20):
        """
        获取活跃游资排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量
            
        Returns:
            游资排名
        """
        return self.database.get_top_youzi(start_date, end_date, limit)
    
    def get_top_stocks(self, start_date=None, end_date=None, limit=20):
        """
        获取热门股票排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量
            
        Returns:
            股票排名
        """
        return self.database.get_top_stocks(start_date, end_date, limit)
    
    def run_comprehensive_analysis_with_progress(
        self, 
        date=None, 
        days=1,
        progress_callback=None,
        log_callback=None
    ) -> Dict[str, Any]:
        """
        运行完整的龙虎榜分析流程（带进度回调）
        
        Args:
            date: 指定日期，格式 YYYY-MM-DD，默认为昨日
            days: 分析最近几天的数据，默认1天
            progress_callback: 进度回调函数 (progress: int, message: str, stage: str)
            log_callback: 日志回调函数 (level: str, message: str)
            
        Returns:
            完整的分析结果
        """
        def _progress(progress: int, message: str, stage: str = ""):
            self.logger.info(f"[{progress}%] {message}")
            if progress_callback:
                progress_callback(progress, message, stage)
        
        def _log(level: str, message: str):
            if level == "info":
                self.logger.info(message)
            elif level == "warning":
                self.logger.warning(message)
            elif level == "error":
                self.logger.error(message)
            if log_callback:
                log_callback(level, message)
        
        _progress(0, "🚀 智瞰龙虎综合分析系统启动", "init")
        
        results = {
            "success": False,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "data_info": {},
            "agents_analysis": {},
            "final_report": {},
            "recommended_stocks": []
        }
        
        try:
            # 阶段1: 获取龙虎榜数据
            _progress(5, "📊 正在获取龙虎榜数据...", "fetch_data")
            
            if date:
                data_result = self.data_fetcher.get_longhubang_data(date)
                data_list = data_result.get('data', []) if data_result else []
            else:
                data_list = self.data_fetcher.get_recent_days_data(days)
            
            if not data_list:
                _log("error", "未获取到龙虎榜数据")
                results["error"] = "未获取到龙虎榜数据"
                return results

            _log("info", f"成功获取 {len(data_list)} 条龙虎榜记录")
            _progress(10, f"✓ 获取到 {len(data_list)} 条记录", "fetch_data")
            
            # 阶段2: 保存数据到数据库
            _progress(12, "💾 保存数据到数据库...", "save_data")
            saved_count = self.database.save_longhubang_data(data_list)
            _log("info", f"保存 {saved_count} 条记录")
            _progress(15, f"✓ 保存 {saved_count} 条记录", "save_data")
            
            # 阶段3: 数据分析和统计
            _progress(18, "📈 数据分析和统计...", "analyze_data")
            summary = self.data_fetcher.analyze_data_summary(data_list)
            formatted_data = self.data_fetcher.format_data_for_ai(data_list, summary)
            
            results["data_info"] = {
                "total_records": summary.get('total_records', 0),
                "total_stocks": summary.get('total_stocks', 0),
                "total_youzi": summary.get('total_youzi', 0),
                "summary": summary
            }
            _progress(22, "✓ 数据统计完成", "analyze_data")
            
            # 阶段3.5: AI智能评分排名
            _progress(25, "🏆 AI智能评分排名...", "scoring")
            scoring_df = self.scoring.score_all_stocks(data_list)
            scoring_ranking_data: List[Dict[str, Any]] = []
            try:
                if scoring_df is not None and hasattr(scoring_df, 'to_dict'):
                    scoring_ranking_data = scoring_df.to_dict('records')
                    _log("info", f"完成 {len(scoring_ranking_data)} 只股票的智能评分排名")
            except Exception as e:
                _log("warning", f"评分排名数据转换失败: {e}")
            results["scoring_ranking"] = scoring_ranking_data
            _progress(30, f"✓ 完成 {len(scoring_ranking_data)} 只股票评分", "scoring")
            
            # 阶段4: AI分析师团队分析
            _progress(32, "🤖 AI分析师团队开始工作...", "ai_analysis")
            agents_results = {}
            
            # 1. 游资行为分析师
            _progress(35, "🎯 游资行为分析师正在分析...", "agent_youzi")
            _log("info", "1/5 游资行为分析师...")
            youzi_result = self.agents.youzi_behavior_analyst(formatted_data, summary)
            agents_results["youzi"] = youzi_result
            _progress(45, "✓ 游资行为分析完成", "agent_youzi")
            
            # 2. 个股潜力分析师
            _progress(47, "📈 个股潜力分析师正在分析...", "agent_stock")
            _log("info", "2/5 个股潜力分析师...")
            stock_result = self.agents.stock_potential_analyst(formatted_data, summary)
            agents_results["stock"] = stock_result
            _progress(55, "✓ 个股潜力分析完成", "agent_stock")
            
            # 3. 题材追踪分析师
            _progress(57, "🔥 题材追踪分析师正在分析...", "agent_theme")
            _log("info", "3/5 题材追踪分析师...")
            theme_result = self.agents.theme_tracker_analyst(formatted_data, summary)
            agents_results["theme"] = theme_result
            _progress(65, "✓ 题材追踪分析完成", "agent_theme")
            
            # 4. 风险控制专家
            _progress(67, "⚠️ 风险控制专家正在分析...", "agent_risk")
            _log("info", "4/5 风险控制专家...")
            risk_result = self.agents.risk_control_specialist(formatted_data, summary)
            agents_results["risk"] = risk_result
            _progress(75, "✓ 风险控制分析完成", "agent_risk")
            
            # 5. 首席策略师综合
            _progress(77, "👔 首席策略师综合分析...", "agent_chief")
            _log("info", "5/5 首席策略师综合分析...")
            all_analyses = [youzi_result, stock_result, theme_result, risk_result]
            chief_result = self.agents.chief_strategist(all_analyses)
            agents_results["chief"] = chief_result
            _progress(85, "✓ 首席策略师分析完成", "agent_chief")
            
            results["agents_analysis"] = agents_results
            _log("info", "所有AI分析师分析完成")
            
            # 阶段5: 提取推荐股票
            _progress(87, "🎯 提取推荐股票...", "extract_stocks")
            recommended_stocks = self._extract_recommended_stocks(
                chief_result.get('analysis', ''),
                stock_result.get('analysis', ''),
                summary
            )
            results["recommended_stocks"] = recommended_stocks
            _progress(90, f"✓ 提取 {len(recommended_stocks)} 只推荐股票", "extract_stocks")
            
            # 阶段6: 生成最终报告
            _progress(92, "📝 生成最终报告...", "generate_report")
            final_report = self._generate_final_report(agents_results, summary, recommended_stocks)
            results["final_report"] = final_report
            _progress(95, "✓ 最终报告生成完成", "generate_report")
            
            # 阶段7: 保存完整分析报告到数据库
            _progress(97, "💾 保存分析报告...", "save_report")
            data_date_range = self._get_date_range(data_list)
            
            full_analysis_content = {
                "agents_analysis": agents_results,
                "data_info": results["data_info"],
                "scoring_ranking": scoring_ranking_data,
                "final_report": final_report,
                "timestamp": results["timestamp"]
            }
            
            report_id = self.database.save_analysis_report(
                data_date_range=data_date_range,
                analysis_content=full_analysis_content,
                recommended_stocks=recommended_stocks,
                summary=final_report.get('summary', ''),
                full_result=results
            )
            results["report_id"] = report_id
            _log("info", f"完整报告已保存 (ID: {report_id})")
            
            results["success"] = True
            _progress(100, "🎉 智瞰龙虎综合分析完成！", "complete")
            
        except Exception as e:
            _log("error", f"分析过程出错: {e}")
            results["error"] = str(e)
            import traceback
            _log("error", traceback.format_exc())

        return results


# 测
if __name__ == "__main__":
    print("=" * 60)
    print("测试智瞰龙虎分析引擎")
    print("=" * 60)
    
    # 创建引擎实例
    engine = LonghubangEngine()
    
    # 运行综合分析（分析昨天的数据）
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    results = engine.run_comprehensive_analysis(date=yesterday)
    
    if results.get('success'):
        print("\n" + "=" * 60)
        print("分析成功！")
        print("=" * 60)
        print(f"数据记录: {results['data_info']['total_records']}")
        print(f"涉及股票: {results['data_info']['total_stocks']}")
        print(f"推荐股票: {len(results['recommended_stocks'])}")
    else:
        print(f"\n分析失败: {results.get('error', '未知错误')}")

