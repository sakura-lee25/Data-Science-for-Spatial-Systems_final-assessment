---
description: 回顾项目状态，快速恢复上下文。每次开始工作时运行。
allowedTools: ["Read", "Bash", "Glob", "Grep"]
---

帮我快速回顾 UK 交通事故分析项目的当前状态：

## 项目记忆
!`cat CLAUDE.md 2>/dev/null`

## 详细进度
!`cat .claude/memory/progress.md 2>/dev/null`

## 最近踩坑
!`tail -30 .claude/memory/lessons.md 2>/dev/null`

## Git 活动
!`git log --oneline -10 2>/dev/null`
!`git status --short 2>/dev/null`

## 数据文件状态
!`ls -lh data/raw/ 2>/dev/null`
!`ls -lh data/processed/ 2>/dev/null`

## 虚拟环境
!`echo "VIRTUAL_ENV=$VIRTUAL_ENV"`

给我一份简洁摘要（不超过 15 行）：
1. 当前在哪个 Phase，整体进度
2. 上次做到哪了
3. 数据状态（有什么数据，缺什么数据）
4. 虚拟环境是否激活（如果 VIRTUAL_ENV 为空，提醒我运行 source .venv/bin/activate）
5. 今天建议从哪里继续
