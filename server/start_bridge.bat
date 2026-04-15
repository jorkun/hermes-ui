@echo off
echo Starting Hermes Bridge Server...

REM 查找 Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM 设置环境变量
set HERMES_ROOT=%USERPROFILE%\.hermes\hermes-agent

REM 启动 Bridge
cd /d "%HERMES_ROOT%"
python server\chat_bridge.py

pause
