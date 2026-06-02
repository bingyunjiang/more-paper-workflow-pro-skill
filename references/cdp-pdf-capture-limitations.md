# CDP PDF 捕获：使用 cdp_utils 共享模块

## 核心原则

**SD 论文下载必须使用 `cdp_utils.capture_pdf_via_fetch()`，不要写临时 Fetch 脚本。**

## 为什么不能写临时 Fetch 脚本

CDP 的 Fetch 拦截涉及精确的 WebSocket 事件时序：
1. `Page.enable`、`Fetch.enable`、`Page.reload` 必须按序发送
2. 发送后不能等待响应（`json.loads(pws.recv())`），因为等待会吃掉 `Fetch.requestPaused` 事件
3. 必须立即进入事件循环，从 WebSocket 直接读取所有消息
4. `Fetch.getResponseBody` 的响应需要做 `id` 匹配，因为事件循环中混杂了协议事件

这些细节 `cdp_utils.py` 中的 `capture_pdf_via_fetch()` 已全部处理妥当。

## 正确用法

```python
import sys
sys.path.insert(0, "More-Paper-Workflow-Pro-Skill/scripts")
from cdp_utils import (create_tab, wait_for_tab_url, get_tab_ws_url,
                        capture_pdf_via_fetch, close_all_tabs)

wu, tid = create_tab(port, pdfft_url)
pdf_tab = wait_for_tab_url(port, SD_PDF_HOST, timeout=15)
tab_ws_url = get_tab_ws_url(port, pdf_tab["id"])
pdf_data = capture_pdf_via_fetch(port, tab_ws_url, "*main.pdf*")
close_all_tabs(port)
```

## 错误用法（会失败）

```python
# 自行实现 Fetch 逻辑会踩所有坑
pws = websocket.create_connection(tab_ws_url)
pws.send(json.dumps({"id":10,"method":"Page.enable"}))
json.loads(pws.recv())  # 吃掉 Fetch 事件
pws.send(json.dumps({"id":11,"method":"Fetch.enable",...}))
json.loads(pws.recv())  # 又吃掉 Fetch 事件
pws.send(json.dumps({"id":12,"method":"Page.reload"}))
# 后面的事件循环永远收不到 Fetch.requestPaused
```

## 下载失败诊断流程

| 现象 | 原因 | 处理 |
|------|------|------|
| `NO DATA`（PDF 标签页找到了但无数据） | Fetch 事件被中间 recv() 吃掉 | 改用 `capture_pdf_via_fetch()` |
| `no PDF redirect`（无重定向） | 期刊无访问权限 | 手动在 Chrome 中打开文章页检查 |
| 页面停留在 pdfft URL | Cloudflare 重新挑战 | 等待 60s 或手动过验证 |
| 浏览器能打开文章页但 PDF 按钮不可用 | 无机构会话 Cookie | 检查 `Network.getCookies` → 若为 0 → 需登录 |
| 所有出版商均返回 403/超时 | CDP 实例为全新无 Cookie 浏览器 | 在 Chrome 窗口中手动登录机构账号（Shibboleth / SSO / CARSI） |

## CDP Cookie 诊断（通用检查）

```python
import json, urllib.request, websocket
wu = json.loads(urllib.request.urlopen(
    "http://127.0.0.1:9223/json/version").read())["webSocketDebuggerUrl"]
ws = websocket.create_connection(wu, timeout=10)
ws.send(json.dumps({"id": 1, "method": "Network.getCookies"}))
while True:
    msg = json.loads(ws.recv())
    if msg.get("id") == 1:
        cookies = msg["result"]["cookies"]
        pubs = ["ieee","wiley","aip","asme","springer","nature","sciencedirect","elsevier"]
        pc = sum(1 for c in cookies if any(p in c.get("domain","") for p in pubs))
        print(f"出版商Cookie: {pc}/{len(cookies)}")
        break
```
结果 0/0 说明 CDP 浏览器为全新实例，必须先手动登录。
