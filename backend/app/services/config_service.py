"""
配置管理服务
"""
from __future__ import annotations

from typing import Dict, Tuple

from sqlalchemy.orm import Session

from app.core.config_defaults import CONFIG_DEFAULTS
from app.models.config import AppConfig


class ConfigService:
    """配置管理服务类，使用数据库存储配置"""

    def __init__(self, db: Session):
        self.db = db
        self.defaults = CONFIG_DEFAULTS
        self._ensure_table()
        self._ensure_defaults()

    async def get_config(self) -> Dict[str, str]:
        """获取当前配置"""
        return self._load_config()

    async def update_config(self, config_data: Dict) -> Dict[str, str]:
        """更新配置并返回最新配置"""
        sanitized = self._sanitize_config(config_data)
        merged = {**self._load_config(), **sanitized}

        is_valid, message = self._validate_with_defaults(merged)
        if not is_valid:
            raise ValueError(message)

        for key, value in sanitized.items():
            self._upsert_config(key, value)

        self.db.commit()
        return self._load_config()

    async def validate_config(self, config_data: Dict) -> Dict[str, str]:
        """验证配置有效性"""
        sanitized = self._sanitize_config(config_data)
        merged = {**self._load_config(), **sanitized}
        is_valid, message = self._validate_with_defaults(merged)

        if not is_valid:
            raise ValueError(message)
        return {"success": True, "message": message}

    async def test_config(self, config_type: str | None) -> Dict[str, str]:
        """测试指定配置的准备情况"""
        if not config_type:
            raise ValueError("config_type 为必填参数")

        config_type = config_type.lower()
        config = self._load_config()

        testers = {
            "deepseek": self._test_deepseek,
            "email": self._test_email,
            "webhook": self._test_webhook,
            "mysql": self._test_mysql,
        }

        tester = testers.get(config_type)
        if not tester:
            raise ValueError(f"暂不支持的配置类型: {config_type}")

        success, message = tester(config)
        if not success:
            raise ValueError(message)

        return {"success": True, "message": message}

    @staticmethod
    def _sanitize_config(config_data: Dict) -> Dict[str, str]:
        """将前端传入的配置规范为字符串"""
        sanitized = {}
        for key, value in (config_data or {}).items():
            if isinstance(value, bool):
                sanitized[key] = "true" if value else "false"
            elif value is None:
                sanitized[key] = ""
            else:
                sanitized[key] = str(value)
        return sanitized

    @staticmethod
    def _test_deepseek(config: Dict[str, str]) -> Tuple[bool, str]:
        api_key = config.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            return False, "DeepSeek API Key 未配置"
        if len(api_key) < 20:
            return False, "DeepSeek API Key 格式看起来不正确"
        return True, "DeepSeek 配置看起来有效"

    @staticmethod
    def _test_email(config: Dict[str, str]) -> Tuple[bool, str]:
        enabled = config.get("EMAIL_ENABLED", "false").lower() == "true"
        if not enabled:
            return False, "邮件通知未启用"

        required_keys = ["SMTP_SERVER", "SMTP_PORT", "EMAIL_FROM", "EMAIL_PASSWORD", "EMAIL_TO"]
        missing = [key for key in required_keys if not config.get(key)]
        if missing:
            return False, f"邮件配置缺少必要字段: {', '.join(missing)}"

        return True, "邮件配置字段完整，可继续使用"

    @staticmethod
    def _test_webhook(config: Dict[str, str]) -> Tuple[bool, str]:
        enabled = config.get("WEBHOOK_ENABLED", "false").lower() == "true"
        if not enabled:
            return False, "Webhook 通知未启用"

        if not config.get("WEBHOOK_URL"):
            return False, "Webhook 地址未配置"

        if config.get("WEBHOOK_TYPE", "dingtalk") == "dingtalk" and not config.get("WEBHOOK_KEYWORD"):
            return False, "钉钉 Webhook 需要配置关键词"

        return True, "Webhook 配置字段完整，可继续使用"

    @staticmethod
    def _test_mysql(config: Dict[str, str]) -> Tuple[bool, str]:
        enabled = config.get("MYSQL_ENABLED", "false").lower() == "true"
        if not enabled:
            return False, "MySQL 行情库未启用"

        required = ["MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_DATABASE", "MYSQL_STOCK_TABLE"]
        missing = [key for key in required if not config.get(key)]
        if missing:
            return False, f"MySQL 配置缺少字段: {', '.join(missing)}"

        return True, "MySQL 配置字段完整，可继续使用"

    def _ensure_table(self):
        """确保配置表存在"""
        AppConfig.__table__.create(bind=self.db.get_bind(), checkfirst=True)

    def _ensure_defaults(self):
        """将默认配置写入数据库（不存在时）"""
        existing_keys = {key for (key,) in self.db.query(AppConfig.key).all()}
        created = False
        for key, meta in self.defaults.items():
            if key not in existing_keys:
                self.db.add(AppConfig(key=key, value=meta["value"], description=meta["description"]))
                created = True
        if created:
            self.db.commit()

    def _load_config(self) -> Dict[str, str]:
        """从数据库读取配置，缺失项使用默认值"""
        rows = self.db.query(AppConfig).all()
        config = {row.key: row.value for row in rows}
        for key, meta in self.defaults.items():
            config.setdefault(key, meta["value"])
        return config

    def _upsert_config(self, key: str, value: str):
        """更新或插入配置"""
        entry = self.db.query(AppConfig).filter(AppConfig.key == key).one_or_none()
        if entry:
            entry.value = value
        else:
            description = self.defaults.get(key, {}).get("description")
            self.db.add(AppConfig(key=key, value=value, description=description))

    def _validate_with_defaults(self, config: Dict[str, str]) -> Tuple[bool, str]:
        """基于默认定义校验配置"""
        for key, meta in self.defaults.items():
            if meta.get("required") and not config.get(key):
                return False, f"必填项 {meta['description']} 不能为空"

        api_key = config.get("DEEPSEEK_API_KEY", "")
        if api_key and len(api_key) < 20:
            return False, "DeepSeek API Key格式不正确（长度太短）"

        return True, "配置验证通过"
