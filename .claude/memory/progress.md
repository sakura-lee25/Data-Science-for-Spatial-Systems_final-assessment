# 进度追踪 — CASA0006 UK Road Traffic Accident Analysis

## Phase 0: 项目搭建 ✅
- [x] 项目初始化、目录结构
- [x] 研究方向确定：空间统计 + MGWR + ML分类
- [x] 实施计划编写 (保存在 .claude/plans/)
- [ ] 安装全部 Python 依赖
- [ ] 更新 CLAUDE.md 为最新课程要求

## Phase 1: 数据采集
- [ ] 下载 STATS19 碰撞数据 (2021-2024)
- [ ] 下载 MSOA 2021 边界 GeoJSON (ONS)
- [ ] 下载 IMD 2019 数据
- [ ] 下载人口估计数据 (ONS mid-year)
- [ ] 编写下载脚本 src/scraper/

## Phase 2: 数据处理与特征工程
- [ ] STATS19 数据清洗
- [ ] 事故点→MSOA 空间联结
- [ ] IMD LSOA→MSOA 聚合
- [ ] 计算 accident_rate_per_10k
- [ ] 合并所有特征为 GeoDataFrame
- [ ] 生成各年单独数据 (敏感性分析用)

## Phase 3: 空间自相关分析
- [ ] Queen 邻接空间权重矩阵
- [ ] Global Moran's I
- [ ] Local Moran's I (LISA)
- [ ] Moran 散点图 + LISA 聚类地图
- [ ] 各年 LISA 对比 (敏感性分析)

## Phase 4: MGWR 分析
- [ ] VIF 多重共线性检查
- [ ] OLS 基线回归
- [ ] MGWR 拟合
- [ ] 局部系数空间分布图

## Phase 5: 机器学习分类
- [ ] 定义高风险标签 (top 20%)
- [ ] 空间感知 train/test split
- [ ] Random Forest + SMOTE
- [ ] PR 曲线、混淆矩阵、特征重要性

## Phase 6: Notebook 整合与报告
- [ ] 整合为单一 Jupyter Notebook
- [ ] Introduction + 文献引用
- [ ] Discussion & Conclusion
- [ ] 检查字数 ≤ 1500 词
- [ ] Restart & Rerun All
- [ ] 导出 PDF
- [ ] 数据上传 GitHub
- [ ] 提交
