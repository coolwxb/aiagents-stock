# Requirements Document

## Introduction

GS策略模块是一个基于中枢G买卖信号的自动化交易系统。该模块允许用户管理股票池、设置监控参数、自动执行GS策略买卖信号，并通过QMT接口进行实际交易。系统提供完整的持仓管理和历史统计功能，帮助用户追踪策略执行效果和收益情况。

## Glossary

- **GS策略**: 基于中枢G买卖信号的量化交易策略，通过计算BB基线和中枢A来生成买卖信号
- **股票池**: 用户手动添加的待监控股票列表
- **监控队列**: 正在执行GS策略监控的股票列表
- **QMT**: 迅投MiniQMT量化交易接口，用于执行实际买卖操作
- **监测间隔**: 执行GS策略分析的时间间隔（秒）
- **买卖信号**: GS策略计算产生的g_buy（买入信号）和g_sell（卖出信号）
- **完整交易**: 一次完整的买入-卖出交易周期

## Requirements

### Requirement 1

**User Story:** As a user, I want to manage a stock pool for GS strategy, so that I can organize stocks I want to monitor with the GS strategy.

#### Acceptance Criteria

1. WHEN a user adds a stock to the stock pool THEN the GS_Strategy_System SHALL store the stock code, stock name, and creation timestamp
2. WHEN a user views the stock pool THEN the GS_Strategy_System SHALL display all stocks with their code, name, add time, and operation buttons
3. WHEN a user removes a stock from the stock pool THEN the GS_Strategy_System SHALL delete the stock record and remove it from any active monitoring
4. WHEN a user searches for a stock by code or name THEN the GS_Strategy_System SHALL filter and display matching stocks in the pool
5. WHEN a user adds a duplicate stock code THEN the GS_Strategy_System SHALL reject the addition and display an error message

### Requirement 2

**User Story:** As a user, I want to add stocks from the pool to the monitoring queue with custom intervals, so that I can execute GS strategy automatically.

#### Acceptance Criteria

1. WHEN a user clicks "Add to Monitor" for a stock THEN the GS_Strategy_System SHALL display a dialog to configure monitoring interval
2. WHEN a user confirms monitoring configuration THEN the GS_Strategy_System SHALL create a monitoring task with the specified interval and start monitoring
3. WHEN a monitoring task is created THEN the GS_Strategy_System SHALL record the start time and initialize execution count to zero
4. WHEN the monitoring interval elapses THEN the GS_Strategy_System SHALL execute the GS strategy analysis for that stock
5. WHEN a stock is already in the monitoring queue THEN the GS_Strategy_System SHALL prevent duplicate monitoring and display a warning

### Requirement 3

**User Story:** As a user, I want the system to execute trades based on GS strategy signals, so that I can automate my trading decisions.

#### Acceptance Criteria

1. WHEN the GS strategy generates a buy signal (g_buy=1) THEN the GS_Strategy_System SHALL call the QMT buy interface with the configured parameters
2. WHEN the GS strategy generates a sell signal (g_sell=1) THEN the GS_Strategy_System SHALL call the QMT sell interface for the held position
3. WHEN a QMT order is successfully placed THEN the GS_Strategy_System SHALL send a notification via the configured notification channel
4. WHEN a QMT order fails THEN the GS_Strategy_System SHALL log the error and send a failure notification
5. WHEN a trade is executed THEN the GS_Strategy_System SHALL record the trade details including stock code, action, price, quantity, and timestamp

### Requirement 4

**User Story:** As a user, I want to manage the monitoring queue, so that I can control which stocks are being actively monitored.

#### Acceptance Criteria

1. WHEN a user views the monitoring management tab THEN the GS_Strategy_System SHALL display all monitored stocks with code, name, start time, running duration, and execution count
2. WHEN a user pauses a monitoring task THEN the GS_Strategy_System SHALL stop the strategy execution while preserving the task configuration
3. WHEN a user resumes a paused monitoring task THEN the GS_Strategy_System SHALL restart the strategy execution with the existing configuration
4. WHEN a user removes a stock from monitoring THEN the GS_Strategy_System SHALL stop the monitoring task and delete it from the queue
5. WHEN the running duration is displayed THEN the GS_Strategy_System SHALL calculate and show the elapsed time since monitoring started

### Requirement 5

**User Story:** As a user, I want to view my current QMT positions, so that I can understand my portfolio status.

#### Acceptance Criteria

1. WHEN a user views the position management tab THEN the GS_Strategy_System SHALL display all current QMT positions
2. WHEN displaying positions THEN the GS_Strategy_System SHALL show stock code, name, quantity, cost price, current price, profit/loss amount, and profit/loss percentage
3. WHEN QMT is not connected THEN the GS_Strategy_System SHALL display a connection status message and empty position list
4. WHEN a user refreshes positions THEN the GS_Strategy_System SHALL fetch the latest position data from QMT

### Requirement 6

**User Story:** As a user, I want to view historical trading statistics, so that I can analyze the performance of the GS strategy.

#### Acceptance Criteria

1. WHEN a user views the history statistics tab THEN the GS_Strategy_System SHALL display all completed trade cycles
2. WHEN displaying trade history THEN the GS_Strategy_System SHALL show stock code, name, buy price, buy time, sell price, sell time, profit/loss amount, and profit/loss percentage
3. WHEN a trade cycle is completed (buy followed by sell) THEN the GS_Strategy_System SHALL calculate and record the profit/loss
4. WHEN displaying statistics THEN the GS_Strategy_System SHALL show total trades, winning trades, losing trades, total profit/loss, and win rate
5. WHEN a user filters history by date range THEN the GS_Strategy_System SHALL display only trades within the specified period

### Requirement 7

**User Story:** As a user, I want the GS strategy page to have a tabbed interface, so that I can easily navigate between different functions.

#### Acceptance Criteria

1. WHEN a user navigates to the GS Strategy page THEN the GS_Strategy_System SHALL display four tabs: Stock Pool, Monitor Management, Position Management, and History Statistics
2. WHEN a user clicks on a tab THEN the GS_Strategy_System SHALL switch to display the corresponding content
3. WHEN the page loads THEN the GS_Strategy_System SHALL default to showing the Stock Pool tab
4. WHEN switching tabs THEN the GS_Strategy_System SHALL preserve the state of other tabs

### Requirement 8

**User Story:** As a developer, I want the GS strategy data to be persisted in the database, so that the system state is preserved across restarts.

#### Acceptance Criteria

1. WHEN a stock is added to the pool THEN the GS_Strategy_System SHALL persist the record to the gs_stock_pool table
2. WHEN a monitoring task is created THEN the GS_Strategy_System SHALL persist the task to the gs_monitor_tasks table
3. WHEN a trade is executed THEN the GS_Strategy_System SHALL persist the trade record to the gs_trade_history table
4. WHEN the system restarts THEN the GS_Strategy_System SHALL restore all monitoring tasks that were in running state
5. WHEN serializing trade records to the database THEN the GS_Strategy_System SHALL encode them using JSON format for complex fields
6. WHEN deserializing trade records from the database THEN the GS_Strategy_System SHALL decode JSON fields back to their original structure
