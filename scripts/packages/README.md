# Zotero MCP Server 离线依赖缓存

本目录当前缓存的是 `zotero-mcp-server` **v0.5.0** 及其对应依赖 wheel，用于 Step 6 的离线/半离线安装。

## 📦 当前缓存内容

- **104 个文件**，共约 **74 MB**
- **86 个** `py3-none-any.whl` — 纯 Python 包
- **16 个** 平台相关 wheel（如 `cp314-macosx_*`、`py3-none-macosx_*`）
- **2 个** `.tar.gz` — 源码包（`bibtexparser`, `sgmllib3k`）

## ✅ 平台兼容性

当前缓存**不再是全纯 Python**。其中包含一批平台相关 wheel，因此兼容性应按“缓存内容 + 目标机器”共同判断：

| 平台 | 兼容性 |
|------|--------|
| macOS ARM64 (Apple Silicon) | ✅ 当前缓存已验证覆盖 |
| macOS x86_64 (Intel) | ⚠ 纯 Python 依赖可复用，平台相关 wheel 可能需重下 |
| Linux x86_64 / ARM64 | ⚠ 纯 Python 依赖可复用，平台相关 wheel 需按目标平台补齐 |
| Windows x86_64 / ARM64 | ⚠ 纯 Python 依赖可复用，平台相关 wheel 需按目标平台补齐 |

## 🔧 使用方式

`setup_zotero.py --install` 自动使用本目录：

```bash
# 优先使用本地 wheel（离线），缺失的平台依赖自动从 PyPI 补全
python3 scripts/setup_zotero.py --install
```

安装逻辑：
1. `pip install zotero-mcp-server --find-links scripts/packages/` — pip 优先用本地 `.whl`
2. 若本地缺失某些平台依赖或匹配版本，pip 自动从 PyPI 下载
3. 若上述均失败，尝试直接安装本地 `zotero_mcp_server-*.whl`
4. 最终回退：`pip install zotero-mcp-server`（全量从 PyPI 下载）

## ⚠️ 注意事项

- **本目录由原作者维护**，升级 `zotero-mcp-server` 版本时需同步更新 wheel
- **断网环境**：仅当目标平台与当前缓存覆盖的平台兼容时，才可完全离线安装
- **锁定清单**：`manifest.lock.json` 记录当前缓存的文件名、大小、SHA-256 和平台标签；更新缓存后运行 `python3 scripts/check_offline_packages.py --write-manifest`
- **重复版本治理**：`python3 scripts/check_offline_packages.py` 默认只提示重复版本；准备拆分平台 bundle 或瘦身时再使用 `--strict`
- **更新依赖**：
  ```bash
  rm -f scripts/packages/zotero_mcp_server-*.whl
  pip download zotero-mcp-server==0.5.0 --dest scripts/packages/
  ```

## 🔄 版本同步建议

- 更新本目录中的 `zotero_mcp_server-*.whl` 与关键平台相关依赖
- 重新执行 `python3 scripts/setup_zotero.py --smoke-test`
- 确认 `pip show zotero-mcp-server` 输出版本与离线 wheel 版本一致

## 📄 许可证

本目录中的软件包遵循各自的原始许可证。上游项目：
- [zotero-mcp-server](https://github.com/54yyyu/zotero-mcp) (MIT)
- [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) (MIT)
