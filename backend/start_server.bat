@echo off
chcp 65001 >nul
echo 正在启动Backend服务...
echo.

REM 激活conda环境并启动服务
call conda activate ai-agent
cd /d "%~dp0"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
