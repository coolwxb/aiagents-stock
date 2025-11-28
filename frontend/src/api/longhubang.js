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

// 历史报告
export function getLonghubangHistory(params) {
  return request({
    url: '/api/v1/longhubang/history',
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

