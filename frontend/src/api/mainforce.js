import request from '@/utils/request'

// 主力选股分析
export function analyzeMainforce(data) {
  return request({
    url: '/api/v1/mainforce/analyze',
    method: 'post',
    data,
    timeout: 600000 // 10分钟超时
  })
}

// 批量分析
export function batchAnalyzeMainforce(data) {
  return request({
    url: '/api/v1/mainforce/batch-analyze',
    method: 'post',
    data,
    timeout: 1800000 // 30分钟超时
  })
}

// 历史记录列表
export function getMainforceHistory(params) {
  return request({
    url: '/api/v1/mainforce/history',
    method: 'get',
    params
  })
}

// 历史记录详情
export function getMainforceHistoryDetail(recordId) {
  return request({
    url: `/api/v1/mainforce/history/${recordId}`,
    method: 'get'
  })
}

// 删除历史记录
export function deleteMainforceHistory(recordId) {
  return request({
    url: `/api/v1/mainforce/history/${recordId}`,
    method: 'delete'
  })
}

// 获取统计信息
export function getMainforceStatistics() {
  return request({
    url: '/api/v1/mainforce/statistics',
    method: 'get'
  })
}

