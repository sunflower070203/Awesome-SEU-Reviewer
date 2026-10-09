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

## 统一数据总线（Skill 交融的基础）

四个 Skill **不是孤立的命令**，而是围绕同一条"数据总线"组装的能力模块：

```
            ┌──────────────────────────────────────────────┐
            │        questions JSON（通用数据货币）           │
            └──────────────────────────────────────────────┘
                 ▲                    ▲              ▲
                 │ 输出               │ 输入+输出      │ 输入
          ┌──────┴──────┐    ┌───────┴──────┐  ┌────┴────┐
          │ Skill A      │    │ Skill B      │  │Skill C  │
          │ 图片→questions│   │ 语料→questions │  │questions│
          └──────────────┘    │   (含预测题)   │  │  →.tex  │
                              └──────────────┘  └─────────┘
```

**核心约定**：`questions`（题目 JSON 数组）是所有 Skill 的通用输入输出格式。

| Skill | 输入 | 输出 |
|---|---|---|
| A | 图片 | `questions` |
| B | 语料 + `questions`（真题） | `questions`（预测题，多 `rationale` 字段） |
| C | `questions` | `.tex` |
| D | `.tex` | PDF |

**这带来三个直接后果**（Agent 必须理解）：

1. **任何 Skill 的输出可以直接喂给下一个**，不需要格式转换
2. **多条来源的 questions 可以合并**：OCR 真题 70% + 预测题 30% 混合出卷是自然操作
3. **部分采纳是常规操作**：学生挑 10 道预测题 + 5 道 OCR 真题，合并后进 Skill C

---

## 动态编排逻辑（Agent 自己推理，不是固定 pipeline）

### 第一步：资料盘点（inventory）

Agent 收到学生请求后，**先盘点**学生提供的资料，分类：

| 资料形态 | 可处理的 Skill |
|---|---|
| 图片（.jpg/.png，拍照/手写） | A |
| PPT（.pptx） | B |
| LaTeX 真题（.tex） | B（作语料）、C（直接重排） |
| 复习笔记（.md/.txt） | B |
| questions JSON | C |
| .tex 文件 | D |

### 第二步：目标反推（goal decomposition）

Agent 询问（或从对话推断）学生想要的**最终产物**：

| 学生说 | 最终产物 | 需要的中间产物 |
|---|---|---|
| "帮我生成预测试卷" | PDF | `questions` → `.tex` |
| "整理这份手写卷子" | 重排的 PDF | `questions` → `.tex` |
| "今年会考什么" | 对话讨论 | 仅 `keywords` + `predicted_questions` |
| "OCR 这张图" | `questions` JSON | 仅 OCR |
| "把这些题排版" | `.tex` / PDF | `.tex` |

### 第三步：链式组装（Agent 自主推理）

Agent 根据"盘点结果 + 目标产物"**自主组装调用链**：

- 缺哪段补哪段：有图无题 → 先 OCR；有题无预测 → 可跳过 B
- 产物够了就停：学生只要考点讨论，不调 C/D
- 降级可继续：OCR 凭据未配置 → 提示人工转录 → 学生贴文本 → 继续 B/C/D

### 第四步：审阅节点（人机交互）

每个 Skill 返回 JSON 后，Agent **必须**把中间产物展示给学生：

- "第 3 题 needs_review=true，要人工核对吗？"
- "预测了 15 题，要全用还是挑几道？"
- 学生改动后，Agent 只重跑受影响的下游（学生改了题 → 只重跑 C；没改 → 直接进 C）

---

## 组合剧本（典型场景，非穷举）

### 剧本 1：全流程（拍照真题 + PPT → 预测卷 PDF）

```
盘点: 3 张拍照真题 + 2 个 PPT
目标: 预测试卷 PDF
组装: A(图片→questions) → 审阅 → B(PPT+questions→预测题)
      → 审阅(挑选合并) → C(questions→tex) → D(tex→PDF)
```

