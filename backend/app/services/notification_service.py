"""
通知服务
支持邮件和Webhook（钉钉、飞书）通知
配置从数据库读取
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import logging
from sqlalchemy.orm import Session

from app.config import settings
from app.models.config import AppConfig


class NotificationService:
    """通知服务类"""
    
    # 类级别的配置缓存
    _config = {}
    
    def __init__(self, db: Optional[Session] = None):
        self.logger = logging.getLogger(__name__)
        self.db = db
        
        # 如果提供了数据库会话，从数据库加载配置
        if db is not None:
            self.load_config(db)
        else:
            # 否则从 settings 加载（向后兼容）
            self.config = self._load_config_from_settings()
    
    def load_config(self, db: Session):
        """
        从数据库加载通知配置
        
        Args:
            db: 数据库会话
        """
        try:
            # 查询通知相关配置
            config_keys = [
                'EMAIL_ENABLED',
                'SMTP_SERVER',
                'SMTP_PORT',
                'EMAIL_FROM',
                'EMAIL_PASSWORD',
                'EMAIL_TO',
                'WEBHOOK_ENABLED',
                'WEBHOOK_URL',
                'WEBHOOK_TYPE',
                'WEBHOOK_KEYWORD'
            ]
            
            configs = db.query(AppConfig).filter(AppConfig.key.in_(config_keys)).all()
            
            # 转换为字典并缓存
            NotificationService._config = {cfg.key: cfg.value for cfg in configs}
            
            # 设置默认值
            NotificationService._config.setdefault('EMAIL_ENABLED', 'false')
            NotificationService._config.setdefault('SMTP_SERVER', settings.SMTP_SERVER)
            NotificationService._config.setdefault('SMTP_PORT', str(settings.SMTP_PORT))
            NotificationService._config.setdefault('EMAIL_FROM', '')
            NotificationService._config.setdefault('EMAIL_PASSWORD', '')
            NotificationService._config.setdefault('EMAIL_TO', '')
            NotificationService._config.setdefault('WEBHOOK_ENABLED', 'false')
            NotificationService._config.setdefault('WEBHOOK_URL', '')
            NotificationService._config.setdefault('WEBHOOK_TYPE', settings.WEBHOOK_TYPE.lower())
            NotificationService._config.setdefault('WEBHOOK_KEYWORD', settings.WEBHOOK_KEYWORD)
            
            # 更新实例配置
            self.config = self._load_config_from_db()
            
            self.logger.info(f"通知配置已从数据库加载: email={NotificationService._config.get('EMAIL_ENABLED')}, webhook={NotificationService._config.get('WEBHOOK_ENABLED')}")
            
        except Exception as e:
            self.logger.error(f"加载通知配置失败: {e}")
            # 使用默认配置（从 settings）
            self.config = self._load_config_from_settings()
    
    def _load_config_from_db(self) -> Dict:
        """从类级别缓存加载配置"""
        cfg = NotificationService._config
        return {
            'email_enabled': cfg.get('EMAIL_ENABLED', 'false').lower() == 'true',
            'smtp_server': cfg.get('SMTP_SERVER', ''),
            'smtp_port': int(cfg.get('SMTP_PORT', '587')),
            'email_from': cfg.get('EMAIL_FROM', ''),
            'email_password': cfg.get('EMAIL_PASSWORD', ''),
            'email_to': cfg.get('EMAIL_TO', ''),
            'webhook_enabled': cfg.get('WEBHOOK_ENABLED', 'false').lower() == 'true',
            'webhook_url': cfg.get('WEBHOOK_URL', ''),
            'webhook_type': cfg.get('WEBHOOK_TYPE', 'dingtalk').lower(),
            'webhook_keyword': cfg.get('WEBHOOK_KEYWORD', '')
        }
    
    def _load_config_from_settings(self) -> Dict:
        """从 settings 加载配置（向后兼容）"""
        return {
            'email_enabled': settings.EMAIL_ENABLED,
            'smtp_server': settings.SMTP_SERVER,
            'smtp_port': settings.SMTP_PORT,
            'email_from': settings.EMAIL_FROM,
            'email_password': settings.EMAIL_PASSWORD,
            'email_to': settings.EMAIL_TO,
            'webhook_enabled': settings.WEBHOOK_ENABLED,
            'webhook_url': settings.WEBHOOK_URL,
            'webhook_type': settings.WEBHOOK_TYPE.lower(),
            'webhook_keyword': settings.WEBHOOK_KEYWORD
        }
    
    def send_notification(self, notification: Dict) -> bool:
        """
        发送通知
        
        Args:
            notification: 通知数据，包含以下字段：
                - symbol: 股票代码
                - name: 股票名称
                - type: 通知类型
                - message: 通知消息
                - details: 详细内容（可选）
                - triggered_at: 触发时间
        
        Returns:
            是否发送成功
        """
        success = False
        
        # 尝试webhook通知
        if self.config['webhook_enabled']:
            webhook_success = self._send_webhook_notification(notification)
            if webhook_success:
                success = True
        
        # 尝试邮件通知
        if self.config['email_enabled']:
            email_success = self._send_email_notification(notification)
            if email_success:
                success = True
        
        return success
    
    def _send_email_notification(self, notification: Dict) -> bool:
        """发送邮件通知"""
        try:
            # 检查邮件配置是否完整
            if not all([self.config['smtp_server'], self.config['email_from'], 
                       self.config['email_password'], self.config['email_to']]):
                self.logger.warning("邮件配置不完整，跳过邮件通知")
                return False
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.config['email_from']
            msg['To'] = self.config['email_to']
            msg['Subject'] = f"股票监测提醒 - {notification.get('symbol', '')}"
            
            # 邮件正文
            details = notification.get('details', notification.get('message', ''))
            body = f"""
            <h2>股票监测提醒</h2>
            <p><strong>股票代码:</strong> {notification.get('symbol', '')}</p>
            <p><strong>股票名称:</strong> {notification.get('name', '')}</p>
            <p><strong>提醒类型:</strong> {notification.get('type', '')}</p>
            <p><strong>提醒内容:</strong> {notification.get('message', '')}</p>
            <p><strong>触发时间:</strong> {notification.get('triggered_at', '')}</p>
            <hr>
            <pre>{details}</pre>
            <hr>
            <p><em>此邮件由AI股票分析系统自动发送</em></p>
            """
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # 根据端口选择连接方式
            if self.config['smtp_port'] == 465:
                server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'], timeout=15)
            else:
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'], timeout=15)
                server.starttls()
            
            server.login(self.config['email_from'], self.config['email_password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"邮件发送成功: {notification.get('symbol', '')}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {e}")
            return False
    
    def _send_webhook_notification(self, notification: Dict) -> bool:
        """发送Webhook通知"""
        try:
            # 检查webhook配置是否完整
            if not self.config['webhook_url']:
                self.logger.warning("Webhook URL未配置，跳过Webhook通知")
                return False
            
            webhook_type = self.config['webhook_type']
            
            if webhook_type == 'dingtalk':
                return self._send_dingtalk_webhook(notification)
            elif webhook_type == 'feishu':
                return self._send_feishu_webhook(notification)
            else:
                self.logger.warning(f"不支持的webhook类型: {webhook_type}")
                return False
        
        except Exception as e:
            self.logger.error(f"Webhook发送失败: {e}")
            return False
    
    def _send_dingtalk_webhook(self, notification: Dict) -> bool:
        """发送钉钉Webhook通知"""
        try:
            import requests
            
            # 构建钉钉消息格式（包含自定义关键词）
            keyword = self.config.get('webhook_keyword', '')
            title_prefix = f"{keyword} - " if keyword else ""
            content_prefix = f"### {keyword} - " if keyword else "### "
            
            details = notification.get('details', notification.get('message', ''))
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"{title_prefix}{notification.get('symbol', '')} {notification.get('name', '')}",
                    "text": f"""{content_prefix}股票监测提醒

