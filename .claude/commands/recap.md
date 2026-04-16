---
description: 回顾项目状态，快速恢复上下文。每次开始工作时运行。
allowedTools: ["Read", "Bash", "Glob", "Grep"]
---

帮我快速回顾 CASA0006 课程作业项目的当前状态：

## 项目记忆
!`cat CLAUDE.md`

## 详细进度
!`cat .claude/memory/progress.md`

## 最近踩坑
!`tail -20 .claude/memory/lessons.md`

## Git 活动
!`git log --oneline -10`
!`git status --short`

## 数据文件状态
!`ls data/raw/`
!`ls data/processed/`

给我一份简洁摘要（不超过 15 行）：
1. 当前在哪个 Phase，整体进度
2. 上次做到哪了
3. 数据状态
4. 今天建议从哪里继续

同时读取 .claude/plans/ 目录下的计划文件，告诉我实施计划的概要。