### 剧本 2：混合出卷（OCR 真题为主体 + 预测题补充）

```
盘点: 1 份手写真题 + PPT
目标: 复习卷（真题为主）
组装: A → 审阅 → B → 学生说"真题全要，预测题挑 5 道"
      → Agent 合并 questions（真题 20 + 预测 5）→ C → D
```

### 剧本 3：只要整理（老卷翻新）

```
盘点: 1 份拍照真题
目标: 清晰可打印的旧卷
组装: A → 审阅 → C → D（完全不调 B）
```

### 剧本 4：只要预测（对话式讨论）

```
盘点: PPT + 已有 LaTeX 真题
目标: 知道考什么
组装: B（真题 .tex 直接读作语料）
      → Agent 对话式讲解 keywords + predicted_questions
      → 不调 C/D，学生问"能出一份吗"再进 C
```

### 剧本 5：迭代修正（局部重跑）

```
学生: "刚才那份卷子第 3 题换掉"
Agent: 修改 questions[2] → 只重跑 C → 重跑 D
      （不重跑 A/B，因为 OCR 结果和预测没变）
```

### 剧本 6：降级链（OCR 不可用）

```
盘点: 拍照真题，但 OCR 凭据未配置
Agent: 提示"OCR 未启用，请把题目文字贴给我"
学生: 贴文本
Agent: 文本 → questions（Agent 自己解析，不走 A）
      → 继续 B/C/D
```

---

## 反模式（Agent 禁止）

- ❌ **固定 pipeline 思维**：不管学生要什么都跑 A→B→C→D 全流程
- ❌ **跳过审阅**：Skill 返回后直接调下一个，不给学生看中间产物
- ❌ **全有全无**：某个 Skill 不可用就整体报错放弃，而不是降级继续
- ❌ **擅自合并**：没问学生就混合 OCR 题和预测题
- ❌ **重复调用**：学生只改了一道题，Agent 重跑整个 A/B

---

## Skill 契约摘要

完整 JSON Schema 见 `docs/review-helper-architecture.md`，以下是 Agent 调用时的最小示例。

### Skill A: 试卷/图片 → questions JSON

**分两步：先渲染，再视觉识别。**

```bash
# 第 1 步：渲染为规范化 PNG（scripts/ocr/render.py）
python scripts/ocr/render.py --input exam.pdf --outdir .tmp-render
python scripts/ocr/render.py --input scans/ --outdir .tmp-render      # 目录批量
```

产出 `.tmp-render/*.png` 与 `manifest.json`（含每页尺寸与文本层字符数）。

```jsonc
// 第 2 步：Agent 用视觉能力读取 PNG，按 assets/prompt-templates/vision-extract.txt
// 的规范输出 questions JSON（Agent 自身是多模态的，无需额外 OCR API）
{
  "exam_id": "2024-25",
  "questions": [
    {
      "number": 1, "type": "fill", "section": "填空题",
      "stem_latex": "若直线 $\\frac{x-1}{2}=\\frac{y-1}{\\lambda}=\\frac{z-1}{1}$ 与直线 $x+1=y-1=z$ 垂直，则 $\\lambda=$____",
      "score": 4,
      "confidence": 0.95, "needs_review": false, "source_page": 1
    }
  ],
  "header": {"course_name": "高等数学分析 II", "semester": "23-24-3"},
  "warnings": []
}
```

**为什么是"渲染 + 视觉"而非直接调 OCR API**（实测依据见 `docs/dataset-observations.md`）：

- 真实试卷 PDF 的文本层可能是 **CID 乱码**（提取出来是字形索引），也可能是**纯扫描件**
- 渲染成 2 倍 PNG 后，视觉模型能**准确还原公式、分式、求和号、分段函数**
- 免费、无凭据依赖，且统一了「电子版 PDF」与「拍照/扫描」两条入口

**外部 OCR 仅作兜底**：若 Agent 不具备视觉能力，或遇到严重涂改，再考虑腾讯云手写 OCR / Mathpix（见 `assets/ocr-providers.example.yaml`）。

