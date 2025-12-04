# 智瞰龙虎榜API

<cite>
**本文档引用文件**  
- [longhubang.py](file://backend/app/api/v1/longhubang.py)
- [longhubang_service.py](file://backend/app/services/longhubang_service.py)
- [longhubang_agents.py](file://backend/app/agents/longhubang_agents.py)
- [deepseek_client.py](file://backend/app/agents/deepseek_client.py)
- [longhubang.js](file://frontend/src/api/longhubang.js)
- [longhubang_db.py](file://backend/app/db/longhubang_db.py)
- [智瞰龙虎AI评分说明.md](file://docs/智瞰龙虎AI评分说明.md)
- [智瞰龙虎功能说明.md](file://docs/智瞰龙虎功能说明.md)
- [index.vue](file://frontend/src/views/longhubang/index.vue)
</cite>

## 目录
1. [简介](#简介)
2. [API端点详情](#api端点详情)
3. [评分模型与AI代理](#评分模型与ai代理)
4. [前端调用流程](#前端调用流程)
5. [异常处理与重试策略](#异常处理与重试策略)
6. [数据流与架构图](#数据流与架构图)
7. [最佳实践与建议](#最佳实践与建议)

## 简介

智瞰龙虎榜功能通过AI智能体对股票龙虎榜数据进行深度分析，生成综合评分和投资建议。系统整合了多维度数据源，利用DeepSeek大模型进行智能分析，为投资者提供科学决策支持。本API文档详细说明了核心接口的使用方法、参数要求、返回结构以及底层实现机制。

该功能主要包含龙虎榜分析、批量分析、评分排名、历史报告查询和PDF报告生成等核心功能，通过RESTful API提供服务，支持前后端分离架构。

**Section sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L1-L87)
- [智瞰龙虎功能说明.md](file://docs/智瞰龙虎功能说明.md#L1-L237)

## API端点详情

### 龙虎榜分析接口

**端点**: `POST /api/v1/longhubang/analyze`  
**用途**: 对指定日期的龙虎榜数据进行AI分析

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| date | string | 否 | null | 分析日期（YYYY-MM-DD格式），为空则使用最近交易日 |
| days | integer | 否 | 1 | 分析最近N天的数据（1-10天） |
| model | string | 否 | deepseek-chat | 使用的AI模型名称 |

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "report_id": 123,
    "analysis_date": "2024-01-15",
    "total_stocks": 50,
    "scoring_ranking": [
      {
        "rank": 1,
        "stock_code": "000001",
        "stock_name": "平安银行",
        "score": 92.5,
        "details": {
          "buy_quality": 28.0,
          "net_buy": 24.0,
          "sell_pressure": 20.0,
          "institution_resonance": 15.0,
          "bonus_points": 5.5
        }
      }
    ],
    "recommended_stocks": ["000001", "600519"],
    "analysis_summary": "今日市场活跃..."
  }
}
```

### 批量分析接口

**端点**: `POST /api/v1/longhubang/batch-analyze`  
**用途**: 对指定股票列表进行批量分析

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| stock_codes | array | 是 | 股票代码列表（如["000001", "600519"]） |
| model | string | 否 | deepseek-chat | 使用的AI模型名称 |

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "batch_id": "batch_20240115_001",
    "total_count": 10,
    "success_count": 8,
    "failed_count": 2,
    "results": [
      {
        "stock_code": "000001",
        "success": true,
        "score": 92.5,
        "analysis": "该股有顶级游资参与..."
      }
    ],
    "failed_list": ["000002", "600000"]
  }
}
```

### 评分排名接口

**端点**: `GET /api/v1/longhubang/scoring`  
**用途**: 获取指定报告的评分排名

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| report_id | integer | 是 | 报告ID |

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "report_id": 123,
    "total_rankings": 50,
    "top_10": [
      {
        "rank": 1,
        "stock_code": "000001",
        "stock_name": "平安银行",
        "score": 92.5,
        "net_inflow": 150000000,
        "top_investors": ["赵老哥", "章盟主"]
      }
    ]
  }
}
```

### 历史报告接口

**端点**: `GET /api/v1/longhubang/history`  
**用途**: 获取历史分析报告列表

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量 |

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 123,
        "analysis_date": "2024-01-15",
        "total_stocks": 50,
        "top_score": 92.5,
        "top_stock": "000001",
        "created_at": "2024-01-15T20:30:00Z"
      }
    ],
    "total": 150,
    "page": 1,
    "page_size": 20
  }
}
```

### PDF报告生成接口

**端点**: `POST /api/v1/longhubang/generate-pdf`  
**用途**: 生成指定报告的PDF文件

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| report_id | integer | 是 | 报告ID |

**成功响应**: 返回PDF文件的二进制流，Content-Type为application/pdf

**Section sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L14-L87)
- [longhubang_service.py](file://backend/app/services/longhubang_service.py#L14-L37)

## 评分模型与AI代理

### 评分模型架构

智瞰龙虎榜采用五维评分体系，对股票进行100分制综合评估：

```mermaid
graph TD
A[综合评分100分] --> B[买入资金含金量<br/>0-30分]
A --> C[净买入额评分<br/>0-25分]
A --> D[卖出压力评分<br/>0-20分]
A --> E[机构共振评分<br/>0-15分]
A --> F[其他加分项<br/>0-10分]
B --> B1[顶级游资+10分/个]
B --> B2[知名游资+5分/个]
B --> B3[普通游资+1.5分/个]
C --> C1[>1亿: 22-25分]
C --> C2[5000万-1亿: 18-22分]
C --> C3[1000万-5000万: 10-18分]
C --> C4[<1000万: 0-10分]
D --> D1[卖出比例<10%: 20分]
D --> D2[10-30%: 15-20分]
D --> D3[30-50%: 10-15分]
D --> D4[50-80%: 5-10分]
D --> D5[>80%: 0-5分]
E --> E1[机构+游资共振: 15分]
E --> E2[仅机构买入: 8-12分]
E --> E3[仅游资买入: 5-10分]
F --> F1[主力集中度: 0-3分]
F --> F2[热门概念: 0-3分]
F --> F3[连续上榜: 0-2分]
F --> F4[买卖比例: 0-2分]
```

**Diagram sources**
- [智瞰龙虎AI评分说明.md](file://docs/智瞰龙虎AI评分说明.md#L5-L176)

### AI代理工作流程

系统通过`longhubang_agents.py`中的AI代理协同工作，每个代理负责特定分析任务：

```mermaid
sequenceDiagram
participant Frontend as 前端
participant API as API服务
participant Service as LonghubangService
participant Agent as AI代理
participant DeepSeek as DeepSeek API
Frontend->>API : 发送分析请求
API->>Service : 调用analyze_longhubang
Service->>Agent : 初始化AI代理
Agent->>DeepSeek : 发送技术面分析请求
DeepSeek-->>Agent : 返回技术分析结果
Agent->>DeepSeek : 发送基本面分析请求
DeepSeek-->>Agent : 返回基本面分析结果
Agent->>DeepSeek : 发送资金面分析请求
DeepSeek-->>Agent : 返回资金面分析结果
Agent->>DeepSeek : 发送综合讨论请求
DeepSeek-->>Agent : 返回综合讨论结果
Agent->>DeepSeek : 发送最终决策请求
DeepSeek-->>Agent : 返回最终投资决策
Agent->>Service : 返回完整分析报告
Service->>API : 返回处理结果
API->>Frontend : 返回成功响应
```

**Diagram sources**
- [longhubang_agents.py](file://backend/app/agents/longhubang_agents.py#L1-L6)
- [deepseek_client.py](file://backend/app/agents/deepseek_client.py#L6-L458)

### DeepSeek API交互

`DeepSeekClient`类负责与DeepSeek API的交互，支持多种分析模式：

```mermaid
classDiagram
class DeepSeekClient {
+string model
+OpenAI client
+__init__(model : string)
+call_api(messages : List, model : string, temperature : float, max_tokens : int) str
+technical_analysis(stock_info : Dict, stock_data : Any, indicators : Dict) str
+fundamental_analysis(stock_info : Dict, financial_data : Dict, quarterly_data : Dict) str
+fund_flow_analysis(stock_info : Dict, indicators : Dict, fund_flow_data : Dict) str
+comprehensive_discussion(technical_report : str, fundamental_report : str, fund_flow_report : str, stock_info : Dict) str
+final_decision(comprehensive_discussion : str, stock_info : Dict, indicators : Dict) Dict[str, Any]
}
class LonghubangService {
+Session db
+analyze_longhubang(date : string, days : int, model : string) Coroutine
+batch_analyze(stock_codes : List[str], model : string) Coroutine
+get_scoring(report_id : int) Coroutine
+get_history(page : int, page_size : int) Coroutine
+generate_pdf(report_id : int) Coroutine
}
DeepSeekClient --> LonghubangService : "被使用"
LonghubangService --> DeepSeekClient : "创建实例"
```

**Diagram sources**
- [deepseek_client.py](file://backend/app/agents/deepseek_client.py#L6-L458)
- [longhubang_service.py](file://backend/app/services/longhubang_service.py#L8-L38)

## 前端调用流程

### 主要调用示例

前端通过`longhubang.js`中的封装函数调用API：

```javascript
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
```

### Vue组件调用流程

在`index.vue`中，组件通过以下流程调用API：

```mermaid
flowchart TD
A[用户点击分析按钮] --> B[收集分析参数]
B --> C{分析模式}
C --> |指定日期| D[设置date参数]
C --> |最近N天| E[设置days参数]
D --> F[调用analyzeLonghubang]
E --> F
F --> G[处理API响应]
G --> H{响应成功?}
H --> |是| I[更新分析结果]
H --> |否| J[显示错误信息]
I --> K[显示成功消息]
J --> L[显示示例数据]
K --> M[分析完成]
L --> M
```

**Diagram sources**
- [longhubang.js](file://frontend/src/api/longhubang.js#L1-L49)
- [index.vue](file://frontend/src/views/longhubang/index.vue#L721-L744)

**Section sources**
- [longhubang.js](file://frontend/src/api/longhubang.js#L1-L49)
- [index.vue](file://frontend/src/views/longhubang/index.vue#L721-L744)

## 异常处理与重试策略

### 错误响应码

| HTTP状态码 | 错误码 | 错误信息 | 说明 |
|-----------|--------|---------|------|
| 500 | 500 | Internal Server Error | 服务器内部错误 |
| 400 | 400 | Bad Request | 请求参数错误 |
| 404 | 404 | Not Found | 资源未找到 |
| 429 | 429 | Too Many Requests | 请求过于频繁 |
| 503 | 503 | Service Unavailable | 服务暂时不可用 |

### 常见异常场景

```mermaid
flowchart TD
A[API调用异常] --> B{异常类型}
B --> |网络连接失败| C[检查网络连接]
B --> |DeepSeek API不可用| D[使用备用模型]
B --> |数据库连接失败| E[重试连接]
B --> |参数验证失败| F[返回400错误]
B --> |分析超时| G[增加超时时间]
C --> H[等待30秒后重试]
D --> I[切换到deepseek-reasoner]
E --> J[最多重试3次]
G --> K[最多重试2次]
H --> L{重试成功?}
I --> M{备用模型可用?}
J --> N{重试次数<3?}
K --> O{重试次数<2?}
L --> |是| P[继续处理]
L --> |否| Q[返回503错误]
M --> |是| R[使用备用模型]
M --> |否| S[返回503错误]
N --> |是| E
N --> |否| T[返回503错误]
O --> |是| G
O --> |否| U[返回503错误]
```

### 前端异常处理

前端在`index.vue`中实现了完善的异常处理机制：

```javascript
async handleAnalyze() {
  this.analysisLoading = true
  try {
    const payload = { model: this.selectedModel }
    if (this.analysisMode === 'date') {
      payload.date = this.selectedDate || dayjs().subtract(1, 'day').format('YYYY-MM-DD')
    } else {
      payload.days = this.recentDays
    }
    const res = await analyzeLonghubang(payload)
    const data = res?.data || res?.result || res
    if (data?.success) {
      this.analysisResult = this.decorateResult(data)
      this.$message.success('龙虎榜分析完成')
    } else {
      throw new Error(data?.error || '分析失败')
    }
  } catch (error) {
    console.warn('analyzeLonghubang fallback', error)
    this.analysisResult = createFallbackResult()
    this.$message.info('接口暂未打通，展示示例分析结果')
  } finally {
    this.analysisLoading = false
  }
}
```

**Section sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L26-L27)
- [response.py](file://backend/app/api/response.py#L10-L31)
- [index.vue](file://frontend/src/views/longhubang/index.vue#L738-L742)

## 数据流与架构图

### 系统整体架构

```mermaid
graph TD
A[前端界面] --> B[API网关]
B --> C[龙虎榜分析服务]
C --> D[AI代理系统]
D --> E[DeepSeek API]
C --> F[数据库]
F --> G[龙虎榜记录表]
F --> H[分析报告表]
F --> I[股票追踪表]
D --> J[技术面分析]
D --> K[基本面分析]
D --> L[资金面分析]
D --> M[综合讨论]
D --> N[最终决策]
C --> O[PDF生成服务]
O --> P[生成PDF报告]
P --> Q[返回二进制流]
Q --> A
G --> C
H --> C
I --> C
```

**Diagram sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L1-L87)
- [longhubang_service.py](file://backend/app/services/longhubang_service.py#L8-L38)
- [longhubang_db.py](file://backend/app/db/longhubang_db.py#L1-L6)

### 服务依赖关系

```mermaid
graph LR
A[longhubang.py] --> B[longhubang_service.py]
B --> C[longhubang_db.py]
B --> D[longhubang_agents.py]
D --> E[deepseek_client.py]
E --> F[DeepSeek API]
A --> G[response.py]
A --> H[get_database]
C --> I[SQLAlchemy]
D --> J[AI分析代理]
```

**Diagram sources**
- [longhubang.py](file://backend/app/api/v1/longhubang.py#L1-L87)
- [longhubang_service.py](file://backend/app/services/longhubang_service.py#L8-L38)
- [longhubang_db.py](file://backend/app/db/longhubang_db.py#L1-L6)
- [deepseek_client.py](file://backend/app/agents/deepseek_client.py#L6-L458)

## 最佳实践与建议

### 推荐使用模式

1. **日常分析流程**：
   - 交易日晚上6点后进行分析
   - 选择"最近1天"模式获取最新数据
   - 重点关注评分80分以上的S级股票
   - 结合技术面和基本面进行综合判断

2. **批量分析策略**：
   - 用于筛选自选股池中的潜力股
   - 建议每次分析不超过50只股票
   - 可以设置定时任务每日自动分析

3. **历史数据研究**：
   - 通过历史报告接口获取长期数据
   - 分析高分股票的后续表现
   - 研究不同市场环境下的评分有效性

### 性能优化建议

- **缓存策略**：对频繁查询的评分排名结果进行缓存
- **异步处理**：对于耗时的分析任务使用异步处理
- **连接池**：使用数据库连接池提高数据库访问效率
- **批量操作**：批量分析时尽量减少API调用次数

### 安全注意事项

- **API密钥保护**：确保DEEPSEEK_API_KEY等敏感信息不泄露
- **输入验证**：对所有API参数进行严格验证
- **速率限制**：防止恶意用户频繁调用API
- **日志审计**：记录关键操作日志便于追踪

**Section sources**
- [智瞰龙虎AI评分说明.md](file://docs/智瞰龙虎AI评分说明.md#L179-L247)
- [智瞰龙虎功能说明.md](file://docs/智瞰龙虎功能说明.md#L173-L198)