# `more-paper-workflow` 更名迁移指南

## 适用范围

自 `v1.0.22-20260724` 起，Skill、GitHub 仓库和插件的主名称由
`more-paper-workflow-pro-skill` 统一缩短为 `more-paper-workflow`。同一
`v1.0.22-20260724` 版本内，Codex 插件也收口为以仓库根目录为插件根的
自包含结构。

## 兼容性

- 旧名称 `more-paper-workflow-pro-skill` 和 `more paper workflow pro skill`
  继续作为触发兼容别名。
- 研究项目、PDF、BibTeX、Zotero 映射和 `.skill-state` 工件不需要迁移。
- 新安装、更新检查、仓库 URL、插件 ID、目录名和缓存键一律使用
  `more-paper-workflow`。

## 升级现有检出

在现有 Git 检出中执行仓库自带升级入口：

```bash
python3 scripts/perform_skill_upgrade.py --json
```

也可以在确认工作区没有未提交冲突后执行：

```bash
git pull --ff-only
```

升级后用以下命令确认三个版本面一致：

```bash
python3 scripts/check_skill_update.py --json --force --no-network
```

## 清理旧安装副本

1. 先确认新仓库或新插件已经能够识别 `more-paper-workflow`。
2. 如果宿主仍展示旧插件 ID，移除旧插件副本后刷新插件目录。
3. 不要删除研究项目中的 `.skill-state`、PDF 池或 Zotero 数据。
4. 不要把旧插件目录改名后与新目录并存，否则宿主可能重复发现同一 Skill。

## 处理旧缓存

- 当前更新检查缓存位于
  `${XDG_CACHE_HOME:-~/.cache}/more-paper-workflow/update-check.json`。
- 如果旧环境仍有
  `${XDG_CACHE_HOME:-~/.cache}/more-paper-workflow-pro-skill/`，先确认新插件
  可以正常触发，再归档或删除该旧目录；它只属于旧版更新检查，不是研究数据。
- 不要清理项目目录中的 `.skill-state`、下载清单、PDF 或 Zotero 工件。

## 验收

- 新名称可以触发 Step 1、5、7、8。
- 旧名称仍能触发同一个 Skill，但输出和工件只使用新名称。
- 插件包内可以读取根 `SKILL.md`、`agents/`、`references/` 和 `scripts/`，
  不依赖插件根之外的文件。
