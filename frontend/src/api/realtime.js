import request from '@/utils/request'

// 获取监测列表
export function getRealtimeMonitors(params) {
  return request({
    url: '/api/v1/realtime/monitors',
    method: 'get',
    params
  })
}

// 添加监测
export function createRealtimeMonitor(data) {
  return request({
    url: '/api/v1/realtime/monitors',
    method: 'post',
    data
  })
}

// 更新监测
export function updateRealtimeMonitor(id, data) {
  return request({
    url: `/api/v1/realtime/monitors/${id}`,
    method: 'put',
    data
  })
}

// 删除监测
export function deleteRealtimeMonitor(id) {
  return request({
    url: `/api/v1/realtime/monitors/${id}`,
    method: 'delete'
  })
}

// 启动监测服务
export function startRealtimeService() {
  return request({
    url: '/api/v1/realtime/start',
    method: 'post'
  })
}

// 停止监测服务
export function stopRealtimeService() {
  return request({
    url: '/api/v1/realtime/stop',
    method: 'post'
  })
}

// 通知历史
export function getRealtimeNotifications(params) {
  return request({
    url: '/api/v1/realtime/notifications',
    method: 'get',
    params
  })
}

