# dch-wrapper

> 说明：这个工具大部分代码由 AI 生成，主要用于个人日常使用，不保证质量或适配所有场景。

`dch-wrapper` 是一个小脚本，用来简化 Debian 包维护时的 `dch` 操作：
- 自动整理最近的 Git 提交作为 changelog 草稿
- 自动补齐 `DEBEMAIL` / `DEBFULLNAME`
- 先写入 changelog，再打开编辑器给你手动确认

适合已经有 `debian/` 目录、但不想每次手敲 `dch` 参数的场景。

## 主要功能

- 检查 `dch` 是否可用（来自 `devscripts`）
- 从 Git 配置读取作者信息并设置打包环境变量
- 从最新 Git tag 推断版本号（无 tag 时默认 `1.0.0`）
- 生成自上次 tag 以来的提交摘要
- 当提交过多时，支持只取最近 30 条
- 运行前检查工作区状态：
  - `debian/changelog` 未提交时拒绝执行
  - 其他未提交改动会先提醒再继续
- 支持 `--dry-run` 查看将执行的命令

## 安装

```bash
bash install.sh
```

默认安装到 `~/.local/bin/dch-wrapper`。

## 依赖

- Python 3.6+
- Git
- `devscripts`（提供 `dch`）

Debian/Ubuntu 安装示例：

```bash
sudo apt-get install devscripts
```

## 用法

```bash
# 自动从 git log 生成 changelog
./dch-wrapper

# 自定义 changelog 文本
./dch-wrapper "修复打包脚本"

# 指定 distribution
./dch-wrapper -D testing "测试发布"

# 仅预览，不实际执行 dch
./dch-wrapper --dry-run
```

查看参数：

```bash
./dch-wrapper --help
```

## 工作流程（简版）

1. 检查 `dch` 与项目目录状态
2. 准备环境变量与版本号
3. 生成 changelog 内容
4. 执行 `dch` 写入
5. 执行 `dch -e` 让你手动修改并确认

## 许可证

Unlicense（见 `LICENSE`）。
