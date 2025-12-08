import request from '@/utils/request'

// 龙虎榜分析
export function analyzeLonghubang(data) {
  return request({
    url: '/api/v1/longhubang/analyze',
    method: 'post',
    data
  })
}

// 批量分析
export function batchAnalyzeLonghubang(data) {
  return request({
    url: '/api/v1/longhubang/batch-analyze',
    method: 'post',
    data
  })
}

// 获取评分排名
export function getLonghubangScoring(params) {
  return request({
    url: '/api/v1/longhubang/scoring',
    method: 'get',
    params
  })
}

// 历史报告列表
export function getLonghubangHistory(params) {
  return request({
    url: '/api/v1/longhubang/history',
    method: 'get',
    params
  })
}

// 获取单个历史报告详情
export function getLonghubangHistoryDetail(reportId) {
  return request({
    url: `/api/v1/longhubang/history/${reportId}`,
    method: 'get'
  })
}

// 删除历史报告
export function deleteLonghubangHistory(reportId) {
  return request({
    url: `/api/v1/longhubang/history/${reportId}`,
    method: 'delete'
  })
}

// 获取统计信息
export function getLonghubangStatistics() {
  return request({
    url: '/api/v1/longhubang/statistics',
    method: 'get'
  })
}

// 获取活跃游资排名
export function getTopYouzi(params) {
  return request({
    url: '/api/v1/longhubang/top-youzi',
    method: 'get',
    params
  })
}

// 获取热门股票排名
export function getTopStocks(params) {
  return request({
    url: '/api/v1/longhubang/top-stocks',
    method: 'get',
    params
  })
}

// 生成PDF
export function generateLonghubangPDF(data) {
  return request({
    url: '/api/v1/longhubang/generate-pdf',
    method: 'post',
    data,
    responseType: 'blob'
  })
}

// 异步分析（支持WebSocket进度推送）
export function analyzeAsyncLonghubang(data) {
  return request({
    url: '/api/v1/longhubang/analyze-async',
    method: 'post',
    data
  })
}

