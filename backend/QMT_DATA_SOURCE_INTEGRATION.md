# QMT数据源集成说明

## 概述

已成功将QMT（迅投QMT）集成为数据源管理器的最高优先级数据源。现在数据获取的优先级顺序为：

**QMT → MySQL → Akshare → Tushare**

## 修改的文件

### 1. `backend/app/data/data_source.py`

#### 主要变更：

1. **类文档更新**
   - 从 "mysql、akshare和tushare的自动切换机制"
   - 改为 "QMT、mysql、akshare和tushare的自动切换机制"

2. **初始化方法 (`__init__`)**
   - 添加 `qmt_available` 标志
   - 添加 `xtdata_module` 引用
   - 调用 `_init_qmt()` 初始化QMT数据源

3. **新增方法：`_init_qmt()`**
   - 导入 `xtquant.xtdata` 模块
   - 尝试连接QMT
   - 设置可用性标志

4. **新增方法：`_fetch_stock_hist_from_qmt()`**
   - 从QMT获取股票历史数据
   - 支持前复权、后复权、不复权
   - 自动格式化股票代码（添加.SH或.SZ后缀）
   - 计算涨跌幅、涨跌额、振幅等衍生指标
   - 返回标准化的DataFrame

5. **新增方法：`_fetch_stock_basic_info_from_qmt()`**
   - 从QMT获取股票基本信息
   - 包括股票名称、行业、市场、上市日期等
   - 包括涨跌停价、流通股本、总股本等详细信息

6. **新增方法：`_fetch_realtime_quotes_from_qmt()`**
   - 从QMT获取实时行情数据
   - 使用 `get_full_tick()` 获取tick数据
   - 自动计算涨跌幅和涨跌额
   - 返回标准化的行情字典

7. **新增方法：`_fetch_financial_data_from_qmt()`**
   - 从QMT获取财务数据
   - 支持利润表、资产负债表、现金流量表
   - 自动转换为DataFrame格式
   - 返回标准化的财务数据

8. **更新方法：`get_stock_hist_data()`**
   - 优先调用 `_fetch_stock_hist_from_qmt()`
   - QMT失败后依次尝试MySQL、Akshare、Tushare
   - 更新错误消息包含所有4个数据源

9. **更新方法：`get_stock_basic_info()`**
   - 优先调用 `_fetch_stock_basic_info_from_qmt()`
   - QMT失败后依次尝试Akshare、Tushare

10. **更新方法：`get_realtime_quotes()`**
   - 优先调用 `_fetch_realtime_quotes_from_qmt()`
   - QMT失败后依次尝试Akshare、Tushare

11. **更新方法：`get_financial_data()`**
   - 优先调用 `_fetch_financial_data_from_qmt()`
   - QMT失败后依次尝试Akshare、Tushare

### 2. `backend/test_qmt_data_source.py` (新建)

创建了完整的测试脚本，包含四个测试函数：

1. **`test_historical_data()`** - 测试历史数据获取
2. **`test_basic_info()`** - 测试基本信息获取
3. **`test_realtime_quotes()`** - 测试实时行情获取
4. **`test_financial_data()`** - 测试财务数据获取

## 技术细节

### QMT API使用

1. **历史数据获取**
   ```python
   xtdata.get_market_data_ex(
       field_list=['time', 'open', 'high', 'low', 'close', 'volume', 'amount'],
       stock_list=[full_code],
       period='1d',
       start_time=start_date,
       end_time=end_date,
       dividend_type='front'  # 前复权
   )
   ```

2. **基本信息获取**
   ```python
   xtdata.get_instrument_detail(full_code)
   ```

3. **实时行情获取**
   ```python
   xtdata.get_full_tick([full_code])
   ```

4. **财务数据获取**
   ```python
   xtdata.get_financial_data(
       stock_code=full_code,
       table_list=['Income'],  # 或 'Balance', 'CashFlow'
       start_time='',
       end_time=''
   )
   ```

### 股票代码格式化

QMT要求股票代码带市场后缀：
- 上海市场（6开头）：`600519.SH`
- 深圳市场（0、3开头）：`000001.SZ`、`300001.SZ`

### 复权类型映射

| 参数 | QMT格式 | 说明 |
|------|---------|------|
| 'qfq' | 'front' | 前复权 |
| 'hfq' | 'back' | 后复权 |
| '' | 'none' | 不复权 |

### 财务报表类型映射

| 参数 | QMT格式 | 说明 |
|------|---------|------|
| 'income' | 'Income' | 利润表 |
| 'balance' | 'Balance' | 资产负债表 |
| 'cashflow' | 'CashFlow' | 现金流量表 |

## 数据字段映射

### 历史数据字段

| 标准字段 | QMT字段 | 说明 |
|----------|---------|------|
| date | time | 日期（毫秒时间戳） |
| open | open | 开盘价 |
| high | high | 最高价 |
| low | low | 最低价 |
| close | close | 收盘价 |
| volume | volume | 成交量 |
| amount | amount | 成交额 |
| pct_change | - | 涨跌幅（计算得出） |
| change | - | 涨跌额（计算得出） |
| amplitude | - | 振幅（计算得出） |

