import request from '@/utils/request'

// ==================== 股票池管理 ====================

/**
 * 获取股票池列表
 * @param {Object} params - 查询参数
 * @returns {Promise} 股票池列表
 */
export function getStockPool(params) {
  return request({
    url: '/api/v1/gs-strategy/stock-pool',
    method: 'get',
    params
  })
}

/**
 * 添加股票到股票池
 * @param {Object} data - 股票信息 { stock_code, stock_name }
 * @returns {Promise} 添加结果
 */
export function addToStockPool(data) {
  return request({
    url: '/api/v1/gs-strategy/stock-pool',
    method: 'post',
    data
  })
}

/**
 * 从股票池中删除股票
 * @param {number} id - 股票池记录ID
 * @returns {Promise} 删除结果
 */
export function removeFromStockPool(id) {
  return request({
    url: `/api/v1/gs-strategy/stock-pool/${id}`,
    method: 'delete'
  })
}

/**
 * 搜索股票池
 * @param {string} keyword - 搜索关键词（股票代码或名称）
 * @returns {Promise} 匹配的股票列表
 */
export function searchStockPool(keyword) {
  return request({
    url: '/api/v1/gs-strategy/stock-pool/search',
    method: 'get',
    params: { keyword }
  })
}

/**
 * 获取股票信息
 * @param {string} stockCode - 股票代码
 * @returns {Promise} 股票信息（包含股票名称）
 */
export function getStockInfo(stockCode) {
  return request({
    url: `/api/v1/gs-strategy/stock-info/${stockCode}`,
    method: 'get'
  })
}

// ==================== 监控任务管理 ====================

/**
 * 获取监控任务列表
 * @param {Object} params - 查询参数
 * @returns {Promise} 监控任务列表
 */
export function getMonitors(params) {
  return request({
    url: '/api/v1/gs-strategy/monitors',
    method: 'get',
    params
  })
}

/**
 * 创建监控任务
 * @param {Object} data - 监控配置 { stock_id, interval }
 * @returns {Promise} 创建的监控任务
 */
export function createMonitor(data) {
  return request({
    url: '/api/v1/gs-strategy/monitors',
    method: 'post',
    data
  })
}

/**
 * 更新监控任务
 * @param {number} id - 监控任务ID
 * @param {Object} data - 更新数据 { interval }
 * @returns {Promise} 更新后的监控任务
 */
export function updateMonitor(id, data) {
  return request({
    url: `/api/v1/gs-strategy/monitors/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除监控任务
 * @param {number} id - 监控任务ID
 * @returns {Promise} 删除结果
 */
export function deleteMonitor(id) {
  return request({
    url: `/api/v1/gs-strategy/monitors/${id}`,
    method: 'delete'
  })
}

/**
 * 启动监控任务
 * @param {number} id - 监控任务ID
 * @returns {Promise} 启动后的监控任务
 */
export function startMonitor(id) {
  return request({
    url: `/api/v1/gs-strategy/monitors/${id}/start`,
    method: 'post'
  })
}

/**
 * 停止监控任务
 * @param {number} id - 监控任务ID
 * @returns {Promise} 停止后的监控任务
 */
export function stopMonitor(id) {
  return request({
    url: `/api/v1/gs-strategy/monitors/${id}/stop`,
    method: 'post'
  })
}

// ==================== 持仓和历史统计 ====================

/**
 * 获取QMT持仓信息
 * @returns {Promise} 账户信息和持仓列表
 */
export function getPositions() {
  return request({
    url: '/api/v1/gs-strategy/positions',
    method: 'get'
  })
}

/**
 * 获取交易历史记录
 * @param {Object} params - 查询参数 { start_date, end_date }
 * @returns {Promise} 交易历史列表
 */
export function getTradeHistory(params) {
  return request({
    url: '/api/v1/gs-strategy/history',
    method: 'get',
    params
  })
}

/**
 * 获取交易统计数据
 * @returns {Promise} 统计数据（总交易数、胜率、总盈亏等）
 */
export function getStatistics() {
  return request({
    url: '/api/v1/gs-strategy/statistics',
    method: 'get'
  })
}
