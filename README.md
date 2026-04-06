# 🚗 UK 交通事故分析项目 — 安装指南

## 你需要做什么

打开终端 (Terminal)，按顺序执行以下命令。每一步都有说明。

---

### Step 1: 创建项目目录

```bash
mkdir -p ~/projects/uk-traffic-analysis
cd ~/projects/uk-traffic-analysis
```

### Step 2: 解压配置文件

把下载的 ZIP 解压，将所有文件复制到项目目录：

```bash
# 假设 ZIP 解压到了 ~/Downloads/uk-traffic-project/
cp -r ~/Downloads/uk-traffic-project/* ~/projects/uk-traffic-analysis/
cp -r ~/Downloads/uk-traffic-project/.* ~/projects/uk-traffic-analysis/ 2>/dev/null
```

或者手动将以下文件放到项目目录：
- `CLAUDE.md` → 项目根目录
- `.claude/` 整个文件夹 → 项目根目录
- `.mcp.json` → 项目根目录
- `setup.sh` → 项目根目录

### Step 3: 运行初始化脚本

```bash
cd ~/projects/uk-traffic-analysis
bash setup.sh
```

这会创建：目录结构、.gitignore、requirements.txt

### Step 4: 创建 Python 虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 5: 初始化 Git

```bash
git init
git add .
git commit -m "chore: 项目初始化"
```

### Step 6: 设置全局 Claude 配置（如果还没有）

```bash
# 创建全局 CLAUDE.md（只需做一次）
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md << 'EOF'
# 关于我
- [你的名字]，[你的角色]
- 偏好中文沟通，代码注释英文

# 我的活跃项目
| 项目 | 路径 | 状态 |
|------|------|------|
| UK 交通事故分析 | ~/projects/uk-traffic-analysis | 开发中 |

# 通用规范
- 每次收工运行 /wrap-up 保存记忆
- 复杂任务先 Plan Mode
EOF
```

### Step 7: 启动 Claude Code！

```bash
cd ~/projects/uk-traffic-analysis
source .venv/bin/activate
claude
```

进入 Claude Code 后：
1. 输入 `/recap` 查看项目状态
2. 开始工作！
3. 结束前输入 `/wrap-up` 保存记忆

---

## 可用命令速查

| 命令 | 用途 | 何时用 |
|------|------|--------|
| `/recap` | 恢复项目上下文 | 每次开始工作 |
| `/wrap-up` | 保存进度和决策 | 每次结束工作 |
| `/eda data/raw/xxx.csv` | 快速数据探索 | 拿到新数据时 |
| `/plot 事故按小时分布柱状图` | 生成学术图表 | 需要可视化时 |

## 文件结构确认

执行完上述步骤后，你的项目目录应该长这样：

```
uk-traffic-analysis/
├── CLAUDE.md                    ✅ 项目记忆
├── .mcp.json                    ✅ MCP 配置
├── .gitignore                   ✅
├── requirements.txt             ✅
├── .env.example                 ✅
├── .claude/
│   ├── settings.json            ✅ Hooks + 权限
│   ├── commands/
│   │   ├── recap.md             ✅ /recap
│   │   ├── wrap-up.md           ✅ /wrap-up
│   │   ├── eda.md               ✅ /eda
│   │   └── plot.md              ✅ /plot
│   ├── memory/
│   │   ├── decisions.md         ✅ 架构决策
│   │   ├── progress.md          ✅ 进度追踪
│   │   └── lessons.md           ✅ 踩坑记录
│   ├── agents/
│   │   └── data-analyst.md      ✅ 数据分析子代理
│   ├── rules/
│   │   └── academic-writing.md  ✅ 学术写作规范
│   └── skills/
│       └── data-analysis/
│           └── SKILL.md         ✅ 数据分析技能
├── data/
│   ├── raw/                     📁 原始数据
│   ├── processed/               📁 清洗后数据
│   └── cache/                   📁 缓存
├── notebooks/                   📁 Jupyter notebooks
├── src/
│   ├── scraper/                 📁 数据采集
│   ├── analysis/                📁 统计分析
│   ├── visualization/           📁 可视化
│   └── utils/                   📁 工具函数
├── reports/
│   ├── figures/                 📁 图表
│   └── tables/                  📁 表格
└── tests/                       📁 测试
```
