# 钉钉Webhook配置

<cite>
**本文档引用的文件**  
- [notification_service.py](file://old\notification_service.py)
- [app.py](file://old\app.py)
- [Webhook通知配置指南.md](file://docs\Webhook通知配置指南.md)
- [Webhook功能实现总结.md](file://docs\Webhook功能实现总结.md)
- [Webhook钉钉关键词快速配置指南.md](file://docs\Webhook钉钉关键词快速配置指南.md)
</cite>

## 目录
1. [钉钉Webhook配置流程](#钉钉webhook配置流程)
2. [安全验证配置](#安全验证配置)
3. [消息类型与JSON结构](#消息类型与json结构)
4. [加签算法实现](#加签算法实现)
5. [测试与异常处理](#测试与异常处理)
6. [安全最佳实践](#安全最佳实践)

## 钉钉Webhook配置流程

钉钉Webhook的配置流程包括在钉钉群中创建自定义机器人、获取Webhook URL以及在系统中进行配置。首先，在钉钉群聊中点击右上角的群设置，选择“智能群助手”并添加一个自定义机器人。为机器人命名，例如“AI股票分析系统”，然后完成安全设置。安全设置可以选择自定义关键词、加签或IP地址段。完成配置后，系统会显示Webhook地址，该地址需要复制并粘贴到系统的配置中。

在系统中配置Webhook时，可以通过Web界面或手动编辑`.env`文件来完成。通过Web界面配置是推荐的方法，用户可以进入环境配置页面，选择“通知配置”标签页，启用Webhook通知，选择Webhook类型（钉钉或飞书），填写Webhook URL，并保存配置。测试配置时，可以在实时监测的“通知管理”区域点击“测试Webhook”按钮，检查群消息是否收到。

**Section sources**
- [Webhook通知配置指南.md](file://docs\Webhook通知配置指南.md#L31-L47)
- [Webhook钉钉关键词快速配置指南.md](file://docs\Webhook钉钉关键词快速配置指南.md#L5-L40)

## 安全验证配置

钉钉Webhook的安全验证配置包括自定义关键词、加签和IP白名单三种方式。自定义关键词是最简单的方式，只需在钉钉机器人安全设置中输入一个关键词，如“aiagents通知”，然后在系统配置中填写相同的关键词即可。加签方式提供了更高的安全性，需要在钉钉机器人安全设置中启用加签，并使用HMAC-SHA256算法生成签名。IP白名单则适用于固定IP服务器，需要将服务器的出口IP添加到白名单中。

在系统配置中，如果选择了自定义关键词，需要确保消息中包含该关键词，否则消息将被拒绝。对于加签方式，系统需要在发送请求时生成签名，并将其拼接到URL中。IP白名单方式则不需要额外的配置，只要服务器的IP在白名单中即可发送消息。

**Section sources**
- [Webhook通知配置指南.md](file://docs\Webhook通知配置指南.md#L71-L76)
- [Webhook钉钉关键词快速配置指南.md](file://docs\Webhook钉钉关键词快速配置指南.md#L56-L66)

## 消息类型与JSON结构

钉钉支持多种消息类型，包括文本、链接、Markdown、ActionCard和FeedCard。每种消息类型都有其特定的JSON结构要求。例如，Markdown消息类型的JSON结构如下所示：

```json
{
  "msgtype": "markdown",
  "markdown": {
    "title": "AI股票分析系统",
    "text": "### 股票监测提醒\n\n**股票代码**: 600519\n\n**股票名称**: 贵州茅台\n\n**提醒类型**: 进场提醒\n\n**提醒内容**: 股票价格 1650.00 进入进场区间\n\n**触发时间**: 2024-01-15 10:30:00\n\n---\n\n_此消息由AI股票分析系统自动发送_"
  }
}
```

系统会根据平台类型自动格式化消息，确保消息在钉钉或飞书中正确显示。对于飞书，系统支持文本和交互式卡片消息，消息格式会有所不同。

**Section sources**
- [Webhook通知配置指南.md](file://docs\Webhook通知配置指南.md#L86-L130)
- [notification_service.py](file://old\notification_service.py#L316-L341)

## 加签算法实现

加签算法的实现方式是使用HMAC-SHA256生成签名，并将签名拼接到URL中。具体步骤如下：首先，从钉钉机器人安全设置中获取密钥（Secret），然后使用HMAC-SHA256算法对时间戳和密钥进行加密，生成签名。签名生成后，需要将其进行URL编码，并与时间戳一起拼接到Webhook URL中。最终的URL格式如下：

```
https://oapi.dingtalk.com/robot/send?access_token=xxxxx&timestamp=xxx&sign=xxx
```

在系统中，加签的实现代码如下：

```python
import time
import hmac
import hashlib
import base64
from urllib.parse import quote_plus

timestamp = str(round(time.time() * 1000))
secret = 'your_secret'
secret_enc = secret.encode('utf-8')
string_to_sign = '{}\n{}'.format(timestamp, secret)
hmac_code = hmac.new(secret_enc, string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
sign = quote_plus(base64.b64encode(hmac_code))
webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
```

**Section sources**
- [Webhook钉钉关键词快速配置指南.md](file://docs\Webhook钉钉关键词快速配置指南.md#L60-L62)
- [notification_service.py](file://old\notification_service.py#L317-L320)

## 测试与异常处理

通过/test接口可以测试配置的有效性。在系统中，可以点击“测试Webhook”按钮，系统会发送一条测试消息到钉钉群。如果收到消息，说明配置正确。常见的异常情况包括410错误（IP不在白名单）和401错误（签名验证失败）。对于410错误，需要检查服务器的出口IP是否在钉钉机器人的IP白名单中。对于401错误，需要检查签名是否正确生成，以及时间戳是否在有效范围内。

系统会在终端输出详细的日志，帮助用户排查问题。例如，如果Webhook发送失败，日志会显示具体的错误信息，如“钉钉Webhook返回错误: invalid sign”。用户可以根据日志信息进行相应的调整。

**Section sources**
- [Webhook通知配置指南.md](file://docs\Webhook通知配置指南.md#L225-L341)
- [notification_service.py](file://old\notification_service.py#L473-L516)

## 安全最佳实践

为了确保Webhook的安全性，建议采取以下最佳实践：定期更换密钥，以减少密钥泄露的风险；限制机器人权限，只授予必要的权限；启用日志监控，记录所有Webhook的发送情况，以便及时发现异常行为。此外，不要在公开场合分享Webhook URL，也不要将其提交到版本控制系统中。使用环境变量或配置文件来管理Webhook URL，可以提高安全性。

**Section sources**
- [Webhook通知配置指南.md](file://docs\Webhook通知配置指南.md#L284-L290)
- [Webhook功能实现总结.md](file://docs\Webhook功能实现总结.md#L352-L357)