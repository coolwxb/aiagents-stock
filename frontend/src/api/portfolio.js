import request from '@/utils/request'

// 获取持仓列表
export function getPortfolioStocks(params) {
  return request({
    url: '/api/v1/portfolio/stocks',
    method: 'get',
    params
  })
}

// 添加持仓
export function createPortfolioStock(data) {
  return request({
    url: '/api/v1/portfolio/stocks',
    method: 'post',
    data
  })
}

// 更新持仓
export function updatePortfolioStock(id, data) {
  return request({
    url: `/api/v1/portfolio/stocks/${id}`,
    method: 'put',
    data
  })
}

// 删除持仓
export function deletePortfolioStock(id) {
  return request({
    url: `/api/v1/portfolio/stocks/${id}`,
    method: 'delete'
  })
}

// 批量分析
export function batchAnalyzePortfolio(data) {
  return request({
    url: '/api/v1/portfolio/batch-analyze',
    method: 'post',
    data
  })
}

// 获取定时配置
export function getPortfolioSchedule() {
  return request({
    url: '/api/v1/portfolio/schedule',
    method: 'get'
  })
}

// 设置定时配置
export function setPortfolioSchedule(data) {
  return request({
    url: '/api/v1/portfolio/schedule',
    method: 'post',
    data
  })
}

// 分析历史
export function getPortfolioHistory(params) {
  return request({
    url: '/api/v1/portfolio/history',
    method: 'get',
    params
  })
}

