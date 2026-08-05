#!/bin/bash
# LeyoQuant - 乐友量化系统启动脚本（前台常驻版）
# launchd 上下文：全部使用绝对路径，绕过 PATH / 内置 npm 封装限制

ROOT_DIR="/Users/ffzwai/.qclaw/workspace-agent-c5dfcbaa/leyo-quant"
PYTHON_BIN="/Users/ffzwai/Library/Application Support/QClaw/python/bin/python3.11"
NODE_BIN="/Users/ffzwai/Library/Application Support/QClaw/openclaw/config/bin/node/node"
VITE_BIN="/Users/ffzwai/.qclaw/workspace-agent-c5dfcbaa/leyo-quant/frontend/node_modules/.bin/vite"

cd "$ROOT_DIR"

echo "🎯 乐友量化投资系统 v1.0"
echo "========================"

# 后端
echo "▶ 启动后端服务..."
cd backend
nohup "$PYTHON_BIN" main.py > /tmp/leyo_backend.log 2>&1 &
BACKEND_PID=$!

# 前端（直接用 node 跑 vite，绕开 npm 封装）
echo "▶ 启动前端服务..."
cd "$ROOT_DIR/frontend"
nohup "$NODE_BIN" "$VITE_BIN" > /tmp/leyo_frontend.log 2>&1 &
FRONTEND_PID=$!

echo ""
echo "✅ 系统启动完成！"
echo "   后端: http://localhost:8000"
echo "   前端: http://localhost:5173"
echo ""

# 前台常驻
while true; do
  sleep 3600
done
