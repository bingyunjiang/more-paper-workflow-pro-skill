# Publisher Download Access Matrix

如何从各出版商下载 PDF，按自动化可行性排序。

## 图例

| 图标 | 含义 |
|------|------|
| ✅ 已验证 | 批量运行成功，>90% 成功率 |
| ⚠️ 可行但有局限 | 会话过期快，成功率中等 |
| 🔴 被拦截 | 自动化下载不可行（Akamai/Cloudflare） |
| ❓ 未测试 | 未用本工具链测试过 |

## Sci-Hub（✅ CDP 可用）

**仅 2021 年以前论文有收录。** HTTP 直连全部被 Cloudflare 封锁，但 CDP Chrome 方式可用。

| 镜像站 | HTTP 直连 | CDP Chrome | 说明 |
|--------|-----------|------------|------|
| sci-hub.st | 🔴 拦截 | ✅ 可用 | 提取 `<object>.data` → Fetch 捕获，~6s/篇 |
| sci-hub.ru | 🔴 拦截 | ✅ 可用 | |
| sci-hub.shop | 🔴 拦截 | ✅ 可用 | |
| sci-hub.vg | 🔴 拦截 | ✅ 可用 | |
| sci-hub.in | 🔴 拦截 | ✅ 可用 | |
| sci-hub.al | 🔴 拦截 | ✅ 可用 | |
| sci-hub.box | 🔴 拦截 | ✅ 可用 | |
| sci-hub.red | 🔴 拦截 | ✅ 可用 | |
| sci-hub.ren | 🔴 拦截 | ✅ 可用 | |
| sci-hub.se | 🔴 拦截 | 🔴 不可用 | 跳转 Chrome 错误页 |
| sci-hub.wf | 🔴 拦截 | 🔴 不可用 | 跳转到首页 |
| sci-hub.ee | 🔴 拦截 | 🔴 不可用 | Cloudflare Turnstile |
| sci-hub.mk | 🔴 拦截 | 🔴 不可用 | 跳转到首页 |

**CDP 下载流程：**
1. 启动 Chrome（`--remote-debugging-port=9223`）about:blank
2. 运行 `download_via_scihub.py 检索文献表.md`
3. 脚本自动测试镜像站 → 取可用站 → 提取 `<object>.data` → 新标签页 Fetch 捕获

```bash
python3 scripts/download_via_scihub.py dois.txt --output paper-temp/
```

**实测性能：**
| 项目 | 数值 |
|------|------|
| 可用镜像站（CDP） | **9/13 个** |
| 下载速度 | ~6s/篇 |
| PDF 大小 | 3-4MB |
| 失败原因 | 论文不在 Sci-Hub 数据库（主要是 2021 年后论文） |

## 出版商矩阵

| 出版商 | DOI 前缀 | 访问方式 | 状态 | 策略 |
|--------|----------|----------|------|------|
| **Elsevier/SD** | `10.1016/` | CDP Chrome + Fetch | ✅ 已验证 | Layer 3: DOI→PII → 导航到 pdfft → 等待 PDF 重定向 → Fetch.reload → 原始字节 |
| **MDPI** | `10.3390/` | 手动浏览器 | 🔴 被拦截 | Akamai Bot Manager 在 CDN。**手动方案：** 打开文章页 → 点 Download PDF |
| **IEEE** | `10.1109/` | CDP Chrome | ❓ 未测试 | `ieeexplore.ieee.org` 可能需要机构认证，类似 SD 的 Cloudflare |
| **ASME** | `10.1115/` | CDP Chrome | ❓ 未测试 | `asmedigitalcollection.asme.org` 可能需要不同的 PDF URL 模式 |
| **IOP** | `10.1088/` | 直连 HTTP | ❓ 未测试 | `iopscience.iop.org` 部分开放获取 |
| **AIP** | `10.1063/` | 直连 HTTP | ❓ 未测试 | `pubs.aip.org` 可能支持 `?pdf=1` |
| **Wiley** | `10.1002/` | CDP Chrome | ❓ 未测试 | `onlinelibrary.wiley.com` 可能需要 CDP |
| **Springer** | `10.1007/` | 直连 HTTP | ❓ 未测试 | `link.springer.com` 部分开放获取 |
| **SSRN** | `10.2139/` | 直连 HTTP | ✅ 基本可行 | 预印本服务器，大多可直接下载 |
| **Frontiers** | `10.3389/` | 直连 HTTP | ✅ 基本可行 | 开放获取 |
| **ACS** | `10.1021/` | CDP Chrome | ❓ 未测试 | `pubs.acs.org` |

## 实测命中率

| 出版商 | 尝试数 | 成功 | 无 PDF | 成功率 |
|--------|--------|------|--------|--------|
| **Elsevier/SD** | 185 | 180 | 5 | **96%** |
| **MDPI** | 30 | 0（自动化） | 30 | **0%** |
| **Sci-Hub**（所有镜像） | 10+ | 0 | 全部 | **0%** |

## 决策树

```
论文 DOI
├── 10.1016/ → Elsevier/SD → CDP Layer 3+4（已验证）
├── 10.3390/ → MDPI        → 手动下载（Akamai）
├── 10.2139/ → SSRN        → 直连 HTTP 下载
├── 10.3389/ → Frontiers   → 直连 HTTP 下载
└── 其他                    → 先试直连 HTTP，不行上 CDP
```

## CDP 通用方案（适用于任一家出版商）

SD CDP 方法理论上适用于任何满足以下条件的出版商：
1. 通过浏览器可访问的 URL 提供 PDF
2. 使用 Cloudflare 或类似机制拦截 HTTP 库
3. 可通过机构认证访问

通用步骤：
1. 启动 Chrome + `--remote-debugging-port`
2. 登录出版商网站
3. 在文章页找到 PDF 链接（通过 JS 或 DOM）
4. 导航到 PDF URL + Fetch.enable + Page.reload
5. 通过 Fetch.getResponseBody 捕获

每家出版商可能需要不同的 PDF URL 模式——发现后记录于此。
