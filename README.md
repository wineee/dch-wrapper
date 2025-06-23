# dch-wrapper

一个帮助非deb开发者使用dch命令的Python脚本，自动化了Debian包开发中的变更日志管理流程。

## 功能特性

- 🔍 **自动检查dch命令**: 检查系统是否安装了devscripts包，如果没有则提供安装指导
- 📧 **智能环境变量配置**: 自动从git配置中获取作者信息，设置DEBEMAIL和DEBFULLNAME环境变量
- 📦 **自动版本号获取**: 自动从git tag获取最新版本号，如果没有tag则使用默认版本号1.0.0
- 📝 **自动生成变更日志**: 读取git log从上次tag到当前commit的变化，使用简略的提交信息（不包含commit hash）
- 🔒 **Git状态检查**: 执行前检查git工作目录状态：
  - 如果debian/changelog有未commit的修改，直接拒绝运行
  - 如果其他文件有未commit的修改，警告用户并询问是否继续
- 🚀 **两步执行dch**: 自动分两步执行dch命令：
  - 第一步：调用dch命令添加变更日志到changelog文件
  - 第二步：调用dch -e命令打开编辑器，让用户手动调整和编辑变更日志

## 安装要求

### 系统依赖
- Python 3.6+
- git
- devscripts包（包含dch命令）

### 安装devscripts
```bash
# Ubuntu/Debian
sudo apt-get install devscripts

# CentOS/RHEL
sudo yum install devscripts

# Fedora
sudo dnf install devscripts
```

## 使用方法

### 基本用法
```bash
# 使用git log作为变更日志
python3 dch_wrapper.py

# 或者直接执行（需要执行权限）
./dch_wrapper.py
```

### 高级用法
```bash
# 使用自定义消息
python3 dch_wrapper.py "修复了重要的bug"

# 模拟执行，不实际调用dch
python3 dch_wrapper.py --dry-run

# 显示帮助信息
python3 dch_wrapper.py --help

# 显示版本信息
python3 dch_wrapper.py --version
```

## 参数说明

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `--help` | `-h` | 显示帮助信息 |
| `--version` | `-v` | 显示版本信息 |
| `--dry-run` | - | 只显示将要执行的操作，不实际执行 |
| `message` | - | 自定义提交消息，覆盖自动生成的git log |

## 工作流程

1. **检查环境**: 验证dch命令是否可用，如果不可用则提示安装devscripts
2. **配置环境变量**: 检查DEBEMAIL和DEBFULLNAME环境变量，如果未设置则从git配置中获取
3. **检查Git状态**: 检查git工作目录状态：
   - 如果debian/changelog有未commit的修改，直接拒绝运行
   - 如果其他文件有未commit的修改，警告用户并询问是否继续
4. **获取版本号**: 自动从git tag获取最新版本号，如果没有tag则使用默认版本号1.0.0
5. **生成变更日志**: 读取git log从上次tag到当前commit的变化
6. **执行dch命令**: 分两步执行：
   - 第一步：调用dch命令添加变更日志到changelog文件
   - 第二步：调用dch -e命令打开编辑器，让用户手动调整和编辑变更日志

## 项目结构

```
dch-wrapper/
├── README.md          # 项目说明文档
├── dch_wrapper.py     # 主脚本文件
└── .git/             # Git版本控制目录
```

## 错误处理

脚本包含完善的错误处理机制：

- **dch命令未找到**: 提供详细的安装指导
- **debian目录不存在**: 提示用户切换到正确的项目目录
- **debian/changelog有未commit修改**: 直接拒绝运行，提供解决建议
- **其他文件有未commit修改**: 警告用户并询问是否继续执行
- **git配置缺失**: 使用默认值并给出警告
- **git操作失败**: 提供友好的错误信息

## 开发说明

### 代码结构
- `DchWrapper`类: 主要的包装器类，包含所有核心功能
- `check_dch_available()`: 检查dch命令可用性
- `setup_environment_variables()`: 配置环境变量
- `check_git_status()`: 检查git工作目录状态
- `get_latest_version_from_git_tag()`: 从git tag获取最新版本号
- `get_git_changes_since_last_tag()`: 获取git变更日志
- `run_dch()`: 执行dch命令

### 扩展性
脚本采用模块化设计，易于扩展和维护。可以轻松添加新的功能，如：
- 支持不同的版本号格式
- 集成其他包管理工具
- 添加更多的配置选项

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证，详见LICENSE文件。