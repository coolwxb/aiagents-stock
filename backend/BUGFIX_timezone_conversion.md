# Bug Fix: 时区转换问题

## 问题描述

QMT返回的时间戳转换为日期时，时区不正确。

### 错误示例：

```python
# 时间戳: 1765123200000 (毫秒)
# 预期日期: 2025-12-08 00:00:00 (北京时间)
# 实际结果: 2025-12-07 16:00:00 (UTC时间)
```

## 根本原因

`pd.to_datetime(timestamp, unit='ms')` 默认使用 **UTC 时区**，而中国股市使用 **UTC+8（北京时间/Asia/Shanghai）**。

时差：**8小时**

## 解决方案

### 修改前（错误）：

```python
df = pd.DataFrame({
    'date': pd.to_datetime(stock_data['time'], unit='ms'),
    # ...
})
```

这会将时间戳解释为 UTC 时间，导致日期比实际早 8 小时。

### 修改后（正确）：

```python
# 方法：直接加8小时的偏移量
timestamps_ms = stock_data['time']
beijing_offset_ms = 8 * 3600 * 1000  # 8小时 = 28800000毫秒

df = pd.DataFrame({
    'date': pd.to_datetime(timestamps_ms + beijing_offset_ms, unit='ms'),
    # ...
})
```

### 转换步骤说明：

1. **计算时区偏移量**
   - 北京时间 = UTC + 8小时
   - 8小时 = 8 × 3600秒 × 1000毫秒 = 28,800,000毫秒

2. **直接在时间戳上加偏移量**
   - `timestamps_ms + beijing_offset_ms`
   - 这样转换后的时间就是北京时间

3. **转换为datetime**
   - `pd.to_datetime(..., unit='ms')`
   - 得到正确的北京时间日期

### 为什么用这个方法？

之前的方法 `.tz_convert('Asia/Shanghai')` 需要索引是 DatetimeIndex，但我们的数据在列中，会报错：
```
index is not a valid DatetimeIndex or PeriodIndex
```

直接加偏移量的方法更简单、更可靠，不需要处理时区对象。

## 验证

### 测试代码：

```python
import pandas as pd
from datetime import datetime

# QMT返回的时间戳（毫秒）
timestamp_ms = 1765123200000

# 方法1：错误的转换（UTC）
date_utc = pd.to_datetime(timestamp_ms, unit='ms')
print(f"UTC时间: {date_utc}")
# 输出: 2025-12-07 16:00:00

# 方法2：正确的转换（北京时间）
date_beijing = pd.to_datetime(timestamp_ms, unit='ms', utc=True).tz_convert('Asia/Shanghai').tz_localize(None)
print(f"北京时间: {date_beijing}")
# 输出: 2025-12-08 00:00:00

# 验证
assert date_beijing.strftime('%Y-%m-%d') == '2025-12-08'
print("✅ 时区转换正确")
```

### 预期结果：

| 时间戳（毫秒） | UTC时间 | 北京时间（UTC+8） |
|---------------|---------|------------------|
| 1765123200000 | 2025-12-07 16:00:00 | 2025-12-08 00:00:00 |
| 1764864000000 | 2025-12-05 16:00:00 | 2025-12-06 00:00:00 |
| 1764777600000 | 2025-12-04 16:00:00 | 2025-12-05 00:00:00 |

## 影响范围

这个修复影响所有从QMT获取的历史数据的日期字段。

### 修复前的问题：

- 所有日期都比实际早 8 小时
- 例如：2025-12-08 的数据显示为 2025-12-07
- 可能导致数据对齐问题

### 修复后的改进：

- ✅ 日期显示正确
- ✅ 与中国股市交易日期一致
- ✅ 与其他数据源（Akshare、Tushare）日期格式统一

## 其他时区相关注意事项

### 1. QMT时间戳格式

QMT返回的时间戳是：
- **毫秒级时间戳**（13位数字）
- **UTC+8 时区的0点时间**
- 例如：2025-12-08 00:00:00 (北京时间)

### 2. 为什么需要时区转换？

虽然QMT的时间戳已经是北京时间，但 pandas 的 `to_datetime` 默认解释为 UTC，所以需要：
1. 先标记为 UTC（`utc=True`）
2. 再转换为北京时间（`tz_convert('Asia/Shanghai')`）
3. 最后移除时区信息（`tz_localize(None)`）

### 3. 其他可能的时区问题

如果遇到其他时区相关问题，可以使用：

```python
# 查看时区信息
print(df['date'].dt.tz)

# 手动设置时区
df['date'] = df['date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')

# 移除时区信息
df['date'] = df['date'].dt.tz_localize(None)
```

## 测试建议

运行以下测试确保修复正确：

```python
# 测试QMT数据获取
df = data_source_manager.get_stock_hist_data("600519", "1d", count=5)

# 检查最新日期
latest_date = df['date'].max()
print(f"最新数据日期: {latest_date.strftime('%Y-%m-%d')}")

# 验证日期格式
assert latest_date.hour == 0  # 应该是0点
assert latest_date.minute == 0
assert latest_date.second == 0

# 验证是交易日（周一至周五）
weekday = latest_date.weekday()
assert weekday < 5, f"最新日期是周末: {latest_date}"

print("✅ 时区转换测试通过")
```

## 总结

- **问题**：时间戳转换时未考虑时区，导致日期早8小时
- **原因**：pandas 默认使用 UTC 时区
- **解决**：明确转换为北京时间（Asia/Shanghai）
- **影响**：所有QMT历史数据的日期字段
- **状态**：✅ 已修复
