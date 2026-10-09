# SKILL.md — Agent 工作指令

> 本文件被 Agent（Codex / WorkBuddy / Claude Code 等）自动加载。Agent 收到与"复习/考点/试卷/OCR"相关的请求时，按本文件的约定路由到对应的 Skill。

---

## 触发条件

满足以下任一条件时，本 Skill 被激活：

1. 用户提供 PPT / 真题 / 复习笔记路径，请求"生成预测试卷"、"预测考点"、"整理真题"
2. 用户提到"OCR"、"扫描版"、"手写"、"拍照版"等关键词
3. 用户要求"LaTeX 试卷"、"Overleaf 编译"、"exampaper 模板"
4. 用户问"这道题会不会考"、"今年重点是什么"

---

## 核心约束

**学生本地 Agent 是总主编**。本 Skill 不替代学生 Agent 的判断：

- ✅ Skill 返回 JSON 中间产物，由学生 Agent 决定是否继续 / 修改 / 重试
- ❌ Skill 不擅自"一键出成品"，跳过审阅步骤
- ❌ Skill 不缓存学生资料，所有文件操作走学生提供的路径

---

## 路由表

根据用户输入类型，按以下顺序调用 Skill：

| 场景 | 调用顺序 |
|---|---|
| 用户提供**拍照/手写真题** | Skill A → Skill B（可选）→ Skill C → Skill D |
| 用户提供**PPT + 往年真题（LaTeX）** | Skill B → Skill C → Skill D |
| 用户提供**纯复习笔记** | Skill B → Skill C → Skill D |
| 用户只问**"OCR 这一张图"** | 仅 Skill A |
| 用户只问**"预测考点"** | 仅 Skill B |
| 用户只问**"生成 LaTeX"** | 仅 Skill C |

---

## Skill 契约摘要

完整 JSON Schema 见 `docs/review-helper-architecture.md`，以下是 Agent 调用时的最小示例。

### Skill A: OCR → LaTeX

```jsonc
// 输入
{
  "images": ["C:/.../q1.jpg", "C:/.../q2.png"],
  "pipeline_strategy": "auto",
  "ocr_providers": {
    "handwriting": "tencent",
    "formula": "mathpix"
  },
  "preprocess": {"enabled": true, "super_resolution": true}
}

// 输出
{
  "questions": [
    {
      "number": 1,
      "type": "calculation",
      "stem_latex": "设 $X \\sim N(\\mu, \\sigma^2)$，求 ...",
      "ocr_confidence": 0.91,
      "needs_review": false
    }
  ],
  "ocr_summary": {"total_pages": 4, "avg_confidence": 0.83},
  "warnings": []
}
```

### Skill B: 考点预测器

```jsonc
// 输入
{
  "ppt_paths": ["C:/.../ch3.pptx"],
  "past_exam_questions": [...],
  "focus_topics": ["第三章"],
  "config": {"algorithm": "tfidf_textrank_llm", "predicted_questions_n": 15}
}

// 输出
{
  "keywords": [{"term": "中心极限定理", "weight": 0.92, "source": "..."}],
  "predicted_questions": [
    {
      "id": "P1", "type": "calculation", "topic": "假设检验",
      "weight": 0.88, "rationale": "近 3 年出现 5 次",
      "sample_question_latex": "...", "expected_difficulty": "medium"
    }
  ],
  "explainability": {"method": "TF-IDF + TextRank + LLM"}
}
```

### Skill C: LaTeX 试卷生成

```jsonc
// 输入
{
  "questions": [{"number": 1, "type": "choice", "stem_latex": "...", "score": 5}],
  "header": {
    "course_name": "概率论",
    "course_code": "ST203",
    "semester": "2025-2026-2",
    "major": "信息工程",
    "exam_type": "闭卷",
    "duration_minutes": 120
  }
}

// 输出
{
  "tex_source": "\\documentclass[12pt,a4paper]{exampaper}...",
  "tex_file_path": "C:/.../predicted_exam.tex",
  "warnings": []
}
```

### Skill D: Overleaf 集成

```jsonc
// 输入
{
  "overleaf_project_url": "https://www.overleaf.com/project/abc123",
  "tex_content": "...",
  "compile_strategy": "replace_main"
}

// 输出
{
  "pdf_path": "C:/.../predicted_exam.pdf",
  "compile_success": true,
  "overleaf_url": "..."
}
```

---

## Agent 工作流程（推荐）

```
[1] 询问学生：
    - 课程名？
    - 重点章节？
    - 有哪些资料（PPT路径 / 真题路径 / 笔记路径）？

[2] 检查资料路径是否存在
    - 缺失则提示学生补齐，不擅自猜测

[3] 按路由表顺序调 Skill，每个 Skill 返回 JSON 后立刻展示给学生审阅

[4] 学生 Agent 应主动追问：
    - "第 3 题 needs_review=true，要不要人工核对？"
    - "为什么 P1 的 weight=0.88？"
    - "exampaper 模板要不要换成我自己的？"

[5] 全部 Skill 调用完毕，整理一份给学生的"复习总结"：
    - 预测的考点 Top 10
    - 重点题型与分布
    - 生成的 PDF 路径
```

---

## OCR Provider 配置

学生首次使用 OCR 前，需在本地配置 API 凭据：

```bash
cp assets/ocr-providers.example.yaml ~/.config/seu-review-helper/ocr-providers.yaml
# 编辑填入凭据，或用环境变量
```

支持的 provider：

| Provider | 擅长 | 凭据 |
|---|---|---|
| 腾讯云手写体 | 中等清晰度手写中文 | `TENCENT_SECRET_ID` / `TENCENT_SECRET_KEY` |
| Mathpix | 印刷体公式（99%+） | `MATHPIX_APP_ID` / `MATHPIX_APP_KEY` |
| PaddleOCR 本地 | 离线场景 | 模型路径 |
| LLM Vision（GPT-4V/Claude） | 严重涂抹，语义推断 | 通过本地 Agent 调用 |

未配置时不报错，直接降级到 "无 OCR" 模式（学生 Agent 提示"OCR 未启用，请人工转录"）。

---

## 不做什么

- ❌ 不做账号系统、不收集用户数据
- ❌ 不训练模型、不微调
- ❌ 不生成网页前端
- ❌ 不做"一键出成品"的黑盒流程
- ❌ 不擅自决定学生想要什么样的试卷

---

## 反馈与改进

发现 Bug 或有改进建议：在 `https://github.com/sunflower070203/Awesome-SEU-Reviewer/issues` 提 Issue。
