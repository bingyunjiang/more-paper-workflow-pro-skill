# 朋友圈海报生成工作流

## 流程

1. 编写文案 → 用户确认后，设计 HTML 海报
2. 用 Chrome headless 截图 1080×1080px 正方形
3. 通过 MEDIA 路径展示给用户

## Chrome 截图命令

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --disable-gpu --no-sandbox \
  --screenshot=/path/to/output.png \
  --window-size=1080,1080 \
  file:///path/to/poster.html
```

## HTML 设计规范

| 项目 | 规格 |
|------|------|
| 尺寸 | 1080×1080px（朋友圈正方形） |
| 字体 | system-ui, PingFang SC |
| 色系 | 深色渐变背景 + 紫色/蓝色渐变强调 |
| 布局 | 顶部 badge → 标题 → 内容区块 → 底部 repo 链接 + 作者信息 |
| 关键数据 | 加粗放大展示（如 94.7%/94篇/10s） |

## 海报内容要素（按从上到下顺序）

### 1. 顶部 Badge
- `Academic Research Workflow · 8-Step Pipeline`
- 小字号，半透明，居中

### 2. 标题
- **More Paper Workflow Pro Skill** `v1.0.1`
- 副标题：完整学术文献检索和写作工作流

### 3. 核心亮点（3 列图标 + 数据）
| 图标 | 标签 | 数据 |
|------|------|------|
| 📥 | SD 下载成功率 | 94.7%（89/94 篇） |
| 🔌 | IEEE 两步走 | 5/5 论文 100% |
| 🌐 | 三源检索 | Semantic + Crossref + OpenAlex |

### 4. 下载源覆盖（横向 3 卡片）
| 来源 | 策略 | 标签 |
|------|------|------|
| **Sci-Hub** | CDP 真实浏览器 + 13 镜像自动检测 | 老论文免费 |
| **ScienceDirect** | IP/SSO 双重认证 + pdfft 直连 + JS 渲染回退 | 机构认证 |
| **IEEE Xplore** | 两步走：点击 PDF 按钮 → stamp 标签页 Fetch 捕获 | 机构认证 |

### 5. 版本亮点（列表）
- 🔧 **8 个新函数** — 浏览器检测 / SD 会话管理 / 登录引导 / Cloudflare 处理
- ⚡ **IEEE 两步走 v1.1** — 分层选择器 + 同页跳转 + stale tab 过滤
- ✍️ **Step 7 写作模式** — 4 种模式 + 双边摘要 + 同行评审质量门
- 📝 **Step 8 润色增强** — 句长波动检测 + 段落节奏优化

### 6. 底部
- GitHub: `bingyunjiang/More-paper-workflow-pro-skill`
- 小字：`pip install websocket-client && python3 scripts/auto_sd_downloader.py`

### 7. 作者信息
- **Dr. Jiang Bingyun（江博士）**
- WeChat: Bingyunjiang
- Email: bingyunjiang@qq.com

## 文案风格

- 简洁，每行 ≤25 字
- 要点用列表 / 表格呈现
- 关键数据突出（加数字、百分比）
- 末尾附 GitHub 链接 + 作者联系方式
