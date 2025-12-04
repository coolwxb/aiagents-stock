import request from '@/utils/request'

// 更新板块数据
export function updateSectors() {
  return request({
    url: '/api/v1/data/sectors/update',
    method: 'post'
  })
}

// 更新板块成分股
export function updateSectorStocks(sectorCode = null) {
  return request({
    url: '/api/v1/data/sectors/stocks/update',
    method: 'post',
    params: {
      sector_code: sectorCode
    }
  })
}

// 更新股票基本信息
export function updateStockInfo(stockCode = null) {
  return request({
    url: '/api/v1/data/stocks/update',
    method: 'post',
    params: {
      stock_code: stockCode
    }
  })
}

// 获取板块列表
export function getSectors(params) {
  return request({
    url: '/api/v1/data/sectors',
    method: 'get',
    params
  })
}

// 获取股票列表
export function getStocks(params) {
  return request({
    url: '/api/v1/data/stocks',
    method: 'get',
    params
  })
}
