# 飞书Webhook配置

<cite>
**本文档引用的文件**
- [Webhook功能完成说明.md](file://docs/Webhook功能完成说明.md)
- [Webhook功能实现总结.md](file://docs/Webhook功能实现总结.md)
- [Webhook通知配置指南.md](file://docs/Webhook通知配置指南.md)
- [Webhook自定义关键词功能说明.md](file://docs/Webhook自定义关键词功能说明.md)
- [notification_service.py](file://backend/app/services/notification_service.py)
- [monitor_service.py](file://backend/app/services/monitor_service.py)
- [config_manager.py](file://old/config_manager.py)
- [app.py](file://old/app.py)
</cite>

## 目录
1. [引言](#引言)
2. [飞书Webhook配置流程](#飞书webhook配置流程)
3. [消息格式与API规范](#消息格式与api规范)
4. [测试与验证](#测试与验证)
5. [错误处理与故障排查](#错误处理与故障排查)
6. [配置最佳实践](#配置最佳实践)
7. [总结](#总结)

## 引言

本系统已成功集成飞书Webhook通知功能，支持将实时监测提醒和智策定时分析报告推送到飞书群组。通过自定义机器人，用户可以实现即时消息推送，提升团队协作效率和投资决策响应速度。系统支持与邮件通知双通道并行，确保重要信息不被遗漏。

**文档来源**
- [Webhook功能完成说明.md](file://docs/Webhook功能完成说明.md)
- [Webhook功能实现总结.md](file://docs/Webhook功能实现总结.md)

## 飞书Webhook配置流程

### 添加自定义机器人

1. **进入飞书群设置**：在目标群聊中点击右上角“...”进入群设置。
2. **添加机器人**：选择“群机器人” → “添加机器人” → “自定义机器人”。
3. **配置机器人信息**：
   - **机器人名称**：建议设置为“AI股票分析系统”。
   - **机器人描述**：可填写“股票监测和板块分析通知”。
   - **安全设置**：可选择签名验证等安全选项（可选）。

### 获取Webhook地址

完成机器人配置后，系统会生成一个Webhook地址，格式如下：
```
https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxxxxxx
```
请复制完整的URL地址，用于后续系统配置。

### 配置安全策略

#### 加密密钥（签名验证）
若启用签名验证，需在飞书机器人安全设置中获取加密密钥，并在系统配置中进行相应设置。系统会自动处理签名生成和验证。

#### 关键字过滤
飞书机器人通常不强制要求关键字过滤。若需使用，可在`.env`文件中配置`WEBHOOK_KEYWORD`，系统会自动在消息标题和内容中添加关键词前缀。

**配置示例**：
```env
WEBHOOK_ENABLED=true
WEBHOOK_TYPE=feishu
WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxxxxxx
WEBHOOK_KEYWORD=aiagents通知
```

**文档来源**
- [Webhook通知配置指南.md](file://docs/Webhook通知配置指南.md)
- [Webhook自定义关键词功能说明.md](file://docs/Webhook自定义关键词功能说明.md)

## 消息格式与API规范

系统基于`send_webhook`服务方法，支持多种飞书消息格式。

### 支持的消息类型

| 消息类型 | 描述 | 使用场景 |
|---------|------|---------|
| `text` | 纯文本消息 | 简单提醒 |
| `post` | 富文本消息 | 详细报告 |
| `image` | 图片消息 | 技术图表 |
| `file` | 文件消息 | 附件报告 |
| `interactive` | 交互式卡片 | 主要消息格式 |

### JSON结构示例

#### 交互式卡片消息（推荐）
```json
{
  "msg_type": "interactive",
  "card": {
    "config": {
      "wide_screen_mode": true
    },
    "header": {
      "title": {
        "tag": "plain_text",
        "content": "股票监测提醒"
      },
      "template": "blue"
    },
    "elements": [
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**股票代码**: 600519\n\n**股票名称**: 贵州茅台"
        }
      },
      {
        "tag": "hr"
      },
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**提醒类型**: 进场提醒\n\n**提醒内容**: 股票价格 1650.00 进入进场区间"
        }
      }
    ]
  }
}
```

#### 富文本消息（多语言支持）
系统支持在`post`类型消息中使用多语言内容，通过`zh_cn`、`en_us`等字段定义不同语言版本。

#### 代码示例
系统通过`_send_feishu_webhook()`方法构造符合飞书API规范的请求数据，自动处理消息格式化和JSON序列化。

**文档来源**
- [Webhook功能完成说明.md](file://docs/Webhook功能完成说明.md)
- [notification_service.py](file://backend/app/services/notification_service.py)

## 测试与验证

### 使用/test接口验证

系统提供`/api/v1/notification/test`接口用于验证Webhook配置正确性。

**测试步骤**：
1. 在“实时监测”模块的“通知管理”区域，点击“发送测试Webhook”按钮。
2. 检查飞书群组是否收到如下测试消息：
```
股票代码: 测试
股票名称: Webhook测试
提醒类型: 测试消息
提醒内容: 如果您收到此消息，说明Webhook配置正确！
触发时间: 刚刚
```
3. 查看系统日志确认发送状态。

**文档来源**
- [Webhook通知配置指南.md](file://docs/Webhook通知配置指南.md)
- [notification.py](file://backend/app/api/v1/notification.py)

## 错误处理与故障排查

### 常见错误及解决方案

| 错误类型 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 网络超时 | 网络连接不稳定 | 检查网络连接，确保服务器可访问飞书API |
| 400错误（无效请求） | Webhook URL格式错误或消息内容不符合规范 | 检查URL完整性，验证JSON结构 |
| 403错误（权限不足） | Webhook URL无效或机器人被移出群聊 | 重新获取Webhook URL，确认机器人状态 |

### 故障排查清单

1. ✅ 确认`WEBHOOK_ENABLED=true`
2. ✅ 检查Webhook URL是否完整正确
3. ✅ 确认网络连接正常
4. ✅ 验证机器人未被移出群聊
5. ✅ 查看系统日志获取详细错误信息

**文档来源**
- [Webhook功能完成说明.md](file://docs/Webhook功能完成说明.md)
- [Webhook通知配置指南.md](file://docs/Webhook通知配置指南.md)

## 配置最佳实践

### 环境变量管理
使用`.env`文件存储`WEBHOOK_URL`和`WEBHOOK_KEYWORD`等敏感信息，避免硬编码和版本控制泄露。

### 消息频率限制
- **飞书限制**：每个机器人每分钟最多50条消息。
- **系统控制**：实时监测重复通知间隔为60分钟，智策分析每天1次，确保不会触发平台限流。

### 失败重试机制
系统内置自动错误处理和重试机制，发送失败时会记录日志但不影响核心功能运行。

### 安全建议
- ❌ 不要公开分享Webhook URL
- ❌ 不要提交到版本控制系统
- ✅ 定期更换Webhook地址
- ✅ 使用环境变量管理密钥

**文档来源**
- [Webhook功能实现总结.md](file://docs/Webhook功能实现总结.md)
- [Webhook通知配置指南.md](file://docs/Webhook通知配置指南.md)

## 总结

飞书Webhook功能已全面实现，具备以下特点：
1. **双平台支持**：同时支持钉钉和飞书
2. **灵活配置**：支持Web界面和`.env`文件配置
3. **丰富消息格式**：支持文本、富文本、交互式卡片等多种格式
4. **可靠传输**：内置错误处理、日志记录和重试机制
5. **完整文档**：提供详细的配置指南和故障排查手册

通过合理配置，用户可实现高效、及时的投资信息推送，提升决策效率。

**文档来源**
- [Webhook功能完成说明.md](file://docs/Webhook功能完成说明.md)
- [Webhook功能实现总结.md](file://docs/Webhook功能实现总结.md)