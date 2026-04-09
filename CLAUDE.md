# UK Road Traffic Accident Analysis — 英国道路交通事故与地点/天气关系研究

## 项目概述
分析英国道路交通事故率如何随地点（地区、道路类型、城乡）和天气条件（降雨、能见度、温度、路面状况）而变化。最终交付以python代码及提供上下文解释（格式如下：引言，研究问题，数据，方法论，结果和讨论，结论以及参考文献）的报告。

## 技术栈
- 语言: Python 3.11+
- 数据处理: Pandas, NumPy, GeoPandas
- 数据采集: Requests, BeautifulSoup, Selenium (如需)
- 天气数据: Meteostat / Open-Meteo API
- 可视化: Matplotlib, Seaborn, Plotly, Folium (地图)
- 统计分析: SciPy, Statsmodels, Scikit-learn
- 笔记本: Jupyter Notebook
- 测试: Pytest

## 核心命令
- `source .venv/bin/activate` — 激活虚拟环境
- `pip install -r requirements.txt` — 安装依赖
- `jupyter notebook` — 启动 Jupyter
- `pytest` — 运行测试
- `python -m src.scraper.main` — 运行数据采集
- `python -m src.analysis.main` — 运行分析流水线

## 目录结构
- `data/raw/` — 原始数据（不提交 git）
- `data/processed/` — 清洗后的数据
- `notebooks/` — 探索性分析 Jupyter notebooks
- `src/scraper/` — 数据采集脚本
- `src/analysis/` — 统计分析模块
- `src/visualization/` — 图表生成
- `src/utils/` — 工具函数（日志、配置、数据加载）
- `reports/` — 最终报告、图表、表格
- `tests/` — 测试文件

## 数据来源
- **事故数据**: UK Department for Transport — STATS19 数据集
  - 下载: https://www.data.gov.uk/dataset/road-accidents-safety-data
  - 包含: 事故严重程度、地点坐标、日期时间、道路类型、光照条件、天气条件
- **天气数据**: Open-Meteo Historical Weather API (免费)
  - https://open-meteo.com/en/docs/historical-weather-api
  - 包含: 温度、降水、风速、能见度
- **地理数据**: UK 行政区划 GeoJSON
  - ONS Geography Portal

## 研究方法
1. **数据采集**: 从 data.gov.uk 获取 STATS19 事故数据 + Open-Meteo 获取对应天气
2. **数据清洗**: 处理缺失值、统一坐标系、时间对齐
3. **探索性分析 (EDA)**: 描述性统计、分布可视化
4. **地理分析**: 事故热力图、区域对比
5. **天气关联分析**: 天气条件与事故率的统计检验
6. **建模**: 回归分析 / 分类模型预测事故风险
7. **报告撰写**: 学术论文格式

## 编码规范
- 函数和变量: snake_case
- 类名: PascalCase
- 文档字符串: Google 风格 docstring
- 类型标注: 所有公开函数必须有 type hints
- 数据路径: 用 pathlib.Path，不硬编码
- 配置: 用 .env + python-dotenv，不在代码中写密钥
- 日志: 用 loguru，不用 print

## 注意事项
- .env 中有 API 密钥，不要读取
- data/raw/ 中的原始 CSV 可能很大 (100MB+)，不要全部读入内存展示
- STATS19 数据的坐标系是 OSGB36 (EPSG:27700)，需转换为 WGS84 (EPSG:4326) 才能与天气数据匹配
- 学术报告需要 APA/Harvard 引用格式

---
<!-- ===== 以下动态区由 /wrap-up 命令维护 ===== -->

## 当前状态
最后更新: 尚未开始
当前分支: main
当前任务: 项目初始化 — 搭建结构、确认数据来源
阻塞问题: 无

## 最近完成
- （尚未开始）

## 关键决策
- （尚未做出决策）
- 详情见 @.claude/memory/decisions.md

## 已知问题
- [ ] 需要确认 STATS19 数据集的具体年份范围
- [ ] 需要评估 Open-Meteo 历史天气数据的覆盖范围
