import request from '@/utils/request'

// 发送邮件
export function sendEmail(data) {
  return request({
    url: '/api/v1/notification/email',
    method: 'post',
    data
  })
}

// 发送Webhook
export function sendWebhook(data) {
  return request({
    url: '/api/v1/notification/webhook',
    method: 'post',
    data
  })
}

// 通知历史
export function getNotificationHistory(params) {
  return request({
    url: '/api/v1/notification/history',
    method: 'get',
    params
  })
}

// 测试通知
export function testNotification(data) {
  return request({
    url: '/api/v1/notification/test',
    method: 'post',
    data
  })
}

