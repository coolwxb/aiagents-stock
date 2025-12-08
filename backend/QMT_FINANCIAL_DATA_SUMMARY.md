# QMT财务数据集成总结

## 概述

已成功将QMT财务数据获取功能集成到数据源管理器中，现在 `get_financial_data()` 方法优先使用QMT获取财务数据。

## 数据源优先级

**QMT → Akshare → Tushare**

## 新增方法

### `_fetch_financial_data_from_qmt(symbol, report_type='income')`

从QMT获取财务数据的内部方法。

**参数：**
- `symbol`: 股票代码（6位数字）
- `report_type`: 报表类型
  - `'income'` - 利润表
  - `'balance'` - 资产负债表
  - `'cashflow'` - 现金流量表

**返回：**
- DataFrame格式的财务数据
- 包含多个报告期的数据
- 自动添加 `report_date` 列标识报告期

**实现细节：**

1. **股票代码格式化**
   ```python
   # 6开头 -> 上海市场
   "600519" -> "600519.SH"
   
   # 0或3开头 -> 深圳市场
   "000001" -> "000001.SZ"
   "300001" -> "300001.SZ"
   ```

2. **报表类型映射**
   ```python
   type_mapping = {
       'income': 'Income',        # 利润表
       'balance': 'Balance',      # 资产负债表
       'cashflow': 'CashFlow'     # 现金流量表
   }
   ```

3. **调用QMT API**
   ```python
   financial_data = xtdata.get_financial_data(
       stock_code=full_code,
       table_list=[qmt_report_type],
       start_time='',  # 不限制开始时间
       end_time=''     # 不限制结束时间
   )
   ```

4. **数据格式转换**
   - QMT返回格式：`{报表类型: {报告期: {字段: 值}}}`
   - 转换为DataFrame：每行代表一个报告期，每列代表一个财务指标

## 更新的方法

### `get_financial_data(symbol, report_type='income')`

**变更：**
- 优先调用 `_fetch_financial_data_from_qmt()`
- QMT失败后依次尝试Akshare、Tushare
- 保持接口不变，向后兼容

**使用示例：**

```python
from app.data.data_source import data_source_manager

# 获取利润表
income_df = data_source_manager.get_financial_data("600519", report_type='income')

# 获取资产负债表
balance_df = data_source_manager.get_financial_data("600519", report_type='balance')

# 获取现金流量表
cashflow_df = data_source_manager.get_financial_data("600519", report_type='cashflow')
```

## QMT财务数据字段说明

### 利润表 (Income)

| 字段名 | 说明 | 单位 |
|--------|------|------|
| revenue | 营业收入 | 元 |
| netProfit | 净利润 | 元 |
| netProfitExclMinIntInc | 归母净利润 | 元 |
| operProfit | 营业利润 | 元 |
| totProfit | 利润总额 | 元 |
| totalOperCost | 营业总成本 | 元 |
| totalExpense | 营业成本 | 元 |
| saleExpense | 销售费用 | 元 |
| financialExpense | 财务费用 | 元 |
| lessGerlAdminExp | 管理费用 | 元 |
| incTax | 所得税 | 元 |
| grossProfit | 毛利润 | 元 |

### 资产负债表 (Balance)

| 字段名 | 说明 | 单位 |
|--------|------|------|
| totalAssets | 资产总计 | 元 |
| totalLiab | 负债合计 | 元 |
| totalEquity | 股东权益合计 | 元 |
| currentAssets | 流动资产合计 | 元 |
| nonCurrentAssets | 非流动资产合计 | 元 |
| currentLiab | 流动负债合计 | 元 |
| nonCurrentLiab | 非流动负债合计 | 元 |
| monetaryFunds | 货币资金 | 元 |
| accountsReceivable | 应收账款 | 元 |
| inventory | 存货 | 元 |
| fixedAssets | 固定资产 | 元 |
| intangibleAssets | 无形资产 | 元 |

### 现金流量表 (CashFlow)

| 字段名 | 说明 | 单位 |
|--------|------|------|
| netCashFlowOper | 经营活动产生的现金流量净额 | 元 |
| netCashFlowInv | 投资活动产生的现金流量净额 | 元 |
| netCashFlowFin | 筹资活动产生的现金流量净额 | 元 |
| netCashFlow | 现金及现金等价物净增加额 | 元 |
| cashFlowOper | 经营活动产生的现金流量 | 元 |
| cashFlowInv | 投资活动产生的现金流量 | 元 |
| cashFlowFin | 筹资活动产生的现金流量 | 元 |

## 数据格式示例

### QMT原始返回格式

```python
{
    'Income': {
        '20231231': {
            'revenue': 1234567890.0,
            'netProfit': 123456789.0,
            'operProfit': 234567890.0,
            ...
        },
        '20230930': {
            'revenue': 987654321.0,
            'netProfit': 98765432.0,
            'operProfit': 187654321.0,
            ...
        },
        ...
    }
}
```

### 转换后的DataFrame格式

```
   revenue    netProfit  operProfit  report_date
0  1234567890 123456789  234567890   20231231
1  987654321  98765432   187654321   20230930
...
```

## 测试方法

运行测试脚本中的财务数据测试：

```bash
cd backend
python test_qmt_data_source.py
```

测试会自动：
1. 检查QMT数据源是否可用
2. 尝试获取贵州茅台(600519)的利润表数据
3. 显示获取的报告期数量和数据列
4. 显示最新报告期的数据

## 错误处理

所有可能的错误都已处理：

1. **QMT不可用** - 自动跳过，使用Akshare
2. **股票代码无效** - 返回None，尝试下一个数据源
3. **报表类型错误** - 返回None，尝试下一个数据源
4. **数据为空** - 返回None，尝试下一个数据源
5. **网络错误** - 捕获异常，尝试下一个数据源

## 优势

1. **数据完整** - QMT财务数据字段完整，符合官方标准
2. **速度快** - 本地数据，无需网络请求
3. **无限制** - 不像Tushare需要积分，不像Akshare有频率限制
4. **多报告期** - 一次获取多个报告期的数据
5. **标准化** - 自动转换为DataFrame格式，便于分析

## 注意事项

1. **QMT需要先下载财务数据**
   - 可以使用 `xtdata.download_financial_data()` 预先下载
   - 或者在QMT客户端中查看过该股票的财务数据

2. **字段名称使用英文**
   - QMT返回的字段名为英文（如revenue、netProfit）
   - 与Akshare的中文字段名不同

3. **数据单位**
   - QMT财务数据单位为元（不是万元）
   - 与Tushare的单位可能不同，需要注意转换

4. **报告期格式**
   - QMT报告期格式为 'YYYYMMDD'（如 '20231231'）
   - 已自动添加到DataFrame的 `report_date` 列

## 后续优化建议

1. 添加更多报表类型支持（如主要指标、股本表等）
2. 支持指定报告期范围
3. 添加财务数据缓存机制
4. 支持批量获取多只股票的财务数据
5. 添加财务指标计算功能（如ROE、毛利率等）
