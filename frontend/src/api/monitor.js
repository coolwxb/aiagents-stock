import request from '@/utils/request'

// 获取监控任务列表
export function getMonitorTasks(params) {
  return request({
    url: '/api/v1/monitor/tasks',
    method: 'get',
    params
  })
}

// 创建监控任务
export function createMonitorTask(data) {
  return request({
    url: '/api/v1/monitor/tasks',
    method: 'post',
    data
  })
}

// 更新监控任务
export function updateMonitorTask(id, data) {
  return request({
    url: `/api/v1/monitor/tasks/${id}`,
    method: 'put',
    data
  })
}

// 删除监控任务
export function deleteMonitorTask(id) {
  return request({
    url: `/api/v1/monitor/tasks/${id}`,
    method: 'delete'
  })
}

// 启动任务
export function startMonitorTask(id) {
  return request({
    url: `/api/v1/monitor/tasks/${id}/start`,
    method: 'post'
  })
}

// 停止任务
export function stopMonitorTask(id) {
  return request({
    url: `/api/v1/monitor/tasks/${id}/stop`,
    method: 'post'
  })
}

// 获取任务状态
export function getMonitorTaskStatus(id) {
  return request({
    url: `/api/v1/monitor/tasks/${id}/status`,
    method: 'get'
  })
}

// 获取持仓
export function getMonitorPositions() {
  return request({
    url: '/api/v1/monitor/positions',
    method: 'get'
  })
}

// 决策历史
export function getMonitorHistory(params) {
  return request({
    url: '/api/v1/monitor/history',
    method: 'get',
    params
  })
}

// 获取股票实时行情
export function getStockQuote(stockCode) {
  return request({
    url: `/api/v1/monitor/quote/${stockCode}`,
    method: 'get'
  })
}

