import request from '@/utils/request'

// 获取历史记录列表
export function fetchHistoryRecords(params) {
  return request({
    url: '/api/v1/history/records',
    method: 'get',
    params
  })
}

// 获取单条历史记录详情
export function getHistoryRecord(recordId) {
  return request({
    url: `/api/v1/history/records/${recordId}`,
    method: 'get'
  })
}

// 删除历史记录
export function deleteHistoryRecord(recordId) {
  return request({
    url: `/api/v1/history/records/${recordId}`,
    method: 'delete'
  })
}

// 加入监测（可选）
export function addHistoryRecordToMonitor(recordId, payload) {
  return request({
    url: `/api/v1/history/records/${recordId}/monitor`,
    method: 'post',
    data: payload
  })
}

