# Implementation Plan

## Backend Implementation

- [x] 1. Create database models for GS Strategy
  - [x] 1.1 Create GSStockPool model in `backend/app/models/gs_strategy.py`
    - Define id, stock_code (unique), stock_name, created_at, updated_at fields
    - Add index on stock_code for fast lookup
    - _Requirements: 1.1, 8.1_
  - [x] 1.2 Create GSMonitorTask model
    - Define id, stock_pool_id (FK), stock_code, stock_name, interval, status, started_at, execution_count, last_signal, last_signal_time, created_at, updated_at
    - Add index on stock_code and status
    - _Requirements: 2.2, 2.3, 8.2_
  - [x] 1.3 Create GSTradeHistory model
    - Define id, monitor_id (FK), stock_code, stock_name, buy_price, buy_quantity, buy_time, buy_order_id, sell_price, sell_quantity, sell_time, sell_order_id, profit_loss, profit_loss_pct, status, trade_details (JSON), created_at, updated_at
    - _Requirements: 3.5, 6.2, 8.3_
  - [ ]* 1.4 Write property test for data models
    - **Property 14: JSON Serialization Round Trip**
    - **Validates: Requirements 8.5, 8.6**

- [x] 2. Create GS Strategy Service
  - [x] 2.1 Create `backend/app/services/gs_strategy_service.py` with GSStrategyService class
    - Implement constructor with database session injection
    - _Requirements: 1.1, 2.2_
  - [x] 2.2 Implement stock pool management methods
    - `get_stock_pool()` - return all stocks with required fields
    - `add_to_stock_pool(stock_code, stock_name)` - add with duplicate check
    - `remove_from_stock_pool(stock_id)` - delete and cascade to monitors
    - `search_stock_pool(keyword)` - filter by code or name
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [ ]* 2.3 Write property tests for stock pool methods
    - **Property 1: Stock Pool Data Integrity**
    - **Property 2: Stock Pool Uniqueness**
    - **Property 3: Stock Pool Search Consistency**
    - **Property 4: Stock Removal Cascades to Monitoring**
    - **Validates: Requirements 1.1, 1.3, 1.4, 1.5, 8.1**
  - [x] 2.4 Implement monitor management methods
    - `get_monitors()` - return all monitors with running duration calculation
    - `create_monitor(stock_id, interval)` - create with duplicate check
    - `update_monitor(monitor_id, data)` - update interval and other settings
    - `delete_monitor(monitor_id)` - stop and delete
    - `start_monitor(monitor_id)` - set status to running, update started_at
    - `stop_monitor(monitor_id)` - set status to stopped, preserve config
    - _Requirements: 2.2, 2.3, 2.5, 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ]* 2.5 Write property tests for monitor methods
    - **Property 5: Monitor Task Initialization**
    - **Property 6: Monitor Uniqueness Per Stock**
    - **Property 7: Monitor Pause Preserves Configuration**
    - **Property 8: Monitor Resume Restores Running State**
    - **Property 15: Running Duration Calculation**
    - **Validates: Requirements 2.2, 2.3, 2.5, 4.2, 4.3, 4.5**
  - [x] 2.6 Implement position and history methods
    - `get_positions()` - delegate to QMT service
    - `get_trade_history(start_date, end_date)` - filter by date range
    - `get_statistics()` - calculate total, wins, losses, profit, win_rate
    - `record_trade(monitor_id, action, price, quantity, order_id)` - save trade
    - `complete_trade(trade_id, sell_price, sell_quantity, sell_order_id)` - calculate P/L
    - _Requirements: 5.1, 5.2, 6.1, 6.2, 6.3, 6.4, 6.5_
  - [ ]* 2.7 Write property tests for history and statistics
    - **Property 9: Trade Record Completeness**
    - **Property 10: Profit/Loss Calculation Accuracy**
    - **Property 11: Statistics Consistency**
    - **Property 12: Date Range Filter Accuracy**
    - **Property 13: Position Data Completeness**
    - **Validates: Requirements 3.5, 5.2, 6.3, 6.4, 6.5**

