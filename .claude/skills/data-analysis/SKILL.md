---
name: data-analysis
description: 数据分析最佳实践。当进行数据清洗、统计分析、回归建模、假设检验时自动使用。
---

## 数据分析规范

### 数据加载
- 大文件 (>50MB) 用 `pd.read_csv(chunksize=10000)`
- 指定 dtype 避免自动推断错误
- 加载后立即检查 `.shape`, `.dtypes`, `.isnull().sum()`

### 数据清洗
- 记录每步清洗操作和丢弃的数据量
- 缺失值处理要说明理由（删除/插值/填充）
- 异常值用 IQR 或 z-score 检测，不要无理由删除

### 统计分析
- 先检查假设条件（正态性、方差齐性）
- 非正态数据用非参数检验
- 报告: 统计量、自由度、p 值、效应量、置信区间
- 多重比较用 Bonferroni 或 FDR 校正

### 可视化
- 探索阶段: Plotly (交互)
- 论文图表: Matplotlib + Seaborn (静态, 高质量)
- 地理数据: Folium (交互地图) 或 GeoPandas.plot()

### 代码组织
- 每个分析步骤是独立函数
- 函数签名: `def analyze_xxx(df: pd.DataFrame) -> dict:`
- 结果保存为 JSON/CSV 到 data/processed/
- 图表保存到 reports/figures/
