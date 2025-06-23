#!/usr/bin/env bash
set -e

SCRIPT_NAME="dch-wrapper"
INSTALL_DIR="$HOME/.local/bin"
TARGET="$INSTALL_DIR/$SCRIPT_NAME"

# 创建目标目录
if [ ! -d "$INSTALL_DIR" ]; then
    echo "[INFO] 创建目录 $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
fi

# 拷贝脚本
cp "$SCRIPT_NAME" "$TARGET"
chmod +x "$TARGET"
echo "[OK] 已安装 $SCRIPT_NAME 到 $TARGET"

# 检查~/.local/bin是否在PATH中
if ! echo ":$PATH:" | grep -q ":$INSTALL_DIR:"; then
    echo "[WARN] $INSTALL_DIR 不在你的PATH环境变量中。"
    echo "你可以将以下内容添加到你的shell配置文件（如~/.bashrc, ~/.zshrc等）："
    echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
    echo "然后重新加载配置或重启终端。"
else
    echo "[OK] $INSTALL_DIR 已在PATH中，你可以直接使用 $SCRIPT_NAME 命令。"
fi 