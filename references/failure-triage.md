# Failure Triage

> 跨步骤通用的故障分流协议。核心原则：**禁止直接跳到补救动作，先判定失败发生在哪一层。**

---

## 1. 通用输出格式

当 Step 4-7 出现关键失败时，优先输出以下 4 行结构，而不是先给建议：

```md
Observed Symptom:
- 观察到的失败现象

Likely Layer:
- 最可能出问题的层：关键词 / 数据源 / 元数据 / 登录权限 / 映射规则 / 证据基础 / 体裁蓝图

Required Evidence:
- 还需要看到什么，才能确认根因

Next Action:
- 在当前层先做的最小动作
```

---

## 2. 常见失败层

| 层 | 典型问题 |
|----|----------|
| 检索词层 | 关键词过窄、过宽、概念混淆、排除词错误 |
| 数据源层 | 选错数据库、库源覆盖不足、API 返回异常 |
| 元数据层 | DOI 无效、标题冲突、article_url 缺失、中文 source_id 不完整 |
| 登录权限层 | 机构权限不足、CDP 会话过期、cookie 缺失 |
| 映射层 | 集合归属错误、条目匹配错误、附件路径对不上 |
| 证据层 | 只有摘要、没有 PDF、证据不能支撑 claim |
| 蓝图层 | 章节目标不清、体裁风格不明确、论证计划不足 |

---

## 3. 四类优先故障协议

### A. 检索故障

**Observed Symptom**
- 检索结果过少 / 过多 / 明显跑偏

**Likely Layer**
- 检索词层
- 数据源层
- 筛选阈值层

**Required Evidence**
- 当前关键词组
- 当前数据库和时间窗口
- 前 10-20 条代表性结果的偏差类型

**Next Action**
- 先判断是“词不对”还是“库不对”，再决定扩词、换库或调阈值

### B. 下载故障

**Observed Symptom**
- 条目无法下载 / 会话失败 / 标题无法落到 PDF

**Likely Layer**
- 元数据层
- 登录权限层
- 出版社策略层

**Required Evidence**
- DOI / article_url / source_id 是否可用
- 当前 access route
- 下载日志中的明确失败原因

**Next Action**
- 先区分“元数据不足”与“权限不足”，不要一律归因为网络或反爬

### C. Zotero 故障

**Observed Symptom**
- 条目导入错位 / 集合层级不一致 / PDF 无法关联

**Likely Layer**
- 映射层
- 附件路径层
- Zotero 写入层

**Required Evidence**
- `文献-Zotero架构对照.json`
- `pdf-附件池索引.json`
- 当前 collection path / item key / pdf_path

**Next Action**
- 先确认是“映射错”还是“附件缺”，再决定重算对照还是补附件

### D. 写作故障

**Observed Symptom**
- 章节难以下笔 / 引用支撑弱 / 文字能写但证据不足

**Likely Layer**
- 证据层
- 蓝图层
- 范围控制层

**Required Evidence**
- 当前章节目标
- 当前可用文献和证据等级
- `section_blueprints` / `argument_plan`

**Next Action**
- 先区分“文献不足”还是“论证计划不足”，不要直接让模型硬写

---

## 4. 何时必须触发 Failure Triage

以下情况必须先走 triage，再给补救建议：
- 用户说“结果不对”“下载不了”“对不上”“写不出来”
- 当前失败会影响下游 Step 的输入质量
- 当前失败会改变 `WARN / REJECT / 待人工` 的状态判断

以下情况可以直接给建议：
- 纯格式性小问题
- 已经明确根因且不会影响下游契约的小修正