**股票代码**: {notification.get('symbol', '')}

**股票名称**: {notification.get('name', '')}

**提醒类型**: {notification.get('type', '')}

**提醒内容**: {notification.get('message', '')}

**触发时间**: {notification.get('triggered_at', '')}

---

{details}

_此消息由AI股票分析系统自动发送_"""
                }
            }
            
            response = requests.post(
                self.config['webhook_url'],
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    self.logger.info("钉钉Webhook发送成功")
                    return True
                else:
                    self.logger.error(f"钉钉Webhook返回错误: {result.get('errmsg')}")
                    return False
            else:
                self.logger.error(f"钉钉Webhook请求失败: HTTP {response.status_code}")
                return False
        
        except Exception as e:
            self.logger.error(f"钉钉Webhook发送异常: {e}")
            return False
    
    def _send_feishu_webhook(self, notification: Dict) -> bool:
        """发送飞书Webhook通知"""
        try:
            import requests
            
            details = notification.get('details', notification.get('message', ''))
            
            # 构建飞书消息格式
            data = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "content": f"📊 股票监测提醒 - {notification.get('symbol', '')}",
                            "tag": "plain_text"
                        },
                        "template": "blue"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "fields": [
                                {
                                    "is_short": True,
                                    "text": {
                                        "content": f"**股票代码**\n{notification.get('symbol', '')}",
                                        "tag": "lark_md"
                                    }
                                },
                                {
                                    "is_short": True,
                                    "text": {
                                        "content": f"**股票名称**\n{notification.get('name', '')}",
                                        "tag": "lark_md"
                                    }
                                }
                            ]
                        },
                        {
                            "tag": "div",
                            "fields": [
                                {
                                    "is_short": True,
                                    "text": {
                                        "content": f"**提醒类型**\n{notification.get('type', '')}",
                                        "tag": "lark_md"
                                    }
                                },
                                {
                                    "is_short": True,
                                    "text": {
                                        "content": f"**触发时间**\n{notification.get('triggered_at', '')}",
                                        "tag": "lark_md"
                                    }
                                }
                            ]
                        },
                        {
                            "tag": "div",
                            "text": {
                                "content": f"**提醒内容**\n{notification.get('message', '')}\n\n**详细信息**\n```\n{details}\n```",
                                "tag": "lark_md"
                            }
                        },
                        {
                            "tag": "hr"
                        },
                        {
                            "tag": "note",
                            "elements": [
                                {
                                    "tag": "plain_text",
                                    "content": "此消息由AI股票分析系统自动发送"
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(
                self.config['webhook_url'],
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.logger.info("飞书Webhook发送成功")
                    return True
                else:
                    self.logger.error(f"飞书Webhook返回错误: {result.get('msg')}")
                    return False
            else:
                self.logger.error(f"飞书Webhook请求失败: HTTP {response.status_code}")
                return False
        
        except Exception as e:
            self.logger.error(f"飞书Webhook发送异常: {e}")
            return False
    
    def reload_config(self, db: Session):
        """
        重新加载配置（用于配置更新后刷新）
        
        Args:
            db: 数据库会话
        """
        self.load_config(db)
    
    def get_config_status(self) -> Dict:
        """获取通知配置状态"""
        return {
            'email': {
                'enabled': self.config['email_enabled'],
                'configured': all([
                    self.config['smtp_server'],
                    self.config['email_from'],
                    self.config['email_password'],
                    self.config['email_to']
                ]),
                'smtp_server': self.config['smtp_server'] or '未配置',
                'email_to': self.config['email_to'] or '未配置'
            },
            'webhook': {
                'enabled': self.config['webhook_enabled'],
                'configured': bool(self.config['webhook_url']),
                'type': self.config['webhook_type'],
                'url': self.config['webhook_url'][:50] + '...' if self.config['webhook_url'] else '未配置'
            }
        }


# 全局通知服务实例（单例模式）
_notification_service = None

def get_notification_service(db: Optional[Session] = None) -> NotificationService:
    """
    获取通知服务实例（单例）
    
    Args:
        db: 数据库会话（可选），如果提供则从数据库加载配置
    
    Returns:
        通知服务实例
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(db=db)
    elif db is not None:
        # 如果提供了新的数据库会话，重新加载配置
        _notification_service.load_config(db)
    return _notification_service
