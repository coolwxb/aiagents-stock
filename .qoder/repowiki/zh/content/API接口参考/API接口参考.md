# API接口参考

<cite>
**本文档引用的文件**
- [main.py](file://backend/app/main.py)
- [router.py](file://backend/app/api/v1/router.py)
- [deps.py](file://backend/app/api/deps.py)
- [security.py](file://backend/app/core/security.py)
- [websocket.py](file://backend/app/api/websocket.py)
- [user.py](file://backend/app/api/v1/user.py)
- [stock.py](file://backend/app/api/v1/stock.py)
- [sector.py](file://backend/app/api/v1/sector.py)
- [monitor.py](file://backend/app/api/v1/monitor.py)
- [portfolio.py](file://backend/app/api/v1/portfolio.py)
- [longhubang.py](file://backend/app/api/v1/longhubang.py)
- [mainforce.py](file://backend/app/api/v1/mainforce.py)
- [realtime.py](file://backend/app/api/v1/realtime.py)
- [trading.py](file://backend/app/api/v1/trading.py)
- [notification.py](file://backend/app/api/v1/notification.py)
</cite>

## 目录
1. [简介](#简介)
2. [API基础信息](#api基础信息)
3. [认证机制](#认证机制)
4. [WebSocket实时通信](#websocket实时通信)
5. [股票分析API](#股票分析api)
6. [智策板块API](#智策板块api)
7. [智能盯盘API](#智能盯盘api)
8. [持仓分析API](#持仓分析api)
9. [智瞰龙虎API](#智瞰龙虎api)
10. [主力选股API](#主力选股api)
11. [实时监测API](#实时监测api)
12. [量化交易API](#量化交易api)
13. [通知服务API](#通知服务api)
14. [最佳实践](#最佳实践)

## 简介
本API接口参考文档为AI股票分析系统提供完整的RESTful端点说明。系统基于FastAPI构建，提供全面的股票分析、监控和交易功能。所有API端点均遵循统一的响应格式，便于客户端集成和错误处理。

**API基础信息**
- **基础URL**: `http://host:port/api/v1`
- **文档路径**: `/api/docs` (Swagger UI) 或 `/api/redoc` (ReDoc)
- **响应格式**: 统一JSON格式，包含`code`、`msg`和`data`字段
- **错误处理**: 所有错误均返回标准HTTP状态码和统一错误响应结构

**Section sources**
- [main.py](file://backend/app/main.py#L13-L92)
- [router.py](file://backend/app/api/v1/router.py#L20-L36)

## API基础信息

### 统一响应格式
所有API响应均遵循以下统一格式：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {}
}
```

**字段说明**:
- `code`: 状态码，200表示成功，其他为错误码
- `msg`: 人类可读的消息
- `data`: 实际返回的数据，失败时为null

### HTTP状态码
- `200`: 成功
- `400`: 请求参数错误
- `401`: 未授权（JWT认证失败）
- `404`: 资源不存在
- `422`: 请求参数校验失败
- `500`: 服务器内部错误

### 公共请求头
| 请求头 | 必需 | 说明 |
|--------|------|------|
| `Authorization` | 是 | Bearer Token格式，如`Bearer <token>` |
| `Content-Type` | 是 | `application/json` |

**Section sources**
- [main.py](file://backend/app/main.py#L34-L72)
- [response.py](file://backend/app/api/response.py)

## 认证机制

### JWT认证
系统采用JWT（JSON Web Token）进行用户认证，所有需要认证的API端点都要求在请求头中包含有效的JWT令牌。

#### 认证流程
1. 用户通过`/api/v1/user/login`端点登录
2. 服务器验证凭据并返回JWT令牌
3. 客户端在后续请求的`Authorization`头中携带该令牌

#### 登录端点
```http
POST /api/v1/user/login
Content-Type: application/json
```

**请求体**:
```json
{
  "username": "admin",
  "password": "123456"
}
```

**成功响应**:
```json
{
  "code": 200,
  "msg": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

#### 获取用户信息
```http
GET /api/v1/user/info
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "code": 200,
  "msg": "获取用户信息成功",
  "data": {
    "roles": ["admin"],
    "name": "Super Admin",
    "avatar": "https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif"
  }
}
```

#### 登出
```http
POST /api/v1/user/logout
```

**注意**: 当前版本的登出功能为简化实现，实际应用中建议在服务端维护令牌黑名单。

**Section sources**
- [user.py](file://backend/app/api/v1/user.py#L14-L39)
- [deps.py](file://backend/app/api/deps.py#L17-L33)
- [security.py](file://backend/app/core/security.py#L17-L26)

## WebSocket实时通信

### WebSocket连接
系统提供WebSocket支持，用于实时推送分析进度和监测通知。

**连接URL**: `ws://host:port/api/v1/stock/ws/analyze/{task_id}`

### 消息格式
WebSocket消息采用JSON格式，包含以下字段：

```json
{
  "task_id": "123",
  "status": "running",
  "progress": 50,
  "message": "正在分析技术指标",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 客户端交互
客户端可以发送以下控制消息：
- `{"action": "ping"}`: 心跳检测
- `{"action": "get_status"}`: 获取当前任务状态

服务器会相应返回`pong`或当前任务状态。

**Section sources**
- [websocket.py](file://backend/app/api/websocket.py#L9-L41)
- [stock.py](file://backend/app/api/v1/stock.py#L77-L131)

## 股票分析API

### 单股分析
异步启动单只股票的分析任务。

```http
POST /api/v1/stock/analyze
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体 (基于StockAnalyzeRequest模型)**:
```json
{
  "stock_code": "SH600519",
  "period": "daily",
  "model": "deepseek-chat"
}
```

**响应**:
```json
{
  "code": 200,
  "msg": "分析任务已启动，请通过task_id查询进度",
  "data": {
    "task_id": "task_123",
    "message": "分析任务已启动，请通过task_id查询进度"
  }
}
```

**Section sources**
- [stock.py](file://backend/app/api/v1/stock.py#L21-L52)

### 查询分析进度
获取指定分析任务的进度。

```http
GET /api/v1/stock/analyze-progress/{task_id}
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "task_id": "task_123",
    "task_type": "stock_analysis",
    "status": "running",
    "progress": 75,
    "params": {
      "stock_code": "SH600519",
      "period": "daily",
      "model": "deepseek-chat"
    },
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:05:00Z"
  }
}
```

**Section sources**
- [stock.py](file://backend/app/api/v1/stock.py#L54-L64)

### 批量分析
对多只股票进行批量分析。

```http
POST /api/v1/stock/batch-analyze
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体 (基于BatchAnalyzeRequest模型)**:
```json
{
  "stock_codes": ["SH600519", "SZ000858"],
  "period": "daily",
  "model": "deepseek-chat"
}
```

**Section sources**
- [stock.py](file://backend/app/api/v1/stock.py#L133-L145)

### 历史记录
查询股票分析历史。

```http
GET /api/v1/stock/history?stock_code=SH600519&page=1&page_size=20
Authorization: Bearer <token>
```

**查询参数**:
- `stock_code` (可选): 股票代码
- `page`: 页码，默认1
- `page_size`: 每页数量，默认20

**Section sources**
- [stock.py](file://backend/app/api/v1/stock.py#L147-L161)

### 获取股票信息
获取指定股票的详细信息。

```http
GET /api/v1/stock/{stock_code}
Authorization: Bearer <token>
```

**Section sources**
- [stock.py](file://backend/app/api/v1/stock.py#L163-L175)

### 生成PDF报告
为指定的分析结果生成PDF报告。

```http
POST /api/v1/stock/generate-pdf
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "analysis_id": 123
}
```

**Section sources**
- [stock.py](file://backend/app/api/v1/stock.py#L177-L189)

## 智策板块API

### 板块分析
执行智策板块分析。

```http
POST /api/v1/sector/analyze
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
- `model` (可选): 使用的AI模型，默认为"deepseek-chat"

**Section sources**
- [sector.py](file://backend/app/api/v1/sector.py#L14-L26)

### 定时任务管理
获取、设置和删除定时分析任务。

**获取定时任务**:
```http
GET /api/v1/sector/schedule
Authorization: Bearer <token>
```

**设置定时任务**:
```http
POST /api/v1/sector/schedule
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "schedule_time": "09:30",
  "enabled": true
}
```

**删除定时任务**:
```http
DELETE /api/v1/sector/schedule/{schedule_id}
Authorization: Bearer <token>
```

**Section sources**
- [sector.py](file://backend/app/api/v1/sector.py#L28-L66)

### 手动触发分析
立即触发一次板块分析。

```http
POST /api/v1/sector/trigger
Authorization: Bearer <token>
```

**Section sources**
- [sector.py](file://backend/app/api/v1/sector.py#L68-L77)

### 历史报告
获取板块分析历史记录。

```http
GET /api/v1/sector/history?page=1&page_size=20
Authorization: Bearer <token>
```

**Section sources**
- [sector.py](file://backend/app/api/v1/sector.py#L79-L91)

### 生成PDF
为指定的板块分析报告生成PDF。

```http
POST /api/v1/sector/generate-pdf
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "report_id": 123
}
```

**Section sources**
- [sector.py](file://backend/app/api/v1/sector.py#L94-L106)

## 智能盯盘API

### 监控任务管理
提供对监控任务的CRUD操作。

**获取任务列表**:
```http
GET /api/v1/monitor/tasks
Authorization: Bearer <token>
```

**创建任务**:
```http
POST /api/v1/monitor/tasks
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "茅台股价监控",
  "stock_code": "SH600519",
  "conditions": {
    "price_above": 1800,
    "volume_ratio": 2.0
  },
  "enabled": true
}
```

**更新任务**:
```http
PUT /api/v1/monitor/tasks/{task_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**删除任务**:
```http
DELETE /api/v1/monitor/tasks/{task_id}
Authorization: Bearer <token>
```

**Section sources**
- [monitor.py](file://backend/app/api/v1/monitor.py#L14-L66)

### 任务控制
启动和停止监控任务。

**启动任务**:
```http
POST /api/v1/monitor/tasks/{task_id}/start
Authorization: Bearer <token>
```

**停止任务**:
```http
POST /api/v1/monitor/tasks/{task_id}/stop
Authorization: Bearer <token>
```

**Section sources**
- [monitor.py](file://backend/app/api/v1/monitor.py#L68-L93)

### 任务状态
获取指定任务的当前状态。

```http
GET /api/v1/monitor/tasks/{task_id}/status
Authorization: Bearer <token>
```

**Section sources**
- [monitor.py](file://backend/app/api/v1/monitor.py#L96-L107)

### 持仓与历史
获取当前持仓和决策历史。

**获取持仓**:
```http
GET /api/v1/monitor/positions
Authorization: Bearer <token>
```

**决策历史**:
```http
GET /api/v1/monitor/history?page=1&page_size=20
Authorization: Bearer <token>
```

**Section sources**
- [monitor.py](file://backend/app/api/v1/monitor.py#L110-L134)

## 持仓分析API

### 持仓管理
对持仓股票进行增删改查操作。

**获取持仓列表**:
```http
GET /api/v1/portfolio/stocks
Authorization: Bearer <token>
```

**添加持仓**:
```http
POST /api/v1/portfolio/stocks
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "stock_code": "SH600519",
  "stock_name": "贵州茅台",
  "quantity": 100,
  "buy_price": 1800.00,
  "buy_date": "2024-01-01"
}
```

**更新持仓**:
```http
PUT /api/v1/portfolio/stocks/{stock_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**删除持仓**:
```http
DELETE /api/v1/portfolio/stocks/{stock_id}
Authorization: Bearer <token>
```

**Section sources**
- [portfolio.py](file://backend/app/api/v1/portfolio.py#L14-L66)

### 批量分析
对所有持仓股票进行批量分析。

```http
POST /api/v1/portfolio/batch-analyze
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
- `mode`: 执行模式，"sequential"或"parallel"
- `max_workers`: 最大并发数，默认3

**Section sources**
- [portfolio.py](file://backend/app/api/v1/portfolio.py#L68-L81)

### 定时配置
设置和获取持仓分析的定时任务。

**获取定时配置**:
```http
GET /api/v1/portfolio/schedule
Authorization: Bearer <token>
```

**设置定时配置**:
```http
POST /api/v1/portfolio/schedule
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "schedule_times": ["09:30", "13:00", "15:00"]
}
```

**Section sources**
- [portfolio.py](file://backend/app/api/v1/portfolio.py#L83-L106)

### 分析历史
获取持仓分析历史记录。

```http
GET /api/v1/portfolio/history?stock_code=SH600519&page=1&page_size=20
Authorization: Bearer <token>
```

**Section sources**
- [portfolio.py](file://backend/app/api/v1/portfolio.py#L108-L123)

## 智瞰龙虎API

### 龙虎榜分析
分析指定日期的龙虎榜数据。

```http
POST /api/v1/longhubang/analyze
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
- `date` (可选): 分析日期，格式YYYY-MM-DD，为空则使用最近交易日
- `days`: 分析天数，默认1天
- `model`: 使用的AI模型，默认"deepseek-chat"

**Section sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L14-L28)

### 批量分析
对指定股票列表进行批量龙虎榜分析。

```http
POST /api/v1/longhubang/batch-analyze
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "stock_codes": ["SH600519", "SZ000858"],
  "model": "deepseek-chat"
}
```

**Section sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L30-L43)

### 评分排名
获取龙虎榜分析的评分排名。

```http
GET /api/v1/longhubang/scoring?report_id=123
Authorization: Bearer <token>
```

**Section sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L45-L57)

### 历史报告
获取龙虎榜分析历史记录。

```http
GET /api/v1/longhubang/history?page=1&page_size=20
Authorization: Bearer <token>
```

**Section sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L59-L71)

### 生成PDF
为指定的龙虎榜分析报告生成PDF。

```http
POST /api/v1/longhubang/generate-pdf
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "report_id": 123
}
```

**Section sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L74-L86)

## 主力选股API

### 主力选股分析
执行主力选股分析。

```http
POST /api/v1/mainforce/analyze
Authorization: Bearer <token)
Content-Type: application/json
```

**请求体 (基于MainforceAnalyzeRequest模型)**:
```json
{
  "market": "sh",
  "min_market_cap": 100,
  "max_pe": 50,
  "technical_pattern": "golden_cross"
}
```

**Section sources**
- [mainforce.py](file://backend/app/api/v1/mainforce.py#L20-L32)

### 批量分析
执行批量主力选股分析。

```http
POST /api/v1/mainforce/batch-analyze
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体 (基于MainforceBatchAnalyzeRequest模型)**:
```json
{
  "batch_size": 50,
  "analysis_params": [
    {
      "market": "sh",
      "min_market_cap": 100
    },
    {
      "market": "sz",
      "max_pe": 50
    }
  ]
}
```

**Section sources**
- [mainforce.py](file://backend/app/api/v1/mainforce.py#L34-L46)

### 历史记录
获取主力选股分析历史。

```http
GET /api/v1/mainforce/history?page=1&page_size=20
Authorization: Bearer <token>
```

**Section sources**
- [mainforce.py](file://backend/app/api/v1/mainforce.py#L48-L61)

## 实时监测API

### 监测管理
管理实时监测规则。

**获取监测列表**:
```http
GET /api/v1/realtime/monitors
Authorization: Bearer <token>
```

**添加监测**:
```http
POST /api/v1/realtime/monitors
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "大盘指数监测",
  "target": "SH000001",
  "condition": "close > open * 1.02",
  "frequency": "1m"
}
```

**更新监测**:
```http
PUT /api/v1/realtime/monitors/{monitor_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**删除监测**:
```http
DELETE /api/v1/realtime/monitors/{monitor_id}
Authorization: Bearer <token>
```

**Section sources**
- [realtime.py](file://backend/app/api/v1/realtime.py#L14-L66)

### 服务控制
启动和停止实时监测服务。

**启动服务**:
```http
POST /api/v1/realtime/start
Authorization: Bearer <token>
```

**停止服务**:
```http
POST /api/v1/realtime/stop
Authorization: Bearer <token>
```

**Section sources**
- [realtime.py](file://backend/app/api/v1/realtime.py#L68-L87)

### 通知历史
获取实时监测产生的通知历史。

```http
GET /api/v1/realtime/notifications?page=1&page_size=20
Authorization: Bearer <token>
```

**Section sources**
- [realtime.py](file://backend/app/api/v1/realtime.py#L90-L104)

## 量化交易API

### 交易状态
获取当前交易服务状态。

```http
GET /api/v1/trading/status
Authorization: Bearer <token>
```

**Section sources**
- [trading.py](file://backend/app/api/v1/trading.py#L14-L23)

### 下单
执行交易下单操作。

```http
POST /api/v1/trading/order
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "symbol": "SH600519",
  "action": "BUY",
  "quantity": 100,
  "price": 1800.00,
  "order_type": "LIMIT"
}
```

**Section sources**
- [trading.py](file://backend/app/api/v1/trading.py#L25-L37)

### 订单列表
获取历史订单列表。

```http
GET /api/v1/trading/orders?page=1&page_size=20
Authorization: Bearer <token>
```

**Section sources**
- [trading.py](file://backend/app/api/v1/trading.py#L39-L53)

## 通知服务API

### 发送邮件
通过配置的邮件服务发送通知邮件。

```http
POST /api/v1/notification/email
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "to": "user@example.com",
  "subject": "AI分析报告",
  "content": "今日市场分析报告已生成..."
}
```

**Section sources**
- [notification.py](file://backend/app/api/v1/notification.py#L14-L26)

### 发送Webhook
向指定URL发送Webhook通知。

```http
POST /api/v1/notification/webhook
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "url": "https://webhook.example.com/notify",
  "payload": {
    "event": "stock_analysis_completed",
    "data": {
      "stock_code": "SH600519",
      "score": 85
    }
  }
}
```

**Section sources**
- [notification.py](file://backend/app/api/v1/notification.py#L28-L40)

### 通知历史
获取所有通知发送历史。

```http
GET /api/v1/notification/history?page=1&page_size=20
Authorization: Bearer <token>
```

**Section sources**
- [notification.py](file://backend/app/api/v1/notification.py#L42-L54)

### 测试通知
测试通知服务是否正常工作。

```http
POST /api/v1/notification/test
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "notification_type": "email"
}
```

支持的类型：`email`、`webhook`、`dingtalk`等。

**Section sources**
- [notification.py](file://backend/app/api/v1/notification.py#L57-L69)

## 最佳实践

### 错误处理
客户端应妥善处理各种错误状态码：

```javascript
async function callApi(endpoint, data) {
  try {
    const response = await fetch(`/api/v1${endpoint}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      return result.data;
    } else {
      throw new Error(`${result.msg} (code: ${result.code})`);
    }
  } catch (error) {
    console.error('API调用失败:', error.message);
    // 实现重试逻辑或用户提示
  }
}
```

### 令牌管理
实现JWT令牌的自动刷新机制：

```javascript
let authToken = null;
let tokenRefreshPromise = null;

async function getValidToken() {
  if (authToken) {
    return authToken;
  }
  
  if (!tokenRefreshPromise) {
    tokenRefreshPromise = refreshToken();
  }
  
  return tokenRefreshPromise;
}

async function refreshToken() {
  // 实现令牌刷新逻辑
  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  
  const data = await response.json();
  authToken = data.data.token;
  tokenRefreshPromise = null;
  return authToken;
}
```

### WebSocket连接管理
正确管理WebSocket连接的生命周期：

```javascript
class WebSocketManager {
  constructor(taskId) {
    this.taskId = taskId;
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }
  
  async connect() {
    const url = `ws://localhost:8000/api/v1/stock/ws/analyze/${this.taskId}`;
    
    this.socket = new WebSocket(url);
    
    this.socket.onopen = () => {
      console.log('WebSocket连接已建立');
      this.reconnectAttempts = 0;
    };
    
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // 处理进度更新
      updateProgress(data);
    };
    
    this.socket.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
      }
    };
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.close();
    }
  }
}
```

### 性能优化
- 对于批量操作，使用批量API而非多次单个调用
- 合理设置分页参数，避免一次性获取过多数据
- 使用WebSocket获取实时进度，避免频繁轮询
- 缓存频繁访问的数据，减少API调用次数

### 安全注意事项
- 始终使用HTTPS保护传输中的数据
- 安全存储JWT令牌，避免XSS攻击
- 定期轮换API密钥和密码
- 验证所有用户输入，防止注入攻击

通过遵循这些最佳实践，可以确保与AI股票分析系统的稳定、安全和高效集成。