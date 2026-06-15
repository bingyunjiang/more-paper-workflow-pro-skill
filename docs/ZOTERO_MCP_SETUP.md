# Zotero MCP 配置指南

本文档详细说明如何在不同平台和 Agent 环境中配置 Zotero MCP 服务器。

> 当前推荐上游版本：`zotero-mcp-server 0.5.0`。
> 当前 skill 自带的 `scripts/packages/` 已同步到 `0.5.0`，但它不再是“全纯 Python、全平台同一份缓存”；目录中包含平台相关 wheel，跨平台搬运时需要按目标平台补齐。

---

## 目录

1. [前置条件](#前置条件)
2. [快速开始](#快速开始)
3. [连接模式选择](#连接模式选择)
4. [Claude Code 配置](#claude-code-配置)
5. [Hermes/OpenClaw 配置](#hermesopenclaw-配置)
6. [Claude Desktop 配置](#claude-desktop-配置)
7. [Cursor 配置](#cursor-配置)
8. [跨平台注意事项](#跨平台注意事项)
9. [验证与故障排除](#验证与故障排除)

---

## 前置条件

| 需求 | 说明 |
|------|------|
| **Python 3.9+** | 推荐 3.11+ |
| **pip** | Python 包管理器 |
| **zotero-mcp-server** | 推荐 `0.5.0` |
| **Zotero 账号**（Web API 模式） | 需 API Key |
| **Zotero 桌面端**（本地模式） | v6.0+，需保持运行 |

---

## 快速开始

```bash
# 1. 一键检测当前环境
python3 scripts/setup_zotero.py

# 2. 自动检测目标环境并安装
python3 scripts/setup_zotero.py --install --target auto

# 3. 或显式指定目标环境
python3 scripts/setup_zotero.py --install --target claude-code

# 4. 验证安装
python3 scripts/setup_zotero.py --smoke-test
```

---

## 连接模式选择

Zotero MCP 支持两种连接模式：

| 特性 | Web API 模式 | 本地 API 模式 |
|------|------------|-------------|
| **连接方式** | `api.zotero.org` | `localhost:23119` |
| **需要 API Key** | ✅ 是 | ❌ 否 |
| **需要桌面端运行** | ❌ 否 | ✅ 是 |
| **读操作** | ✅ | ✅ |
| **写操作**（创建集合/导入/移动） | ✅ | ❌ 只读 |
| **适用场景** | 需要管理文库 | 仅需读文献写论文 |

### Web API 模式配置

1. 打开 https://www.zotero.org/settings/keys
2. 点击 "Create new private key"
3. 勾选以下权限：
   - ✅ Allow library access
   - ✅ Allow notes access
   - ✅ Allow write access
4. 复制生成的 API Key
5. 在 zotero.org/settings/keys 页面的 URL 中找到你的 User ID（数字）
6. 运行配置脚本时选择 Web API 模式并输入 Key 和 ID

### 本地 API 模式配置

1. 确保 Zotero 桌面端正在运行
2. 运行配置脚本时选择本地 API 模式
3. 无需 API Key

---

## Claude Code 配置

Claude Code 使用 `~/.claude/mcp.json` 配置文件。

### 方式一：自动配置（推荐）

```bash
python3 scripts/setup_zotero.py --install --target claude-code
```

脚本会自动：
1. 安装 `zotero-mcp-server` Python 包
2. 写入 `~/.claude/mcp.json`（保留已有其他 MCP 服务器配置）
3. 提示重启 Claude Code

### 方式二：非交互式配置（CI/CD 或脚本化）

```bash
# Web API 模式
ZOTERO_API_KEY="your_key_here" \
ZOTERO_USER_ID="1234567" \
python3 scripts/setup_zotero.py --install --target claude-code --non-interactive

# 本地 API 模式
ZOTERO_LOCAL=true \
python3 scripts/setup_zotero.py --install --target claude-code --non-interactive
```

### 方式三：手动配置

创建或编辑 `~/.claude/mcp.json`：

```json
{
  "mcpServers": {
    "zotero": {
      "command": "/path/to/zotero-mcp",
      "env": {
        "ZOTERO_API_KEY": "your_api_key_here",
        "ZOTERO_LIBRARY_ID": "1234567"
      }
    }
  }
}
```

执行 `python3 scripts/setup_zotero.py --check` 获取 `zotero-mcp` 的路径。

### 验证

重启 Claude Code 后，在对话中检查是否出现以下工具：
- `zotero_search`
- `zotero_add_by_doi`
- `zotero_get_item_fulltext`
- `zotero_create_collection`
- `zotero_manage_collections`

---

## Hermes/OpenClaw 配置

Hermes/OpenClaw 使用 `~/.hermes/config.yaml` 配置文件。

```bash
python3 scripts/setup_zotero.py --install --target hermes
```

配置格式：

```yaml
mcp_servers:
  zotero:
    command: /path/to/zotero-mcp
    env:
      ZOTERO_API_KEY: "your_key"
      ZOTERO_LIBRARY_ID: "1234567"
    enabled: true
```

验证：

```bash
hermes mcp list
```

---

## Claude Desktop 配置

Claude Desktop 使用 `claude_desktop_config.json`（路径因平台而异）。

```bash
python3 scripts/setup_zotero.py --install --target claude-desktop
```

此模式优先通过 `zotero-mcp setup` 命令调用上游工具完成配置；若失败，`setup_zotero.py` 会回退为直接写入 Claude Desktop 的配置文件。

配置路径：

| 平台 | 路径 |
|------|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `~/AppData/Roaming/Claude/claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

---

## Cursor 配置

Cursor 使用 `~/.cursor/mcp.json` 配置文件，格式与 Claude Code 相同。

```bash
python3 scripts/setup_zotero.py --install --target cursor
```

---

## 跨平台注意事项

### macOS

- **ARM64 (Apple Silicon)**：`scripts/packages/` 本地 wheel 直接可用
- **x86_64 (Intel)**：本地 wheel 同样适用（纯 Python 包），或从 PyPI 自动下载
- Zotero 桌面端路径：`/Applications/Zotero.app`
- 本地 API 端口：`http://127.0.0.1:23119`

### Linux

- 本地 wheel 均为纯 Python，直接可用
- `zotero-mcp` 可执行文件通常位于 Python 的 `bin/` 目录
- Zotero 桌面端需通过 Flatpak/Snap/AppImage 安装

### Windows

- 本地 wheel 均为纯 Python，直接可用
- `zotero-mcp` 可执行文件位于 Python `Scripts\` 目录（`zotero-mcp.exe`）
- `get_zotero_bin()` 自动处理 `.exe` 后缀
- Zotero 桌面端路径：`C:\Program Files\Zotero\zotero.exe`
- 配置路径使用正斜杠 `/`（JSON 格式要求）

### 离线安装

`scripts/packages/` 目录可缓存全部依赖的 wheel 文件（当前约 74 MB），支持同平台离线安装或半离线安装。
当前这份缓存已同步到 `0.5.0`，但目录中同时包含纯 Python wheel 与平台相关 wheel。

因此：

- **当前机器同平台**：通常可直接离线安装
- **跨平台迁移**：纯 Python wheel 可复用，但平台相关 wheel 需要按目标平台重新下载

如果需要在目标平台重新下载平台特定的依赖：

```bash
pip download zotero-mcp-server==0.5.0 --dest scripts/packages/
```

---

## 验证与故障排除

### 环境检测

```bash
# 人类可读的状态报告
python3 scripts/setup_zotero.py

# JSON 格式（供脚本调用）
python3 scripts/setup_zotero.py --check

# 烟雾测试
python3 scripts/setup_zotero.py --smoke-test
```

### 常见问题

#### Q: `zotero-mcp` 命令找不到

```bash
# 查看安装路径
python3 scripts/setup_zotero.py --check | grep binary

# 或直接 Python 调用
python3 -m zotero_mcp_server
```

#### Q: Claude Code 中看不到 `zotero_*` 工具

1. 确认 `~/.claude/mcp.json` 存在且包含 `zotero` 条目
2. 确认 `command` 路径正确（执行 `which zotero-mcp` 验证）
3. **完全退出并重启** Claude Code（不是重新加载窗口）
4. 检查 Claude Code 日志中的 MCP 连接错误

#### Q: 升级到 0.5.0 后，为什么安装出来还是旧版本

最常见原因是 `scripts/packages/` 里仍缓存着旧版主 wheel，`setup_zotero.py --install` 会优先使用本地缓存。

处理方式：

```bash
rm -f scripts/packages/zotero_mcp_server-*.whl
pip download zotero-mcp-server==0.5.0 --dest scripts/packages/
python3 scripts/setup_zotero.py --install
python3 scripts/setup_zotero.py --smoke-test
```

#### Q: 本地 API 模式无法连接

1. 确认 Zotero 桌面端正在运行
2. 检查端口是否监听：`curl http://127.0.0.1:23119/api/users/1/items?limit=1`
3. 确认 `ZOTERO_LOCAL=true` 已设置

#### Q: Web API 模式提示权限错误

1. 确认 API Key 有写权限（在 zotero.org/settings/keys 检查）
2. 确认 Library ID 正确（数字，非用户名）
3. 如果 Key 失效，重新生成

#### Q: 离线安装失败

`scripts/packages/` 中的 wheel 均为纯 Python 包（`py3-none-any`），理论上跨平台通用。如果安装失败：

从 `0.5.0` 开始，这个前提不再总成立：缓存中可能含有平台相关 wheel。若目标机器与缓存平台不一致，请在目标平台重新执行：

```bash
pip download zotero-mcp-server==0.5.0 --dest scripts/packages/
```

---

## 参考资源

- [zotero-mcp-server 上游项目](https://github.com/54yyyu/zotero-mcp)
- [MCP 协议文档](https://modelcontextprotocol.io)
- [Claude Code MCP 集成文档](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [Zotero Web API 文档](https://www.zotero.org/support/dev/web_api/v3/start)
