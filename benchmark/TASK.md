# 标准评测任务（各 Agent 跑同一件事）

> 目的：让 Codex / WorkBuddy / Trae / Kimi 等跑**完全相同**的输入与任务，
> 使 token 消耗与触发效果具有可比性。

## 任务定义

**输入**：`benchmark/input/` 下的试卷文件（PDF 或图片，由你放置）

**要求**：把试卷整理成可打印的 LaTeX 试卷并编译出 PDF。

**产出**（缺一不可）：

| 文件 | 说明 |
|---|---|
| `questions.json` | 结构化题目（按 `references/question-types.md` 的字段定义） |
| `paper.tex` | LaTeX 源码（用 `exampaper.cls`） |
| `paper.pdf` | 编译产物 |

**约束**：
- 不改动 `benchmark/input/` 下的任何文件
- 图（电路图/信号图）需**重绘**，不得直接截图（截图无法打印）
- 不补全原件中缺失的题目

## 单条任务提示词（复制给各 Agent）

```
请用 seu-review-helper 技能，把 benchmark/input/ 里的试卷整理成可打印的
LaTeX 试卷，并编译成 PDF。产出 questions.json、paper.tex、paper.pdf 三样。

要求：
1. 先渲染成图片再做识别（这份 PDF 的文本层不可靠）
2. 图需要重绘成矢量图，不要截图
3. 不要补全原件中缺失的题目，识别不清的地方标注出来让我确认
4. 完成后告诉我：你读了哪些页面、每步大致消耗了多少上下文
```

## 记录哪些指标

| 维度 | 指标 | 采集方式 |
|---|---|---|
| **Token 消耗** | 总 token、输入/输出占比、峰值上下文 | 见 `scripts/bench/estimate_tokens.py`；有 API 用量的直接抄 |
| **触发效果** | 是否自动触发、触发时机、是否走对分支 | 见 `benchmark/trigger-cases.md` |
| **产物质量** | 题目识别准确率、图还原度、编译是否 0 错误 | 人工核对 + 编译日志 |
| **耗时** | 墙钟时间（含人工等待） | 秒表 |
| **人工干预** | 需要用户澄清/纠正的次数 | 自己数 |

**Token 是重点**，因为它是唯一能直接换算成钱的指标。采集时请区分：

- **输入 token**：系统提示 + 技能文档 + 页面图片 + 工具返回
- **输出 token**：Agent 生成的 JSON / LaTeX / 解释文字

> 经验值：视觉识别是消耗大头。一张 1191×1684 的页面 PNG 在不同模型下
> 约 1000–1600 token。6 页试卷 ≈ 6000–10000 token，这是**不可避免的底噪**。

## 控制变量（否则对比无意义）

1. **同一份输入文件**（同一 PDF，不要换）
2. **同一份技能文档**（同一 commit 的 SKILL.md / references）
3. **同一条提示词**（上面的原文，不要改写）
4. **同一台机器与网络**（渲染速度、Overleaf 上传速度会受影响）
5. **每个 Agent 跑 3 次**取中位数（首次运行有缓存/冷启动差异）

## 记录到哪

复制 `benchmark/results-template.csv` 为 `benchmark/results-<agent>.csv`，一跑一行。
