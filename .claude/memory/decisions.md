# 架构决策记录

<!-- 由 /wrap-up 命令追加新条目 -->

## ADR-001: 待定 — 数据分析工具选型
**状态**: 待决策
**选项**:
- Pandas + Matplotlib/Seaborn: 经典学术组合，论文友好
- Pandas + Plotly: 交互式图表，适合探索
- 建议: 先用 Pandas + Seaborn 做分析和论文图表，Plotly 做探索

## ADR-002: 待定 — 天气数据来源
**选项**:
- Open-Meteo: 免费，历史数据全，API 简单
- Met Office: 官方权威但需申请 key
- Meteostat: Python 库直接用，数据来自多源
