# CASA0006 Coursework — UK Road Traffic Accident Spatial Analysis

## 课程作业要求（不可违反）
- **交付物**: 1 个 Jupyter Notebook (.ipynb) + 1 个 PDF (从 notebook 导出)
- **字数限制**: 最多 1500 词（不含 Python 代码和注释）
- **截止日期**: 2025 年 4 月 21 日，周一，英国时间下午 5 点
- **数据集**: UK Road Safety Data (STATS19) + 增强数据
- **方法数量**: 最多 4 个，必须与研究问题直接相关
- **数据托管**: 数据放 GitHub repo，notebook 中用 read_csv 远程读取
- **运行环境**: 仅用推荐环境中的库，若用其他库须注明名称和版本号
- **提交前**: 必须 Restart & Rerun All 确保代码可执行

## 评分标准
| 项目 | 权重 |
|------|------|
| 研究背景与问题 | 15% |
| 数据收集处理 | 15% |
| **分析正确性/深度** | **35%** |
| 可视化 | 10% |
| 写作质量 | 15% |
| 创造性 | 10% |

## ⚠️ 必须避免的扣分项
1. 不要把 ID 列纳入分析
2. 不要把分类变量当数值变量处理
3. 不要对单变量做聚类
4. 不要对 2 个变量做 PCA 然后用 2 个主成分
5. 代码结果和文字讨论必须一致
6. 代码必须能运行且无报错
7. 方法不超过 5 个，且必须相关
8. 用"率 (rate)"而非"数量 (count)"
9. 引用必须真实可查，LLM 编造引用会被处罚

## 研究方向
**空间统计 + MGWR + 机器学习分类**，在 MSOA 级别分析英国道路交通事故的空间分布规律及影响因素。

## 核心方法 (3 个)
1. **空间自相关** — Global/Local Moran's I (libpysal, esda)
2. **MGWR** — 多尺度地理加权回归 (mgwr)
3. **Random Forest 分类** — 高风险区域识别 + SMOTE 处理不平衡 (scikit-learn, imbalanced-learn)

## 数据 (2021-2024, MSOA 级别)
| 数据 | 来源 |
|------|------|
| STATS19 碰撞数据 | data.gov.uk |
| MSOA 2021 边界 | ONS Open Geography Portal |
| IMD 2019 | MHCLG |
| 人口估计 | ONS mid-year estimates |

**关键变量**: accident_rate_per_10k, imd_score, junction_density, road_density, urban_pct, dark_pct, wet_road_pct

**注意**: 2021 为疫情后恢复期，需在报告中注明。敏感性分析需分别分析各年。

## 详细实施计划
见 @.claude/plans/glistening-petting-sutherland.md

## 技术栈
- Python 3.x, Pandas, NumPy, GeoPandas
- libpysal, esda (空间自相关)
- mgwr (MGWR)
- scikit-learn, imbalanced-learn (ML)
- Matplotlib, Seaborn (可视化)

## 核心命令
- `source .venv/bin/activate` — 激活虚拟环境
- `pip install -r requirements.txt` — 安装依赖
- `jupyter notebook` — 启动 Jupyter
- `python -m src.scraper.main` — 运行数据采集

---
<!-- ===== 以下动态区由 /wrap-up 命令维护 ===== -->

## 当前状态
最后更新: 2026-04-13
当前分支: main
当前任务: 补充配置文件 → 安装依赖 → 开始 Phase 1 数据采集
阻塞问题: 无

## 最近完成
- [2026-04-13] Claude Code 记忆系统配置修复
- [2026-04-06] 项目初始化
- [2026-04] 研究大纲和实施计划编写

## 关键决策
- 研究方向: 空间统计 + MGWR + ML（非简单天气分析）
- 数据年份: 2021-2024
- 分析单元: MSOA
- 回归变量: log_accident_rate ~ imd_score + junction_density + road_density + urban_pct + dark_pct + wet_road_pct
- 详情见 @.claude/memory/decisions.md

## 已知问题
- [ ] 依赖尚未安装
- [ ] MGWR 计算需 2-4 小时，需缓存结果
