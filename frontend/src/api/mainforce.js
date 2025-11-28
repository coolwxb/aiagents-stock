import request from '@/utils/request'

// 主力选股分析
export function analyzeMainforce(data) {
  return request({
    url: '/api/v1/mainforce/analyze',
    method: 'post',
    data
  })
}

// 批量分析
export function batchAnalyzeMainforce(data) {
  return request({
    url: '/api/v1/mainforce/batch-analyze',
    method: 'post',
    data
  })
}

// 历史记录
export function getMainforceHistory(params) {
  return request({
    url: '/api/v1/mainforce/history',
    method: 'get',
    params
  })
}

