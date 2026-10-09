# Awesome-SEU-Reviewer

> 让每个学生自己的 AI（Codex / WorkBuddy / Claude Code）成为复习主编，从 PPT、拍照真题、复习笔记生成可编译的预测试卷。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skill](https://img.shields.io/badge/Skill-multi--agent-blueviolet)](SKILL.md)

---

## 这是什么

一个**开源 Skill 包**，不是网站、不是服务、不是 CLI 应用。

它提供四个**可独立调用**的能力（Skill A / B / C / D），由学生本地 Agent（Codex / WorkBuddy / Claude Code 等）根据学生资料和对话上下文自主调度。

## 解决什么痛点

| 痛点 | 解决方案 |
|---|---|
| 期末复习需要往年真题，但拿到的是手写/拍照版 | **Skill A**：OCR pipeline，针对手写/拍照/公式电路三类场景 |
| 手头有 PPT 和真题，但不会总结考点，不知道会考什么 | **Skill B**：TF-IDF + TextRank + 共现矩阵 + LLM 归纳预测 |
| 排版试卷费时，找不到合适的 LaTeX 模板 | **Skill C**：直接对接 [`sunflower070203/SEU-Test-Latex-Template`](../SEU-Test-Latex-Template) 的 `exampaper.cls` |
| 编译 LaTeX 配置麻烦 | **Skill D**：Overleaf 集成，一键上传+编译+下载 PDF |

## 与 `SEU-course-study-kit` 的差异

| 维度 | SEU-course-study-kit | Awesome-SEU-Reviewer |
|---|---|---|
| OCR | 无内置 OCR | **内置三场景 OCR pipeline** |
| 考点预测 | 纯 LLM 生成 | **算法加权 + LLM 归纳** |
| 公式还原 | "无法完全恢复" | **Mathpix 集成** |
| 电路图 | 未提及 | **图像占位 + circuitikz 半自动还原** |
| 试卷模板 | Markdown 校验 | **直接对接 `exampaper.cls`** |

## 快速开始

### 安装（任选一）

**WorkBuddy**
```bash
skillmanage install sunflower070203/Awesome-SEU-Reviewer
```

**Codex**
```bash
git clone https://github.com/sunflower070203/Awesome-SEU-Reviewer.git ~/.codex/skills/seu-review-helper
```

**Claude Code**
```bash
git clone https://github.com/sunflower070203/Awesome-SEU-Reviewer.git ~/.claude/skills/seu-review-helper
```

### 第一次使用

把你的 Agent 唤起来，告诉它：

> "我手头有 `C:/Downloads/高数PPT/` 和 `C:/Downloads/2023高数期末.jpg`，帮我生成一份预测试卷"

Agent 会自动识别可用资料，按顺序调用 Skill A → B → C → D，并在每一步把 JSON 中间产物返回给你审阅。

## 仓库结构

```
Awesome-SEU-Reviewer/
├── README.md                  # 本文件
├── SKILL.md                   # Agent 工作指令
├── LICENSE                    # MIT
├── agents/                    # 多 Agent 适配层
│   ├── openai.yaml            # Codex 加载元数据
│   └── workbuddy.yaml         # WorkBuddy 加载元数据
├── assets/                    # 配置示例 + prompt 模板
│   ├── exam-config.example.json
│   ├── ocr-providers.example.yaml
│   └── prompt-templates/
├── references/                # 规范与质量规则
│   ├── question-types.md
│   ├── quality-rules.md
│   └── chinese-handwriting-ocr.md
├── scripts/                   # Python 实现
│   ├── ocr/
│   ├── predict/
│   └── latex/
├── templates/                 # LaTeX 模板（exampaper.cls 引入）
└── examples/                  # 示例数据与输出
```

详见 [SKILL.md](SKILL.md) 与 `docs/`。

## 路线图

- [x] **Phase 1**：仓库骨架 + 文档
- [ ] **Phase 2**：Skill C LaTeX 模板对接
- [ ] **Phase 3**：Skill B 考点预测算法
- [ ] **Phase 4**：Skill A OCR pipeline
- [ ] **Phase 5**：Skill D Overleaf 集成
- [ ] **Phase 6**：多 Agent 适配
- [ ] **Phase 7**：示例数据 + CI

## 贡献

欢迎提 Issue / PR 改进 OCR 准确率、扩充题型模板、增加新学科的考点词典。

## 许可证

MIT
