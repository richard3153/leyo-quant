#!/bin/bash
# Railway 部署自动化脚本
# 使用方法: railway login 后运行此脚本

set -e

PROJECT_NAME="leyo-quant-backend"
REGION="us-east4"  # 或 singapore, london, etc.
GITHUB_REPO="https://github.com/richard3153/leyo-quant"

echo "=========================================="
echo "  Railway 自动化部署脚本"
echo "=========================================="

# 检查是否已登录
if ! railway whoami > /dev/null 2>&1; then
    echo "❌ 请先运行: railway login"
    exit 1
fi

echo "✅ 已登录 Railway"

# 创建项目
echo "📦 创建 Railway 项目..."
PROJECT_OUTPUT=$(railway init --name "$PROJECT_NAME" --json 2>/dev/null || echo '{}')
PROJECT_ID=$(echo "$PROJECT_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")

if [ -z "$PROJECT_ID" ]; then
    echo "⚠️  项目已存在或无法自动创建，请手动创建后继续"
    echo "   访问: https://railway.app/dashboard"
    echo "   1. 点击 'New Project'"
    echo "   2. 选择 'Deploy from GitHub repo'"
    echo "   3. 选择 richard3153/leyo-quant"
    echo "   4. 设置 Root Directory 为 backend"
    exit 1
fi

echo "✅ 项目 ID: $PROJECT_ID"

# 连接 GitHub 仓库
echo "🔗 连接 GitHub 仓库..."
railway link "$PROJECT_ID" 2>/dev/null || true

# 配置环境变量
echo "🔧 配置环境变量..."
railway environment add production 2>/dev/null || true

# 部署
echo "🚀 触发部署..."
railway up --service backend

echo ""
echo "=========================================="
echo "  部署已触发！"
echo "  访问 https://railway.app/dashboard 查看状态"
echo "=========================================="
