@echo off
echo ===================================
echo  外卖评论爬虫系统 - 一键启动
echo ===================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装 Python 依赖...
pip install -r requirements.txt -q

REM 安装 Playwright 浏览器
echo [2/3] 安装 Playwright 浏览器（首次运行需要几分钟）...
python -m playwright install chromium

REM 启动 Web GUI
echo [3/3] 启动 Web 界面...
echo.
echo  请在浏览器访问: http://localhost:8080
echo  按 Ctrl+C 停止服务
echo.
python main.py

pause
