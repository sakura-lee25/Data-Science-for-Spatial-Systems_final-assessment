#!/bin/bash
# ============================================================
# UK 交通事故分析项目 — Claude Code 配置一键初始化
# 
# 使用方法:
#   1. cd 到你的项目目录（或先创建）
#   2. bash setup.sh
# ============================================================

set -e

echo "🚗 初始化 UK 交通事故分析项目 Claude Code 配置..."
echo ""

# ---- 创建目录结构 ----
mkdir -p .claude/{commands,memory,agents,rules,skills/data-analysis}
mkdir -p data/{raw,processed,cache}
mkdir -p notebooks
mkdir -p src/{scraper,analysis,visualization,utils}
mkdir -p reports/{figures,tables}
mkdir -p tests

echo "✅ 目录结构已创建"

# ---- 创建 .gitignore ----
cat > .gitignore << 'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
*.egg
.venv/
venv/
env/

# Data (大文件不提交，只保留处理脚本)
data/raw/*.csv
data/raw/*.xlsx
data/raw/*.json
data/cache/
*.parquet

# Jupyter
.ipynb_checkpoints/
*.ipynb_metadata

# 环境和密钥
.env
.env.*
*.pem
*.key

# IDE
.idea/
.vscode/settings.json
*.swp

# Claude Code
.claude/settings.local.json
.claude/handoff*.md
.claude/session-snapshot.md

# 报告生成
reports/*.pdf
reports/*.docx
!reports/figures/.gitkeep
!reports/tables/.gitkeep

# OS
.DS_Store
Thumbs.db
GITIGNORE

echo "✅ .gitignore 已创建"

# ---- 创建 requirements.txt ----
cat > requirements.txt << 'REQUIREMENTS'
# 数据处理
pandas>=2.2.0
numpy>=1.26.0
openpyxl>=3.1.0

# 数据采集
requests>=2.31.0
beautifulsoup4>=4.12.0
selenium>=4.15.0
aiohttp>=3.9.0

# 可视化
matplotlib>=3.8.0
seaborn>=0.13.0
plotly>=5.18.0
folium>=0.15.0

# 统计分析
scipy>=1.12.0
statsmodels>=0.14.0
scikit-learn>=1.4.0

# 地理数据
geopandas>=0.14.0
shapely>=2.0.0

# 天气数据
meteostat>=1.6.0

# 工具
python-dotenv>=1.0.0
tqdm>=4.66.0
loguru>=0.7.0

# 测试
pytest>=8.0.0
pytest-cov>=4.1.0

# Jupyter
jupyter>=1.0.0
ipykernel>=6.29.0
REQUIREMENTS

echo "✅ requirements.txt 已创建"

# ---- 创建占位文件 ----
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch reports/figures/.gitkeep
touch reports/tables/.gitkeep
touch src/__init__.py
touch src/scraper/__init__.py
touch src/analysis/__init__.py
touch src/visualization/__init__.py
touch src/utils/__init__.py
touch tests/__init__.py

echo "✅ 占位文件已创建"

# ---- 创建 .env.example ----
cat > .env.example << 'ENVEXAMPLE'
# UK 数据 API
# 申请地址: https://data.gov.uk
DATA_GOV_UK_API_KEY=your_key_here

# Met Office Weather API (可选)
# 申请地址: https://www.metoffice.gov.uk/services/data
MET_OFFICE_API_KEY=your_key_here

# Open-Meteo (免费，无需 key)
# https://open-meteo.com/
ENVEXAMPLE

echo "✅ .env.example 已创建"

echo ""
echo "🎉 项目结构初始化完成！"
echo ""
echo "接下来的步骤："
echo "  1. 编辑 CLAUDE.md 确认项目信息"
echo "  2. 创建虚拟环境:"
echo "     python -m venv .venv && source .venv/bin/activate"
echo "  3. 安装依赖:"
echo "     pip install -r requirements.txt"
echo "  4. 复制环境变量:"
echo "     cp .env.example .env"
echo "  5. 启动 Claude Code:"
echo "     claude"
echo "  6. 运行 /recap 查看项目状态"
echo ""
