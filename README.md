# Awesome-SEU-Reviewer

> 让学生自己的 AI（Codex / WorkBuddy / Claude Code / Trae…）成为复习主编：
> 从历年真题与课件出发，预测考点、生成可打印的 LaTeX 试卷。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skill](https://img.shields.io/badge/Skill-multi--agent-blueviolet)](SKILL.md)

---

## 这是什么

一个**开源 Skill 包**，不是网站、不是服务、不是 CLI 应用。

它把复习这件事拆成四个**可独立调用**的能力，由学生本地的 Agent 按手头资料自主调度：

| | 能力 | 做什么 |
|---|---|---|
| **A** | 试卷 → 结构化题目 | 渲染成图 + 视觉识别，**能还原公式** |
| **B** | 考点预测 | 跨卷重复度 + 位置稳定性，**每步给出依据** |
| **C** | 生成 LaTeX 试卷 | 对接 `exampaper.cls`，图用矢量重绘 |
| **D** | 编译取 PDF | Overleaf 集成，一键上传 + 编译 + 下载 |

## 实测效果

拿东南大学「高等数学分析 II」的三份真题做过一次完整回测：

```
训练：2023-24 卷 + 2024-25 卷（各 18 题）
测试：2024-2025 工科卷
```

| 板块 | 命中 |
|---|---|
| 填空题（9 个位置） | **9 / 9 = 100%** |
| 计算与解答题 | 7 / 9 |
| **合计** | **16 / 18 ≈ 89%** |

完整对比表见 [`docs/backtest-report.md`](docs/backtest-report.md)。

**为什么会这么准**：大学考试不避讳重复命题。三份同课程试卷的 9 道填空题里，
有 8 道完全相同——**跨卷重复度本身就是最强信号**。

> 数据观察见 [`docs/dataset-observations.md`](docs/dataset-observations.md)。

## 快速开始

### 安装

```bash
# 任选一个 Agent 的 skills 目录
git clone https://github.com/sunflower070203/Awesome-SEU-Reviewer.git ~/.claude/skills/seu-review-helper
git clone https://github.com/sunflower070203/Awesome-SEU-Reviewer.git ~/.codex/skills/seu-review-helper
```

WorkBuddy 用户可直接通过技能市场导入。

### 第一次使用

唤起 Agent，告诉它你手上有什么：

> 「我有几份历年真题（PDF），帮我预测今年考点，并出一套模拟卷」

Agent 会自动判断资料类型，选择合适的能力组合，并在每一步把中间产物给你审阅。

**不需要外部 API key**——视觉识别与考点归并都由 Agent 自身完成。

## 设计原则

1. **零外部 API 调用**
   全流程不依赖付费接口。渲染、打分、生成 .tex 都是本地 Python（秒级）；
   视觉识别与语义归并由 Agent 自己完成。

2. **质量优先于省 token**
   `render.py` 默认 2.0× 渲染。降档只在确认无损时使用（如电子版 PDF）。
   理由：识别错误的返工成本远大于省下的 token。
   详见 [`docs/token-optimization.md`](docs/token-optimization.md)。

3. **有多少资料就用多少**
   试卷与课件不是二选一。`predictor.py` 会按实际输入判定
   `exam_only` / `hybrid` / `ppt_only`，并给出可操作的提示。

4. **每步留审阅点**
   中间产物（`questions.json`、预测清单）先给学生看，再决定是否继续。

## 仓库结构

```
Awesome-SEU-Reviewer/
├── SKILL.md                   # Agent 工作指令（含 YAML frontmatter，支持自动触发）
├── agents/                    # 多 Agent 适配
│   ├── generic.md             #   Claude Code / Cursor / 纯脚本用法 + 成本表
│   ├── openai.yaml            #   Codex
│   └── workbuddy.yaml         #   WorkBuddy
├── scripts/
│   ├── ocr/render.py          # PDF/图片 → 规范化 PNG（quality/balanced/fast 三档）
│   ├── predict/predictor.py   # 跨卷聚类 + 计分 + 归并
│   ├── latex/
│   │   ├── exampaper_adapter.py      # questions JSON → .tex
│   │   └── make_signal_figures.py    # 生成信号图（SVG + PDF）
│   └── bench/estimate_tokens.py      # token 消耗估算
├── references/
│   ├── question-types.md      # 题型规范
│   ├── topic-merge.md         # 考点归并规范（给 Agent 的语义判断准则）
│   └── ...
├── figures/signal/            # 矢量图（SVG 源 + PDF 产物）
├── templates/                 # exampaper.cls
├── benchmark/                 # 多 Agent 对比套件
│   ├── TASK.md                #   标准任务
│   ├── trigger-cases.md       #   触发测试用例（20 条）
│   └── results-template.csv
├── docs/                      # 设计与实测文档
└── examples/                  # 示例数据与编译产物
```

## 已知限制

- **仅课件（无试卷）模式尚未实现**：`ppt_only` 会提示需要补充试卷
- **手写体识别**依赖 Agent 的视觉能力，潦草字迹可能需人工核对
- **图的语义重绘**目前针对信号类图形做了实现，电路图需要按学科补充
- 跨卷聚类**无法识别"同考点、不同措辞"**，这部分依赖 Agent 做语义归并（见 `references/topic-merge.md`）

## 路线图

- [x] **Phase 1** 仓库骨架 + 文档
- [x] **Phase 2** Skill C：LaTeX 模板对接
- [x] **Phase 3** Skill B：考点预测（含回测验证）
- [x] **Phase 4** Skill A：渲染 + 视觉识别管线
- [x] **Phase 5** Skill D：Overleaf 编译闭环
- [x] **Phase 6** 多 Agent 适配（frontmatter 触发 + 成本表）
- [ ] **Phase 7** 多 Agent 实测对比（token / 触发效果）
- [ ] **Phase 8** 仅课件模式 + 更多学科的图形重绘

## 相关仓库

- [`sunflower070203/SEU-Test-Latex-Template`](https://github.com/sunflower070203/SEU-Test-Latex-Template) — 试卷 LaTeX 模板（`exampaper.cls`）

## 贡献

欢迎提 Issue / PR 改进识别准确率、扩充题型模板、增加新学科的词表与图形。

## 许可证

MIT
