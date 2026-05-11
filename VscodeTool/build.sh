#!/bin/bash

# Jarvis VSCode Plugin Build Script
# 用于构建 Jarvis VSCode 插件并生成 .vsix 文件

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================"
echo "Jarvis VSCode Plugin Build Script"
echo "======================================"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "错误：未找到 Node.js，请先安装 Node.js (建议 18+)"
    exit 1
fi

echo "Node.js 版本:"
node --version
echo ""

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "错误：未找到 npm"
    exit 1
fi

echo "npm 版本:"
npm --version
echo ""

# 安装依赖
echo "正在安装依赖..."
npm install
echo ""

# 编译 TypeScript
echo "正在编译 TypeScript..."
npm run build
echo ""

# 检查 vsce
if ! command -v vsce &> /dev/null; then
    echo "警告：vsce 未全局安装，尝试使用本地安装..."
    if [ -f "./node_modules/.bin/vsce" ]; then
        VSCE_CMD="./node_modules/.bin/vsce"
    else
        echo "错误：vsce 未安装，请运行 'npm install -g @vscode/vsce'"
        exit 1
    fi
else
    VSCE_CMD="vsce"
fi

# 打包
echo "正在打包生成 .vsix 文件..."
echo "y" | $VSCE_CMD package --no-yarn
echo ""

# 显示生成的文件
echo "======================================"
echo "构建成功！"
echo "======================================"
echo ""
echo "生成的 .vsix 文件:"
ls -lh *.vsix
echo ""
echo "安装方法:"
echo "  1. VSCode 图形界面："
echo "     Ctrl+Shift+X → 点击右上角 '...' → '从 VSIX 安装...'"
echo ""
echo "  2. 命令行安装："
echo "     code --install-extension $(ls *.vsix | head -n1)"
echo ""
