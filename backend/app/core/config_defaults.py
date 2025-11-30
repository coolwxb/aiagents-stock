"""
配置默认值定义
"""

CONFIG_DEFAULTS = {
    "DEEPSEEK_API_KEY": {
        "value": "",
        "description": "DeepSeek API密钥",
        "required": True,
        "type": "password",
    },
    "DEEPSEEK_BASE_URL": {
        "value": "https://api.deepseek.com/v1",
        "description": "DeepSeek API地址",
        "required": False,
        "type": "text",
    },
    "TUSHARE_TOKEN": {
        "value": "",
        "description": "Tushare数据接口Token（可选）",
        "required": False,
        "type": "password",
    },
    "MINIQMT_ENABLED": {
        "value": "false",
        "description": "启用MiniQMT量化交易",
        "required": False,
        "type": "boolean",
    },
    "MINIQMT_ACCOUNT_ID": {
        "value": "",
        "description": "MiniQMT账户ID",
        "required": False,
        "type": "text",
    },
    "MINIQMT_ACCOUNT_TYPE": {
        "value": "STOCK",
        "description": "MiniQMT账户类型（STOCK/CREDIT）",
        "required": False,
        "type": "select",
        "options": ["STOCK", "CREDIT"],
    },
    "MINIQMT_USERDATA_PATH": {
        "value": "E:\\zhongjin_qmt\\userdata_mini",
        "description": "MiniQMT用户数据目录",
        "required": False,
        "type": "text",
    },
    "EMAIL_ENABLED": {
        "value": "false",
        "description": "启用邮件通知",
        "required": False,
        "type": "boolean",
    },
    "SMTP_SERVER": {
        "value": "",
        "description": "SMTP服务器地址",
        "required": False,
        "type": "text",
    },
    "SMTP_PORT": {
        "value": "587",
        "description": "SMTP服务器端口",
        "required": False,
        "type": "text",
    },
    "EMAIL_FROM": {
        "value": "",
        "description": "发件人邮箱",
        "required": False,
        "type": "text",
    },
    "EMAIL_PASSWORD": {
        "value": "",
        "description": "邮箱授权码",
        "required": False,
        "type": "password",
    },
    "EMAIL_TO": {
        "value": "",
        "description": "收件人邮箱",
        "required": False,
        "type": "text",
    },
    "WEBHOOK_ENABLED": {
        "value": "false",
        "description": "启用Webhook通知",
        "required": False,
        "type": "boolean",
    },
    "WEBHOOK_TYPE": {
        "value": "dingtalk",
        "description": "Webhook类型（dingtalk/feishu）",
        "required": False,
        "type": "select",
        "options": ["dingtalk", "feishu"],
    },
    "WEBHOOK_URL": {
        "value": "",
        "description": "Webhook地址",
        "required": False,
        "type": "text",
    },
    "WEBHOOK_KEYWORD": {
        "value": "aiagents通知",
        "description": "Webhook自定义关键词（钉钉安全验证）",
        "required": False,
        "type": "text",
    },
    "MYSQL_ENABLED": {
        "value": "false",
        "description": "启用MySQL行情数据源",
        "required": False,
        "type": "boolean",
    },
    "MYSQL_HOST": {
        "value": "127.0.0.1",
        "description": "MySQL服务器地址",
        "required": False,
        "type": "text",
    },
    "MYSQL_PORT": {
        "value": "3306",
        "description": "MySQL端口",
        "required": False,
        "type": "text",
    },
    "MYSQL_USER": {
        "value": "root",
        "description": "MySQL用户名",
        "required": False,
        "type": "text",
    },
    "MYSQL_PASSWORD": {
        "value": "",
        "description": "MySQL密码",
        "required": False,
        "type": "password",
    },
    "MYSQL_DATABASE": {
        "value": "choose_stock",
        "description": "MySQL数据库名称",
        "required": False,
        "type": "text",
    },
    "MYSQL_STOCK_TABLE": {
        "value": "stock_history",
        "description": "存放行情数据的数据表名称",
        "required": False,
        "type": "text",
    },
}

