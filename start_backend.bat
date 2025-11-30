@echo off
echo 激活 conda 环境并启动 FastAPI 服务...

REM 激活 conda 环境
call conda activate ai-agent

REM 切换到 backend 目录
cd /d "%~dp0backend"

REM 启动 FastAPI 服务
echo 启动 FastAPI 服务在 http://localhost:8000
echo API 文档: http://localhost:8000/api/docs
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause