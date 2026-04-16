# 决策记录

## ADR-001: 研究方向调整 (2026-04)
**决策**: 从天气关联分析调整为空间统计 + MGWR + ML 分类
**背景**: 原计划分析天气与事故的关系，后调整为更有深度的空间分析
**结论**: 使用 Global/Local Moran's I + MGWR + Random Forest，在 MSOA 级别分析

## ADR-002: 数据年份 (2026-04)
**决策**: 2021-2024（4年）
**注意**: 2021 为疫情后首年恢复期，需在报告中注明
**敏感性分析**: 分别分析各年空间格局

## ADR-003: 分析单元 (2026-04)
**决策**: MSOA (Middle Layer Super Output Area)
**背景**: 约 6,791 个 England MSOAs，粒度适中

## ADR-004: 可视化工具 (2026-04)
**决策**: Matplotlib + Seaborn
**背景**: 课程推荐环境内的库，学术标准

## ADR-005: 回归变量 (2026-04)
**决策**: log_accident_rate ~ imd_score + junction_density + road_density + urban_pct + dark_pct + wet_road_pct