### Skill B: 考点预测器

```jsonc
// 输入：试卷池（≥2 份历年卷，由 Skill A 产出 questions）
{
  "exams": [
    {
      "id": "2024-25",
      "label": "2024-2025 学年",
      "questions": [
        {"number": 4, "type": "fill", "score": 4,
         "stem_latex": "设 $D=\\{(x,y)|x^2+y^2\\le 1\\}$，则 $\\iint_D |x+y|d\\sigma=$____"}
      ]
    }
  ]
}

// 输出：按信号强度排序的考点簇
{
  "n_exams": 3,
  "exam_ids": ["2023-24", "2024-25", "gongshu-2024-25"],
  "threshold": 0.5,
  "predictions": [
    {
      "rank": 1, "score": 1.0,
      "repeat": 1.0,
      "exams_seen": ["2023-24", "2024-25", "gongshu-2024-25"],
      "position_stability": 1.0,
      "positions": {"fill#4": 3},
      "n_members": 3,
      "rationale": "在 3/3 份试卷中出现；3 次位于第 4 题（fill）；未缺席，判为必考",
      "stem_samples": ["..."]
    }
  ]
}
```

**实现方式**（本仓库已提供）：

```bash
python scripts/predict/predictor.py --input pool.json --output predictions.json
python scripts/predict/predictor.py --input pool.json --threshold 0.4 --format text
```

**打分公式**（详见 `docs/dataset-observations.md`）：

```
score = 0.75 × 跨卷重复度 + 0.25 × 位置稳定性
跨卷重复度   = 该簇出现的卷数 / 总卷数
位置稳定性   = 簇内「题型 + 题号」一致的样本占比
```

**为什么不用 TF-IDF / 知识追踪**：小样本（2-4 份）下 IDF 只有 3 档、区分度极低；知识追踪需要上万条学生答题数据。真实观察表明「跨卷重复度」本身就是最强信号——三份同课程试卷的 9 道填空题里有 8 道完全相同。

**课件 PPT 为可选输入**：当前实现只用试卷；若提供课件，可加回「PPT 覆盖度」维度（需重新分配权重）。

**输入模式：按实际资料灵活判定**

试卷与课件**不是二选一**——用户可能只有其中一种，也可能两者都有。`predictor.py` 会自动判定模式，Agent 据此提示用户，而非要求补齐某一种：

| 用户手上的资料 | 模式 | 当前支持 |
|---|---|---|
| ≥ 2 份试卷（可与课件同时存在） | `exam_only` / `hybrid` | ✅ 均可用（hybrid 暂降级，返回值带 warning） |
| **只有**课件、无试卷 | `ppt_only` | ❌ 未实现，报错并说明需补充试卷 |
| 两者都不足 | `insufficient` | ❌ 报错，说明最低要求 |

判定逻辑：`≥2 份试卷` + `有课件` → hybrid；`≥2 份试卷` → exam_only；`仅课件` → ppt_only。

> 设计原则：**有多少资料就用多少**——不要因为用户没给课件就拒绝服务，也不要因为没给试卷就报「资料不全」而不提示替代路径。

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

**实现方式**（本仓库已提供，Agent 直接调用）：

```bash
python scripts/latex/exampaper_adapter.py \
  --input  exam.json \      # {"header": {...}, "questions": [...]}，header 也可写作 exam_meta
  --output paper.tex
```

- 模板文件：`templates/exampaper.cls`（说明见 `templates/README.md`）
- 题型 → 栏目标题 / 答题空间的映射，见 `scripts/latex/exampaper_adapter.py` 顶部的 `TYPE_TITLES` / `ANSWER_SPACE` 常量
- 输入示例：`examples/sample-exam-input.json`
- 编译：**XeLaTeX，连续两遍**
- 选项写法：内联 `\quad A.\ ... \quad B.\ ...`（不用 enumerate，详见 `references/question-types.md`）

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
