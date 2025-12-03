import request from '@/utils/request'

// 单股分析 - 启动异步任务
export function analyzeStock(data) {
  return request({
    url: '/api/v1/stock/analyze',
    method: 'post',
    data
  })
}

// 查询分析进度
export function getAnalyzeProgress(taskId) {
  return request({
    url: `/api/v1/stock/analyze-progress/${taskId}`,
    method: 'get'
  })
}

// 获取所有进行中的任务
export function getActiveTasks() {
  return request({
    url: '/api/v1/stock/active-tasks',
    method: 'get'
  })
}

/**
 * 创建WebSocket连接监听任务进度
 * @param {string} taskId - 任务ID
 * @param {function} onMessage - 收到消息时的回调
 * @param {function} onError - 发生错误时的回调
 * @returns {WebSocket} WebSocket实例
 */
export function connectTaskWebSocket(taskId, onMessage, onError) {
  // 获取WebSocket URL
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host // 使用当前页面的host，自动走代理
  const wsUrl = `${protocol}//${host}/dev-api/api/v1/stock/ws/analyze/${taskId}`

  console.log('WebSocket URL:', wsUrl)
  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket连接已建立:', taskId)
    // 发送心跳
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'ping' }))
      } else {
        clearInterval(heartbeat)
      }
    }, 30000) // 每30秒发送一次心跳

    // 保存心跳定时器
    ws._heartbeat = heartbeat
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (onMessage) {
        onMessage(data)
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket错误:', error)
    if (onError) {
      onError(error)
    }
  }

  ws.onclose = () => {
    console.log('WebSocket连接已关闭:', taskId)
    if (ws._heartbeat) {
      clearInterval(ws._heartbeat)
    }
  }

  return ws
}

// 批量分析
export function batchAnalyzeStock(data) {
  return request({
    url: '/api/v1/stock/batch-analyze',
    method: 'post',
    data
  })
}

// 查询历史记录
export function getStockHistory(params) {
  return request({
    url: '/api/v1/stock/history',
    method: 'get',
    params
  })
}

// 获取股票信息
export function getStockInfo(stockCode) {
  return request({
    url: `/api/v1/stock/${stockCode}`,
    method: 'get'
  })
}

// 生成PDF报告
export function generateStockPDF(data) {
  return request({
    url: '/api/v1/stock/generate-pdf',
    method: 'post',
    data,
    responseType: 'blob'
  })
}

