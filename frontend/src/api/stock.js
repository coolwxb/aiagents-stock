import request from '@/utils/request'

// 单股分析
export function analyzeStock(data) {
  return request({
    url: '/api/v1/stock/analyze',
    method: 'post',
    data
  })
}

// 批量分析
export function batchAnalyzeStock(data) {
  return request({
    url: '/api/v1/stock/batch-analyze',
    method: 'post',
    data
  })
}

// 查询历史记录
export function getStockHistory(params) {
  return request({
    url: '/api/v1/stock/history',
    method: 'get',
    params
  })
}

// 获取股票信息
export function getStockInfo(stockCode) {
  return request({
    url: `/api/v1/stock/${stockCode}`,
    method: 'get'
  })
}

// 生成PDF报告
export function generateStockPDF(data) {
  return request({
    url: '/api/v1/stock/generate-pdf',
    method: 'post',
    data,
    responseType: 'blob'
  })
}

