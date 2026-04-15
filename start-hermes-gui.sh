#!/bin/bash
# Hermes GUI 启动脚本 - 自动启动 Bridge 然后打开 App

echo "🚀 启动 Hermes Bridge..."
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/hermes-agent/server/chat_bridge.py &
BRIDGE_PID=$!

echo "⏳ 等待 Bridge 启动..."
sleep 2

# 检查 Bridge 是否启动成功
if curl -s http://127.0.0.1:9120/health > /dev/null 2>&1; then
    echo "✅ Bridge 已就绪"
    echo ""
    echo "📱 打开 Hermes GUI..."
    echo ""
    echo "可选模型:"
    echo "  • Qwen 3.6 Plus"
    echo "  • DeepSeek Chat"
    echo ""
    open ~/work/code/hermes-gui/src-tauri/target/release/bundle/macos/Hermes\ GUI.app
else
    echo "❌ Bridge 启动失败"
    kill $BRIDGE_PID 2>/dev/null
    exit 1
fi