### 基本信息字段

| 标准字段 | QMT字段 | 说明 |
|----------|---------|------|
| name | InstrumentName | 股票名称 |
| industry | IndustryName | 所属行业 |
| market | ExchangeID | 交易所代码 |
| list_date | OpenDate | 上市日期 |
| up_stop_price | UpStopPrice | 涨停价 |
| down_stop_price | DownStopPrice | 跌停价 |
| float_volume | FloatVolume | 流通股本 |
| total_volume | TotalVolume | 总股本 |

### 实时行情字段

| 标准字段 | QMT字段 | 说明 |
|----------|---------|------|
| price | lastPrice | 最新价 |
| open | open | 开盘价 |
| high | high | 最高价 |
| low | low | 最低价 |
| pre_close | lastClose | 昨收价 |
| volume | volume | 成交量 |
| amount | amount | 成交额 |
| change | - | 涨跌额（计算得出） |
| change_percent | - | 涨跌幅（计算得出） |

### 财务数据字段

QMT财务数据返回格式为嵌套字典，自动转换为DataFrame：

**利润表 (Income) 主要字段：**
- revenue - 营业收入
- netProfit - 净利润
- netProfitExclMinIntInc - 归母净利润
- operProfit - 营业利润
- totProfit - 利润总额
- totalOperCost - 营业总成本
- saleExpense - 销售费用
- financialExpense - 财务费用
- lessGerlAdminExp - 管理费用

**资产负债表 (Balance) 主要字段：**
- totalAssets - 资产总计
- totalLiab - 负债合计
- totalEquity - 股东权益合计
- currentAssets - 流动资产合计
- nonCurrentAssets - 非流动资产合计
- currentLiab - 流动负债合计
- nonCurrentLiab - 非流动负债合计

**现金流量表 (CashFlow) 主要字段：**
- netCashFlowOper - 经营活动产生的现金流量净额
- netCashFlowInv - 投资活动产生的现金流量净额
- netCashFlowFin - 筹资活动产生的现金流量净额
- netCashFlow - 现金及现金等价物净增加额

## 使用方法

### 1. 确保QMT已安装并配置

```python
# QMT会在初始化时自动尝试连接
from app.data.data_source import data_source_manager

# 检查QMT是否可用
if data_source_manager.qmt_available:
    print("QMT数据源可用")
else:
    print("QMT数据源不可用，将使用备用数据源")
```

### 2. 获取历史数据

```python
df = data_source_manager.get_stock_hist_data(
    symbol="600519",
    start_date="20240101",
    end_date="20241231",
    adjust='qfq'  # 前复权
)
```

### 3. 获取基本信息

```python
info = data_source_manager.get_stock_basic_info("600519")
print(f"股票名称: {info['name']}")
print(f"所属行业: {info['industry']}")
```

### 4. 获取实时行情

```python
quotes = data_source_manager.get_realtime_quotes("600519")
print(f"最新价: {quotes['price']}")
print(f"涨跌幅: {quotes['change_percent']}%")
```

### 5. 获取财务数据

```python
# 获取利润表
df = data_source_manager.get_financial_data("600519", report_type='income')

# 获取资产负债表
df = data_source_manager.get_financial_data("600519", report_type='balance')

# 获取现金流量表
df = data_source_manager.get_financial_data("600519", report_type='cashflow')
```

## 测试方法

运行测试脚本：

```bash
cd backend
python test_qmt_data_source.py
```

测试脚本会依次测试：
1. 历史数据获取
2. 基本信息获取
3. 实时行情获取
4. 财务数据获取

并显示每个测试的结果。

## 容错机制

所有QMT数据获取方法都包含完整的异常处理：

1. 如果QMT不可用，自动跳过QMT，使用下一个数据源
2. 如果QMT获取失败，打印错误信息并尝试备用数据源
3. 所有数据源都失败时，返回None或空字典

## 优势

1. **速度快** - QMT本地数据，无需网络请求
2. **数据全** - 支持历史数据、实时行情、基本信息、财务数据
3. **稳定性高** - 本地数据源，不受网络限制
4. **无需积分** - 不像Tushare需要积分限制
5. **自动降级** - QMT不可用时自动使用其他数据源
6. **数据标准** - QMT财务数据字段完整，符合官方标准

## 注意事项

1. QMT需要先安装并配置好xtquant模块
2. QMT需要连接到数据服务才能获取数据
3. 如果QMT未安装，系统会自动使用其他数据源
4. 建议在交易时段使用QMT获取实时数据，效果最佳

## 后续优化建议

1. 添加QMT数据缓存机制
2. 支持批量获取多只股票数据
3. 添加QMT连接状态监控
4. 支持更多QMT数据类型（如分钟线、财务数据等）
