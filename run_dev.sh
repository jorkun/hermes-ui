#!/bin/bash
# Hermes GUI 启动脚本

cd "$(dirname "$0")"

echo "✦ 启动 Hermes GUI..."

# 1. 启动 Bridge Server（后台）
echo "→ 启动 Bridge Server (端口 9120)..."
/Users/zkk/.hermes/hermes-agent/venv/bin/python3 server/chat_bridge.py &
BRIDGE_PID=$!
sleep 1

# 2. 启动 Vite Dev Server
echo "→ 启动前端 Dev Server (端口 5173)..."
pnpm dev &

# 3. 打开浏览器
sleep 2
open http://localhost:5173

echo ""
echo "✦ Hermes GUI 已启动"
echo "  前端: http://localhost:5173"
echo "  Bridge: ws://localhost:9120/ws/chat"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待信号
trap "kill $BRIDGE_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
