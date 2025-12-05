@echo off
chcp 65001 >nul
echo 正在启动Backend服务...
echo.

REM 激活conda环境并启动服务
call conda activate ai-agent

REM 设置项目根目录到 PYTHONPATH，让 Python 能找到 xtquant 模块
set PYTHONPATH=%~dp0..;%PYTHONPATH%

cd /d "%~dp0"
echo 提示: 所有配置从数据库读取，不使用 .env 文件
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
