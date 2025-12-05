import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf

from xtquant import xtdata


# =============================
# 常用指标函数
# =============================
def MA(series, n):
    return series.rolling(n).mean()

def EMA(series, n):
    return series.ewm(span=n, adjust=False).mean()

def REF(series, n):
    return series.shift(n)

def CROSS(a, b):
    return (a > b) & (a.shift(1) <= b.shift(1))


# =============================================================
# ⭐ 中枢 G 买卖信号 - 最简核心算法
# =============================================================
def compute_g_buy_sell(df):
    out = df.copy()

    O = out["open"].astype(float)
    H = out["high"].astype(float)
    L = out["low"].astype(float)
    C = out["close"].astype(float)

    # ======== 基线 BB ========
    BB0 = (MA(C, 3) + MA(C, 7) + MA(C, 13) + MA(C, 27)) / 4
    BB1 = EMA(C, 5)
    BB = BB0.fillna(BB1)
    out["BB"] = BB

    # ======== 中枢 A ========
    A = (H + L + 2 * O + 6 * C) / 10
    refC = REF(C, 1).replace(0, np.nan)

    TK = (
        (C < O)
        | ((C < REF(H, 1)) & (C > O))
        | ((C >= O) & ((H - C) >= (C - O)) & (C / refC < 1.02))
        | ((C == O) & ((H - C) >= (C - L)) & (C / refC < 1.05))
    )

    TP = (
        ((C > O) & (C / refC > 0.94))
        | ((C > REF(L, 1)) & (C < O))
        | ((C <= O) & ((C - L) >= (O - C)) & (C / refC > 0.98))
        | ((C == O) & ((C - L) >= (H - C)) & (C / refC > 0.95))
    )

    # A iterative update
    for _ in range(10):
        up_cross = CROSS(A, BB) & TK
        dn_cross = CROSS(BB, A) & TP
        A = np.where(up_cross, BB * 0.98, np.where(dn_cross, BB * 1.02, A))
        A = pd.Series(A, index=out.index)

    out["A"] = A

    # ======== 生成信号 ========
    KK0 = CROSS(A, BB)
    PP0 = CROSS(BB, A)

    ZF = (C / refC - 1) * 100
    ZJ = (A / BB - 1) * 100

    K_zone = A >= BB
    P_zone = A < BB

    TCY = K_zone & (
        ((C >= REF(H, 1)) & (((H - C) < (C - O)) | (ZF >= 7))) |
        ((C < REF(H, 1)) & (C < O) & (ZF > -3) & (ZJ >= 10))
    )

    TKC = P_zone & (
        (C < REF(L, 1)) |
        ((C > REF(L, 1)) & (C > O) & (ZF < 3) & (ZJ <= -10))
    )

    out["g_buy"] = (KK0 & TCY).astype(int)
    out["g_sell"] = (PP0 & TKC).astype(int)

    return out


# =============================================================
# ⭐ XTQUANT 获取历史 K 线
# =============================================================
def load_xtquant_kline(stock_code, end_date, period='1d', count=200):
    """
    stock_code: 如 '600000.SH'
    end_date: '2024-12-31'
    """
    # 将日期格式转换为YYYYMMDD
    if '-' in end_date:
        end_date_yyyymmdd = end_date.replace('-', '')
    else:
        end_date_yyyymmdd = end_date
    xtdata.subscribe_quote(stock_code, period='1d', start_time='', end_time=end_date_yyyymmdd, count=0, callback=None)
    
    # 使用get_market_data_ex方法获取数据
    data = xtdata.get_market_data_ex(
        field_list=["time", "open", "high", "low", "close", "volume"],
        stock_list=[stock_code],
        period=period,
        end_time=end_date_yyyymmdd,
        count=count,
        dividend_type='none'
    )
    print(data)
    
    # 检查是否有数据返回
    if not data or stock_code not in data:
        print(f"未能获取到股票 {stock_code} 的数据，正在尝试下载历史数据...")
     
        # 下载历史数据
        xtdata.download_history_data(stock_code, period, '20250101', end_date_yyyymmdd)
        print(f"历史数据下载完成，重新获取数据...")
        
        # 重新获取数据
        data = xtdata.get_market_data(
            field_list=["time", "open", "high", "low", "close", "volume"],
            stock_list=[stock_code],
            period=period,
            end_time=end_date_yyyymmdd,
            count=count,
            dividend_type='none'
        )
        
        # 再次检查是否有数据返回
        if not data or stock_code not in data:
            print(f"即使下载了历史数据，仍然未能获取到股票 {stock_code} 的数据")
            return pd.DataFrame()  # 返回空的DataFrame
        else:
            print(f"重新获取数据成功，数据包含股票: {list(data.keys())}")
    
    # 添加调试信息
    stock_data = data[stock_code]
    print(f"数据列名: {list(stock_data.columns)}")
    print(f"原始数据条数: {len(stock_data)}")
    if stock_data.empty:
        print("警告: 获取到的数据是空的")
        return pd.DataFrame()  # 返回空的DataFrame而不是继续处理
    
    # 提取数据并创建DataFrame
    stock_data = data[stock_code]
    df = pd.DataFrame({
        "open": stock_data["open"].values,
        "high": stock_data["high"].values,
        "low": stock_data["low"].values,
        "close": stock_data["close"].values,
        "volume": stock_data["volume"].values,
        "time": stock_data["time"].values,
    })

    # 使用日期列作为索引，因为它更符合用户的预期
    date_values = stock_data.index.values
    print(f"前5个日期值: {date_values[:5]}")
    print(f"后5个日期值: {date_values[-5:]}")
    
    # 将日期字符串转换为日期时间索引
    df.index = pd.to_datetime(date_values, format='%Y%m%d')
    
    print(f"解析后的时间范围: {df.index.min()} 到 {df.index.max()}")
    
    # 确保数据包含截止日期
    print(f"请求的截止日期: {end_date_yyyymmdd}")
    return df


