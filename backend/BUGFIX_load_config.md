# Bug Fix: load_config() Method Signature Error

## Issue

Error message:
```
配置加载失败: load_config() takes 1 positional argument but 2 were given
```

## Root Cause

The `load_config()` method in `backend/app/data/data_source.py` was missing the `self` parameter in its method signature.

### Before (Incorrect):
```python
def load_config(config_dict: dict):
    self.tushare_token = config_dict.getenv('TUSHARE_TOKEN', '')
    # ...
```

### After (Correct):
```python
def load_config(self, config_dict: dict):
    """从配置字典加载配置"""
    self.tushare_token = config_dict.get('TUSHARE_TOKEN', '')
    # ...
```

## Changes Made

1. **Added `self` parameter** to the method signature
2. **Changed `getenv()` to `get()`** - Since `config_dict` is a dictionary (not an environment object), we should use `dict.get()` instead of `getenv()`
3. **Added docstring** for better documentation

## How It's Called

In `backend/app/main.py`:
```python
# Load config from database
configs = db.query(AppConfig).all()
config_dict = {cfg.key: cfg.value for cfg in configs}

# Initialize data source manager
from app.data.data_source import data_source_manager
data_source_manager.load_config(config_dict)  # Now works correctly
```

## Impact

This fix ensures that:
- The data source manager can properly load configuration from the database
- QMT, MySQL, and Tushare data sources are initialized with correct settings
- The application startup process completes successfully

## Testing

To verify the fix:
1. Start the backend server
2. Check that no "配置加载失败" error appears
3. Verify that data sources are initialized correctly
4. Check the console output for initialization messages

Expected output:
```
✅ 数据源管理器初始化完成
✅ QMT服务配置加载完成
```
