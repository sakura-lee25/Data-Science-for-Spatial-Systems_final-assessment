---
description: 生成出版质量的学术图表。指定数据和图表类型即可。
allowedTools: ["Read", "Bash", "Write"]
---

生成学术论文质量的图表：$ARGUMENTS

图表规范：
- 使用 Matplotlib + Seaborn
- 字体: 12pt, Times New Roman 或 serif
- DPI: 300 (出版质量)
- 保存为 PDF 和 PNG 到 reports/figures/
- 包含清晰的轴标签、标题、图例
- 配色使用 colorblind-friendly palette
- 图表尺寸: 单栏 (3.5 inch) 或双栏 (7 inch)
- 添加适当的网格线

代码保存为可复现的 Python 脚本到 src/visualization/
