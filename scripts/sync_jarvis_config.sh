#!/bin/bash

# sync_jarvis_config.sh
# 用于将全局配置同步到当前工程目录的 .jarvis/ 子目录
# 用法: ./sync_jarvis_config.sh [--force]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
FORCE_MODE=false
SOURCE_DIR="$HOME/.jarvis"
# 目标目录：使用独立的 .jarvis_config 目录，避免与项目 .jarvis 混在一起
TARGET_DIR=".jarvis_config"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE_MODE=true
            shift
            ;;
        --help|-h)
            echo "用法: $0 [--force]"
            echo ""
            echo "选项:"
            echo "  --force, -f    强制覆盖，不询问确认"
            echo "  --help, -h     显示此帮助信息"
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知参数 $1${NC}"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Jarvis 全局配置同步工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查源目录
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}错误: 源目录不存在: $SOURCE_DIR${NC}"
    echo "请确保 Jarvis 已正确安装并运行过"
    exit 1
fi

# 检查目标目录
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${YELLOW}警告: 目标目录不存在: $TARGET_DIR${NC}"
    echo "正在创建目录..."
    mkdir -p "$TARGET_DIR"
    echo -e "${GREEN}目录已创建${NC}"
fi

# 显示同步信息
echo -e "${YELLOW}同步信息:${NC}"
echo "  源目录: $SOURCE_DIR"
echo "  目标目录: $TARGET_DIR"
echo ""

# 定义要同步的内容
SYNC_ITEMS=(
    "config.yaml:全局配置"
    "memory:记忆存储"
    "methodologies:方法论"
    "rules:规则"
    "tools:自定义工具"
)

echo -e "${YELLOW}将要同步以下内容:${NC}"
for item in "${SYNC_ITEMS[@]}"; do
    name="${item%%:*}"
    desc="${item##*:}"
    if [ -e "$SOURCE_DIR/$name" ]; then
        echo -e "  ${GREEN}✓${NC} $desc ($SOURCE_DIR/$name)"
    else
        echo -e "  ${YELLOW}○${NC} $desc (不存在，将跳过)"
    fi
done
echo ""

# 确认操作
if [ "$FORCE_MODE" = false ]; then
    read -p "是否继续同步? [y/N]: " -r
    case "$REPLY" in
        y|Y )
            echo "开始同步..."
            ;;
        * )
            echo "已取消同步"
            exit 0
            ;;
    esac
fi

# 创建目录结构
mkdir -p "$TARGET_DIR/memory"
mkdir -p "$TARGET_DIR/methodologies"
mkdir -p "$TARGET_DIR/rules"
mkdir -p "$TARGET_DIR/tools"

# 同步函数
sync_item() {
    local src="$1"
    local dst="$2"
    local name="$3"
    
    if [ ! -e "$src" ]; then
        echo -e "${YELLOW}跳过: $name (源不存在)${NC}"
        return
    fi
    
    if [ -d "$src" ]; then
        # 目录同步
        if [ -n "$(ls -A "$src" 2>/dev/null)" ]; then
            # 使用 rsync 或 cp 同步目录
            if command -v rsync &> /dev/null; then
                rsync -av --exclude='__pycache__' "$src/" "$dst/"
            else
                cp -r "$src/"* "$dst/" 2>/dev/null || true
                # 移除 __pycache__ 目录
                find "$dst" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
            fi
            echo -e "${GREEN}✓${NC} 已同步目录: $name"
        else
            echo -e "${YELLOW}○${NC} 目录为空: $name"
        fi
    else
        # 文件同步
        cp "$src" "$dst"
        echo -e "${GREEN}✓${NC} 已同步文件: $name"
    fi
}

# 执行同步
echo ""
echo -e "${BLUE}开始同步...${NC}"
echo ""

# 同步配置文件
sync_item "$SOURCE_DIR/config.yaml" "$TARGET_DIR/config.yaml" "config.yaml"

# 同步记忆目录
if [ -d "$SOURCE_DIR/memory" ]; then
    for subdir in "$SOURCE_DIR/memory"/*/; do
        if [ -d "$subdir" ]; then
            subname=$(basename "$subdir")
            mkdir -p "$TARGET_DIR/memory/$subname"
            sync_item "$subdir" "$TARGET_DIR/memory/$subname/" "memory/$subname"
        fi
    done
    # 也同步 memory 目录下的直接文件（如果有的话）
    for f in "$SOURCE_DIR/memory"/*.json; do
        [ -e "$f" ] && sync_item "$f" "$TARGET_DIR/memory/" "memory/*.json"
    done
fi

# 同步方法论
sync_item "$SOURCE_DIR/methodologies" "$TARGET_DIR/methodologies/" "methodologies"

# 同步规则
sync_item "$SOURCE_DIR/rules" "$TARGET_DIR/rules/" "rules"

# 同步工具
sync_item "$SOURCE_DIR/tools" "$TARGET_DIR/tools/" "tools"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}同步完成!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "配置已同步到: $(pwd)/$TARGET_DIR"
echo ""
echo "提示:"
echo "  - 如果需要恢复，请使用反向同步"
echo "  - 或直接将 $TARGET_DIR 目录复制到其他电脑的 ~/.jarvis/"
