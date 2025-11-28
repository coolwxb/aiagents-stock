import request from '@/utils/request'

// 获取交易记录
export function getTradingRecords(params) {
  return request({
    url: '/api/v1/trading/records',
    method: 'get',
    params
  })
}

// 执行交易
export function executeTrade(data) {
  return request({
    url: '/api/v1/trading/execute',
    method: 'post',
    data
  })
}

// 获取账户信息
export function getTradingAccount() {
  return request({
    url: '/api/v1/trading/account',
    method: 'get'
  })
}

