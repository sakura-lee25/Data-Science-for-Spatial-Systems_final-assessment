---
description: 收工保存记忆！每次结束工作时运行。
allowedTools: ["Read", "Write", "Edit", "Bash"]
---

本次工作即将结束，执行记忆保存：

## 1. 更新 CLAUDE.md 动态区
编辑 CLAUDE.md 中 `<!-- ===== 以下动态区` 之后的内容：
- "最后更新" → 今天日期
- "当前分支" → !`git branch --show-current`
- "当前任务" → 基于本次会话判断下一步
- "最近完成" → 追加今天完成的事项

## 2. 更新 .claude/memory/progress.md
- 勾选已完成任务 `[ ]` → `[x]`
- 追加新发现的待办

## 3. 如有技术决策
追加到 `.claude/memory/decisions.md`

## 4. 如有踩坑
追加到 `.claude/memory/lessons.md`

## 5. 提交记忆
!`git add CLAUDE.md .claude/memory/ 2>/dev/null`
告诉我更新了什么，问我是否提交。
