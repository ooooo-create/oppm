# OPPM - Portable Package Manager

> 🚀 A lightweight portable application manager for Windows. Other OS maybe also work, but I'm not sure if there's a need for it.

[![Python](https://img.shields.io/badge/python-3.13%2B-blue)]()

## 📖 什么是 OPPM？

OPPM (Ooooo's Portable Package Manager) 是一个专为 Windows 设计的**便携应用管理工具**。

### 💡 核心价值

你是否经常遇到这样的困扰？

- 📦 **下载了 .zip 压缩包**：里面是独立软件（开源工具、模拟器、游戏 MOD）— 解压到哪里？`C:\Downloads\my-tool-v1.2`？还是 `D:\Program Files\SomeTool`？时间一长，完全忘了装过什么、装在哪里。

- 📄 **下载了单独的 .exe 文件**：很多命令行工具是一个二进制文件 — 如果手动下载之后放在哪里？`C:\Windows\System32`（危险！）？还是手动创建 `C:\bin` 目录管理？

**OPPM 就是为了解决这些问题而生的！** 它帮你：

- ✅ **统一管理**：所有便携软件集中存放在 `~/.oppm/apps/`，一目了然
- ✅ **自动 PATH 管理**：通过 shims 机制，无需手动配置环境变量
- ✅ **保持系统干净**：不污染注册表，不修改系统目录
- ✅ **轻松迁移**：整个 `.oppm` 目录打包即可迁移到新电脑

### 📦 支持的格式

- ✅ 单独的 `.exe` 文件
- ✅ `.zip`、`.tar.gz`、`.tar.bz2` 等压缩包
- ✅ 整个文件夹（便携版软件目录）

## 🚀 快速开始

### 安装

```bash
# 使用 uv 安装（推荐）
uv tool install oppm

# 使用 pip 安装
pip install oppm

# 或者从源码安装
git clone https://github.com/ooooo-create/ppm.git
cd ppm
pip install -e .
```

### 初始化

```bash
# 创建 OPPM 目录结构（默认在 ~/.oppm）
oppm init

# 将 shims 目录添加到 PATH（重要！）
# Windows PowerShell：
$env:Path += ";$HOME\.oppm\shims"
# 或永久添加到系统环境变量
```

### 基本使用

```bash
# 1. 安装应用（从本地文件）
oppm install path/to/app.exe
oppm install path/to/app.zip -n myapp

# 2. 查看已安装的应用
oppm list

# 3. 添加可执行文件到 PATH
oppm exe add path/to/tool.exe
oppm exe show

# 4. 删除应用
oppm remove myapp

# 5. 清理所有应用
oppm clean
```

## 📚 命令参考

### 基础命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `oppm init` | 初始化 OPPM | `oppm init -r D:\tools` |
| `oppm list` | 列出所有已安装应用 | `oppm list` |
| `oppm install <path>` | 安装应用 | `oppm install app.zip -n vim` |
| `oppm remove <name>` | 卸载应用 | `oppm remove vim` |
| `oppm clean` | 删除所有应用(包括 Shim 目录) | `oppm clean` |

### Shim 管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `oppm exe add <path>` | 添加可执行文件 | `oppm exe add tool.exe -e mytool` |
| `oppm exe delete <name>` | 删除 shim | `oppm exe delete mytool.exe` |
| `oppm exe show` | 显示所有 shims | `oppm exe show` |

### 高级功能

| 命令 | 说明 | 示例 |
|------|------|------|
| `oppm update` | 同步元数据 | `oppm update` |
| `oppm migrate <new_path>` | 迁移到新目录 | `oppm migrate D:\newpath` |
| `oppm pack` | 打包整个 OPPM 目录为 tar.gz | `oppm pack -o backup.tar.gz` |
| `oppm rebuild <archive>` | 从打包文件恢复 OPPM | `oppm rebuild backup.tar.gz -r D:\newpath` |
| `oppm health [--fix]` | 诊断和检查完整性 | `oppm health --fix` |

## 🏗️ 目录结构

```
~/.oppm/
├── apps/           # 已安装的应用
│   ├── geek/
│   ├── jj/
│   └── ...
├── shims/          # 可执行文件的符号链接（需加入 PATH）
│   ├── geek.exe
│   ├── jj.exe
│   └── ...
└── meta.json       # 应用元数据
```

## 💡 工作原理

1. **安装应用**：将应用文件/目录复制或解压到 `~/.oppm/apps/`
2. **创建 shims**：为可执行文件创建符号链接到 `~/.oppm/shims/`
3. **PATH 管理**：只需将 `shims/` 目录加入 PATH，所有工具即可全局访问

## 🔧 高级配置

### 自定义安装目录

```bash
# 使用自定义根目录
oppm init -r D:\MyTools

# 配置文件位置
~/.oppmconfig  # TOML 格式
```

### 示例配置文件

```toml
[config]
root_dir = "C:/Users/YourName/.oppm"
apps_dir = "C:/Users/YourName/.oppm/apps"
meta_file = "C:/Users/YourName/.oppm/meta.json"
shims_dir = "C:/Users/YourName/.oppm/shims"
```

### 场景 1：迁移到新电脑

```bash
# 使用 pack 和 rebuild 命令（推荐）
# 在旧电脑上
oppm pack -o oppm-backup.tar.gz

# 复制 oppm-backup.tar.gz 到新电脑后
# 在新电脑上
oppm rebuild oppm-backup.tar.gz -r D:\MyTools\.oppm
# 或者
oppm init -r D:\MyTools\.oppm
oppm rebuild oppm-backup.tar.gz
```

**💡 提示**：使用 `pack/rebuild` 命令会自动更新所有路径。Shims 使用相对路径创建，解压后会自动工作！

## 🐛 故障排除

### Shims 不工作？

```bash
# 1. 检查 shims 目录是否在 PATH 中
echo $env:Path | Select-String "shims"

# 2. 检查符号链接权限
# 需要管理员权限或启用开发者模式（Windows 10+）
```

### 找不到命令？

```bash
# 查看所有 shims
oppm exe show

# 手动添加可执行文件
oppm exe add <path_to_exe>
```

## 🛣️ 路线图

### ✅ 已完成
- [x] 基础安装/卸载功能
- [x] Shim 管理（使用相对路径，支持迁移）
- [x] 元数据同步
- [x] 迁移功能
- [x] 打包和恢复功能（pack/rebuild）
- [x] 健康检查和自动修复策略

### 🚧 计划中
- [ ] 为 app meta 添加一个类别项（category），如果是字体，直接存放目录还是记录 URL 更好？
- [ ] GitHub Releases 集成（可能也包含从 URL 直接下载安装这个功能）
- [ ] 合理管理 Unicode 符号的使用

### ℹ️ 不确定
- [ ] 从 URL 直接下载安装
- [ ] 应用仓库系统（类似 Scoop buckets）
- [ ] 版本管理和升级功能
- [ ] 应用搜索和描述
- [ ] 依赖管理

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/ooooo-create/ppm.git
cd ppm

# 安装开发依赖
uv sync

# 配置 pre-commit
uv run pre-commit install

# 运行测试
uv run pytest -v

# 代码质量检查
uv run ruff check
```

## 📄 许可证

MIT License

## 🙏 致谢

灵感来源于：
- [Scoop](https://scoop.sh/)