# =============================================================
# ⭐ 最简 T+1 回测
# =============================================================
def simple_backtest(df):
    df = df.copy()
    df["pos"] = 0
    df["trade"] = ""

    holding = False
    buy_price = 0

    for i in range(1, len(df) - 1):
        today = df.index[i]
        next_day = df.index[i + 1]

        if not holding and df.loc[today, "g_buy"] == 1:
            # T+1 次日开盘买入
            df.loc[next_day, "pos"] = 1
            df.loc[next_day, "trade"] = "BUY"
            buy_price = df.loc[next_day, "open"]
            holding = True

        elif holding and df.loc[today, "g_sell"] == 1:
            # T+1 次日开盘卖出
            df.loc[next_day, "pos"] = 0
            df.loc[next_day, "trade"] = "SELL"
            holding = False

        else:
            df.loc[next_day, "pos"] = df.loc[today, "pos"]
    
    # 处理最后一个数据点
    if len(df) > 1:
        last_day = df.index[-1]
        second_last_day = df.index[-2]
        df.loc[last_day, "pos"] = df.loc[second_last_day, "pos"]

    return df


# =============================================================
# ⭐ 绘图：K线 + A/BB + 买卖信号
# =============================================================
def plot_g_signals(df):

    df_plot = df.copy()

    df_plot["buy_signal"] = df_plot["low"] * 0.98
    df_plot["buy_signal"] = df_plot["buy_signal"].where(df_plot["g_buy"] == 1)

    df_plot["sell_signal"] = df_plot["high"] * 1.02
    df_plot["sell_signal"] = df_plot["sell_signal"].where(df_plot["g_sell"] == 1)

    apds = [
        mpf.make_addplot(df_plot["A"], color='blue'),
        mpf.make_addplot(df_plot["BB"], color='orange'),
        mpf.make_addplot(df_plot["buy_signal"], type='scatter', marker='^', markersize=100, color='red'),
        mpf.make_addplot(df_plot["sell_signal"], type='scatter', marker='v', markersize=100, color='green'),
    ]

    # 确保索引是日期时间格式
    df_plot.index = pd.to_datetime(df_plot.index)
    
    # 创建红涨绿跌的颜色方案
    mc = mpf.make_marketcolors(up='red', down='green', edge='inherit', wick='inherit', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    
    # 绘制图表，x轴显示日期，使用红涨绿跌的颜色方案
    mpf.plot(df_plot, type='candle', style=s, addplot=apds, figsize=(18, 10), 
             datetime_format='%Y-%m-%d', xrotation=45)


# =============================================================
# ⭐ 主流程
# =============================================================
if __name__ == "__main__":

    stock = "688333.SH"  # 使用贵航股份作为测试股票
    df = load_xtquant_kline(stock, end_date="20251205", period='1d', count=200)  # 使用指定的截止日期
    
    # 检查是否获取到数据
    if df.empty:
        print(f"未能获取到 {stock} 的历史数据，请检查股票代码和日期设置。")
    else:
        print(f"成功获取到 {stock} 的历史数据，共 {len(df)} 条记录")
        df2 = compute_g_buy_sell(df)
        df_bt = simple_backtest(df2)

        print("最近20条回测记录:")
        print(df_bt[["open", "close", "g_buy", "g_sell", "trade"]].tail(20))

        # 输出CSV文件
        csv_filename = f"{stock}_analysis.csv"
        df_bt.to_csv(csv_filename, encoding='utf-8-sig')
        print(f"分析结果已保存到 {csv_filename}")
        
        # 绘图
        print("正在绘制图表...")
        plot_g_signals(df_bt)
        print("图表绘制完成")
