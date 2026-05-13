#!/bin/bash
set -e
echo "==================================="
echo " 外卖评论爬虫系统 - 一键启动"
echo "==================================="
echo

# 安装依赖
echo "[1/3] 安装 Python 依赖..."
pip3 install -r requirements.txt -q

# 安装 Playwright 浏览器
echo "[2/3] 安装 Playwright 浏览器..."
python3 -m playwright install chromium

# 启动
echo "[3/3] 启动 Web 界面..."
echo
echo " 请在浏览器访问: http://localhost:8080"
echo " 按 Ctrl+C 停止服务"
echo
python3 main.py
