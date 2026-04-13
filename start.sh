#!/bin/bash
# LeyoQuant - 乐友量化系统启动脚本

echo "🎯 乐友量化投资系统 v1.0"
echo "========================"

# 启动后端
echo "▶ 启动后端服务..."
cd backend
pip install -r requirements.txt -q
python main.py &
BACKEND_PID=$!

# 启动前端
echo "▶ 启动前端服务..."
cd ../frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 系统启动完成！"
echo "   后端: http://localhost:8000"
echo "   前端: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"

wait
