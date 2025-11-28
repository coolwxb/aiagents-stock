import request from '@/utils/request'

// 板块分析
export function analyzeSector(data) {
  return request({
    url: '/api/v1/sector/analyze',
    method: 'post',
    data
  })
}

// 获取定时任务
export function getSectorSchedule() {
  return request({
    url: '/api/v1/sector/schedule',
    method: 'get'
  })
}

// 设置定时任务
export function setSectorSchedule(data) {
  return request({
    url: '/api/v1/sector/schedule',
    method: 'post',
    data
  })
}

// 删除定时任务
export function deleteSectorSchedule(id) {
  return request({
    url: `/api/v1/sector/schedule/${id}`,
    method: 'delete'
  })
}

// 手动触发分析
export function triggerSectorAnalysis() {
  return request({
    url: '/api/v1/sector/trigger',
    method: 'post'
  })
}

// 历史报告
export function getSectorHistory(params) {
  return request({
    url: '/api/v1/sector/history',
    method: 'get',
    params
  })
}

// 生成PDF
export function generateSectorPDF(data) {
  return request({
    url: '/api/v1/sector/generate-pdf',
    method: 'post',
    data,
    responseType: 'blob'
  })
}