- [x] 3. Create GS Scheduler for monitoring execution
  - [x] 3.1 Create `backend/app/services/gs_scheduler.py` with GSScheduler class
    - Implement singleton pattern with class-level thread management
    - Define _monitoring_threads and _stop_flags dictionaries
    - _Requirements: 2.4_
  - [x] 3.2 Implement monitor thread management
    - `start_monitor(monitor_id, interval)` - create and start monitoring thread
    - `stop_monitor(monitor_id)` - set stop flag and wait for thread
    - `_monitor_loop(monitor_id, interval, stop_flag)` - main loop with interval wait
    - _Requirements: 2.4, 4.2, 4.3_
  - [x] 3.3 Implement strategy execution logic
    - `_execute_strategy(stock_code)` - call GS strategy compute_g_buy_sell
    - `_handle_buy_signal(stock_code, signal_data)` - call QMT buy, record trade, notify
    - `_handle_sell_signal(stock_code, signal_data)` - call QMT sell, complete trade, notify
    - Integrate with existing `backend/app/policy/gs.py` for signal generation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - [x] 3.4 Implement system restart recovery
    - `restore_running_monitors()` - query running tasks and restart threads
    - Call this method during application startup
    - _Requirements: 8.4_

- [ ] 4. Checkpoint - Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Create GS Strategy API Router
  - [x] 5.1 Create `backend/app/api/v1/gs_strategy.py` with router
    - Import GSStrategyService and dependencies
    - _Requirements: All API requirements_
  - [x] 5.2 Implement stock pool endpoints
    - GET `/stock-pool` - list all stocks
    - POST `/stock-pool` - add stock (validate code format)
    - DELETE `/stock-pool/{id}` - remove stock
    - GET `/stock-pool/search` - search by keyword
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 5.3 Implement monitor endpoints
    - GET `/monitors` - list all monitors
    - POST `/monitors` - create monitor
    - PUT `/monitors/{id}` - update monitor
    - DELETE `/monitors/{id}` - delete monitor
    - POST `/monitors/{id}/start` - start monitoring
    - POST `/monitors/{id}/stop` - stop monitoring
    - _Requirements: 2.2, 4.1, 4.2, 4.3, 4.4_
  - [x] 5.4 Implement position and history endpoints
    - GET `/positions` - get QMT positions
    - GET `/history` - get trade history with date filter
    - GET `/statistics` - get statistics summary
    - _Requirements: 5.1, 6.1, 6.4_
  - [x] 5.5 Register router in `backend/app/api/v1/router.py`
    - Add import for gs_strategy module
    - Include router with prefix "/gs-strategy" and tags ["GS策略"]
    - _Requirements: All API requirements_

- [x] 6. Create database migration
  - [x] 6.1 Create Alembic migration for GS Strategy tables
    - Generate migration file for gs_stock_pool, gs_monitor_tasks, gs_trade_history
    - Run migration to create tables
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 7. Checkpoint - Ensure backend API tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Frontend Implementation

- [x] 8. Create frontend API module
  - [x] 8.1 Create `frontend/src/api/gs-strategy.js`
    - Implement getStockPool, addToStockPool, removeFromStockPool, searchStockPool
    - Implement getMonitors, createMonitor, updateMonitor, deleteMonitor, startMonitor, stopMonitor
    - Implement getPositions, getTradeHistory, getStatistics
    - _Requirements: All frontend API requirements_

- [x] 9. Create GS Strategy page components
  - [x] 9.1 Create main page `frontend/src/views/gs-strategy/index.vue`
    - Implement tab container with 4 tabs
    - Default to Stock Pool tab on load
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [x] 9.2 Create StockPoolTab component
    - Stock list table with code, name, add time, operations
    - Add stock dialog with code and name inputs
    - Search input for filtering
    - "Add to Monitor" button with interval config dialog
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1_
  - [x] 9.3 Create MonitorTab component
    - Monitor list table with code, name, start time, duration, execution count, status
    - Pause/Resume/Remove action buttons
    - Real-time duration update using setInterval
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [x] 9.4 Create PositionTab component
    - Account summary cards (total value, available cash, positions count, total P/L)
    - Position table with all required fields
    - Refresh button
    - Connection status display
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 9.5 Create HistoryTab component
    - Trade history table with all required fields
    - Statistics summary cards (total trades, win rate, total P/L)
    - Date range picker for filtering
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

- [x] 10. Add route configuration
  - [x] 10.1 Update `frontend/src/router/index.js`
    - Add GS Strategy route under /management path
    - Configure menu item with title "GS策略" and icon
    - _Requirements: 7.1_

- [x] 11. Checkpoint - Ensure frontend builds without errors
  - Ensure all tests pass, ask the user if questions arise.

## Integration and Final Testing

- [ ] 12. Integration testing
  - [ ] 12.1 Test complete workflow
    - Add stock to pool → Add to monitor → Verify monitoring starts
    - Pause/Resume monitor → Verify status changes
    - Remove from pool → Verify cascade deletion
    - _Requirements: 1.3, 2.2, 4.2, 4.3, 4.4_
  - [ ]* 12.2 Write integration tests for QMT trading flow
    - Mock QMT service for buy/sell operations
    - Verify notification is sent on successful trade
    - Verify trade history is recorded
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 13. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
