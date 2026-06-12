# 下载路由契约

本文件只定义下载策略层，不覆盖现有脚本实现细节。

## 目标

- 统一 Step 5 的入口判断
- 显式声明 fallback chain
- 输出下载 readiness，而不是只报告成功/失败

## 推荐 fallback chain

1. DOI 直连或出版商入口
2. 会话内页面抓取
3. CDP 浏览器辅助
4. 备用下载器/人工干预

## 输出字段

- requested_items
- downloaded_items
- unresolved_items
- session_status
- readiness
