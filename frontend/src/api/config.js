import request from '@/utils/request'

// 获取配置
export function getConfig() {
  return request({
    url: '/api/v1/config',
    method: 'get'
  })
}

// 更新配置
export function updateConfig(data) {
  return request({
    url: '/api/v1/config',
    method: 'put',
    data
  })
}

// 验证配置
export function validateConfig(data) {
  return request({
    url: '/api/v1/config/validate',
    method: 'post',
    data
  })
}

// 测试配置
export function testConfig(data) {
  return request({
    url: '/api/v1/config/test',
    method: 'post',
    data
  })
}

