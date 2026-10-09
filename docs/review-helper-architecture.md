# 复习助手架构设计文档

> 状态：设计稿 v0.2（待评审）
> 更新：加入 OCR 三痛点处理、GitHub 发布形态、与 `SEU-course-study-kit` 的差异化定位
> 范围：Skill 契约 + 数据流 + 边界，不含具体实现
> 评审通过后再进入实现阶段

---

## 0. 项目定位与差异化

### 0.1 定位

面向东南大学（SEU）学生 / 全国高校师生的 **GitHub Skill 包**，可被 Codex、WorkBuddy、Claude Code 等任意 Agent 加载使用，从 PPT / 拍照真题 / 复习资料生成可编译的预测试卷。

### 0.2 对比 `zhuyilun0409/SEU-course-study-kit`

| 维度 | 同学版本（SEU-course-study-kit） | 本项目 |
|---|---|---|
| OCR | **无内置 OCR**，扫描版需自接 | **内置三场景 OCR pipeline**（手写/拍照/公式电路） |
| 题目生成 | 基于语料的纯 LLM 生成 | LLM + **算法加权**（TF-IDF + TextRank + 真题共现） |
| 公式还原 | "无法完全恢复" | **Mathpix 集成**（业界最强公式 OCR） |
| 电路图 | 未提及 | **图像占位 + circuitikz 还原** + 人工标注接口 |
| 试卷模板 | Markdown 校验 | 直接对接 **`SEU-Test-Latex-Template`**（exampaper.cls） |
| 跨 Agent 兼容 | Codex Skill 单形态 | Codex Skill + WorkBuddy Skill + 通用 CLI |
| 目标 | 任意课程的复习资料生成 | **聚焦期末真题场景**（拍照→预测→编译） |

### 0.3 设计原则

| 原则 | 含义 |
|---|---|
| **Skill 是工具，Agent 是主编** | 每个 Skill 暴露"输入-输出契约"，不封装"何时用、怎么用"的决策 |
| **只返回结构化中间产物** | Skill 输出 JSON，不直接出"成品"；让学生 Agent 审阅、改写、追问 |
| **可部分调用** | 任何 Skill 都可独立使用，不强制端到端流程 |
| **无状态** | Skill 不缓存学生资料；学生资料的所有权在本地文件系统 |
| **插件化 OCR** | OCR provider 不绑定单一服务，学生可切换 / 自部署 |

---

## 1. 设计目标与约束

### 1.1 核心约束（来自用户）

1. **不做成网站/服务**：所有调度权必须在学生本地 Agent，资料不出本地
2. **每个学生用自己的 AI 总结**：服务端只提供"被调用的工具"，不提供"端到端 Agent"
3. **复用已有能力**：Overleaf 集成复用现有 `overleaf-webbridge-check` skill
4. **轻量算法**：考点预测借鉴 TF-IDF / TextRank / 注意力思想，不训练模型
5. **GitHub 开源发布**：可被 Codex / WorkBuddy / Claude Code 等任意 Agent 加载

### 1.2 非目标（明确不做的事）

- 不做账号系统、不做用户管理、不做数据持久化
- 不做模型训练、不做微调
- 不做网页前端、不做移动端
- 不做"一键生成试卷"的黑盒模式

---

## 2. GitHub 发布形态

### 2.1 仓库结构（参考 `SEU-course-study-kit` 改良）

```
SEU-review-helper/
├── README.md                          # 中文/英文双语，含安装、使用、原理
├── LICENSE                            # MIT（与参考项目一致）
├── SKILL.md                           # Agent 工作指令（Codex/WorkBuddy/Claude 共用）
├── agents/
│   ├── openai.yaml                    # Codex 加载元数据
│   └── workbuddy.yaml                 # WorkBuddy 加载元数据
├── assets/
│   ├── exam-config.example.json       # 蓝图配置示例
│   ├── prompt-templates/              # LLM prompt 模板
│   │   ├── keyword_extraction.txt
│   │   ├── question_generation.txt
│   │   └── rationale_explanation.txt
│   └── ocr-providers.example.yaml     # OCR provider 配置示例
├── references/
│   ├── question-types.md              # 题型规范
│   ├── quality-rules.md               # 题目质量规则
│   └── chinese-handwriting-ocr.md     # 手写识别特殊性
├── scripts/
│   ├── build_corpus.py                # 复用同学版本思路：语料构建
│   ├── validate_exam.py               # 试卷校验
│   ├── ocr/
│   │   ├── preprocess.py              # 图像预处理（去噪/二值化/超分）
│   │   ├── tencent_handwriting.py     # 腾讯云手写体
│   │   ├── mathpix.py                 # Mathpix 公式识别
│   │   ├── paddleocr_local.py         # 本地 PaddleOCR（兜底）
│   │   └── pipeline.py                # OCR pipeline 总控
│   ├── predict/
│   │   ├── tfidf_keywords.py          # TF-IDF 关键词提取
│   │   ├── textrank.py                # TextRank 关联度
│   │   ├── cooccurrence.py            # 关键词共现矩阵
│   │   └── predictor.py               # 算法+LLM 融合预测
│   └── latex/
│       ├── exampaper_adapter.py       # 数据 → exampaper.cls 命令
│       └── compile_local.sh           # 本地 XeLaTeX 编译（可选）
├── templates/
│   └── exampaper.cls                  # 从 SEU-Test-Latex-Template 引入（Git submodule 或直接复制）
├── examples/
│   ├── sample-ppt/                    # 示例 PPT（占位）
│   ├── sample-exam-photo/             # 示例拍照真题（占位）
│   └── output/                        # 示例输出 PDF
└── .github/workflows/
    └── build.yml                      # CI:编译模板 + 运行示例
```

### 2.2 多 Agent 兼容

| Agent | 加载方式 | 触发命令 |
|---|---|---|
| **Codex** | `~/.codex/skills/seu-review-helper` | Agent 自动发现 |
| **WorkBuddy** | 通过 SkillManage 安装 | Agent 自动发现 |
| **Claude Code** | `~/.claude/skills/seu-review-helper` | `/skill seu-review-helper` |
| **通用 CLI** | `pip install seu-review-helper` 或直接 `python scripts/` | 命令行 |

SKILL.md 在所有 Agent 形态下共用，仅 `agents/*.yaml` 文件做适配层。

---

## 3. 整体架构

### 3.1 系统分层

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: 学生本地 Agent（总主编）                                  │
│   - 拥有资料文件路径、知识上下文、对话历史                          │
│   - 决定调哪个 Skill、调几次、参数是什么                           │
│   - 审阅 Skill 返回的 JSON，决定是否继续、修改、重试               │
└─────────────────────────────────────────────────────────────────┘
                              │ 调用（输入 JSON）
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: Skill 层（无状态工具）                                    │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐│
│   │ Skill A       │ │ Skill B       │ │ Skill C       │ │Skill D  ││
│   │ OCR → LaTeX  │ │ 考点预测器    │ │ LaTeX 模板    │ │Overleaf ││
│   │ （Pipeline）  │ │              │ │              │ │         ││
│   └──────────────┘ └──────────────┘ └──────────────┘ └─────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │ 调用
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: 基础设施层                                               │
│   - 文件系统（学生本地）                                           │
│   - 浏览器桥（Overleaf WebBridge）                                │
│   - OCR provider 池（可插拔）                                     │
│   - 本地 LLM（学生 Agent 自带）                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 数据流（典型场景）

```
[1] 学生 Agent 读取本地文件
    ├─ PPT 文件路径列表
    ├─ 拍照真题（PNG/JPG）
    └─ 已有往年真题 LaTeX（可选）

[2] 调 Skill A: OCR → LaTeX Pipeline
    输入: {images: [...], pipeline_strategy: "auto"}
    输出: {questions: [...], confidence_map: {...}, warnings: [...]}

[3] 调 Skill B: 考点预测器
    输入: {ppt_paths, past_exam_questions, focus_topics}
    输出: {keywords, predicted_questions, topic_distribution, explainability}

[4] 学生 Agent 审阅 JSON，可追问/删改/补题

[5] 调 Skill C: LaTeX 试卷生成（直接对接 exampaper.cls）
    输入: {questions, header, exam_meta}
    输出: {tex_source, tex_file_path, compile_warnings}

[6] 调 Skill D: Overleaf 集成
    输入: {overleaf_project_url, tex_content}
    输出: {pdf_path, compile_log, success}
```

---

## 4. Skill A: OCR → LaTeX（重点设计）

### 4.1 三个 OCR 痛点的针对性设计

#### 痛点 1：手写版（连笔字、涂抹）

**难点分析**：
- 通用 OCR（百度/腾讯通用版）对连笔手写识别率 < 60%
- 涂抹区域直接 OCR 必失败
- 同一手写者不同题的字迹风格可能不同

**技术方案**（三路并行 + 投票）：

| 通道 | 适用 | 准确率参考 |
|---|---|---|
| **腾讯云手写体识别** | 中等清晰度手写 | 85-92% |
| **PaddleOCR + 手写模型** | 离线场景 | 70-80% |
| **LLM 视觉模型（GPT-4V/Claude Vision）** | 严重涂抹/低清晰 | 60-75%（语义推断强） |

**Pipeline**：
```
原图 → 预处理（去噪/超分/二值化）→ 通道 A（腾讯云手写）→ 结果 R1
                                  → 通道 B（PaddleOCR 手写）→ 结果 R2
                                  → 通道 C（LLM 视觉）→ 结果 R3
                                  → 投票器（编辑距离相似度匹配）
                                  → 共识结果 + 不一致题目标记 needs_review
```

#### 痛点 2：拍照版（模糊不清）

**难点分析**：
- 手机拍摄：光照不均、抖动模糊、透视畸变
- 经常有阴影遮挡关键公式
- 学生手可能出现在画面边缘

**预处理流水线**（必须前置）：
```python
def preprocess(image_path):
    img = cv2.imread(image_path)
    img = deskew(img)                   # 倾斜校正
    img = adaptive_threshold(img)        # 自适应二值化（处理光照不均）
    img = remove_shadow(img)             # 去除阴影
    img = super_resolution(img)          # Real-ESRGAN 超分（处理模糊）
    img = perspective_correct(img)       # 透视校正
    return img
```

**OCR 选型**：
- 印刷体为主 → 腾讯云通用 OCR / 百度 OCR（95%+）
- 仍有手写成分 → 走痛点 1 的 pipeline

#### 痛点 3：公式符号、电路结构还原

**难点分析**：
- 公式：印刷体可用 Mathpix（99%+），手写公式可用 LaTeX-OCR 开源模型
- 电路：没有通用 OCR 方案，目前只能用图像占位 + 半自动标注
- 图表：同上

**分流方案**：
```
图片预处理 → 版面分析（layout detection）
              ├─ 公式区域 → Mathpix / LaTeX-OCR → 输出 LaTeX 公式
              ├─ 文字区域 → 走手写/印刷体 OCR pipeline
              ├─ 电路区域 → 输出 \includegraphics 占位 + TikZ/circuitikz 还原（可选）
              └─ 图表区域 → 输出 \includegraphics 占位 + 图题
              → 合并为完整 LaTeX
```

**电路图处理策略**（务实方案）：
- **首选**：保留原图 `\includegraphics[width=...]{原图路径}` + 图题，LaTeX 渲染原图
- **进阶**：用 circuitikz 还原基本电路（学生可在 Skill 输出后人工微调）
- **不承诺**：100% 自动还原电路细节（标注"这是电路题，请人工核对原图"）

### 4.2 输入输出契约

**输入**：
```json
{
  "images": ["C:/.../q1.jpg", "C:/.../q2.png"],
  "pipeline_strategy": "auto | handwriting_first | photo_first | formula_first",
  "ocr_providers": {
    "handwriting": "tencent | paddleocr_local | llm_vision",
    "printed": "tencent | baidu | paddleocr_local",
    "formula": "mathpix | latex-ocr | tencent_ocr"
  },
  "output_format": "latex | json | both",
  "language": "zh",
  "preprocess": {
    "enabled": true,
    "super_resolution": true,
    "shadow_removal": true
  },
  "mathpix_credentials_path": "C:/.../mathpix.json"
}
```

**输出**：
```json
{
  "questions": [
    {
      "number": 1,
      "type": "calculation",
      "stem_latex": "设 $X \\sim N(\\mu, \\sigma^2)$，求 $P(|X-\\mu|<2\\sigma)$",
      "options": null,
      "answer": null,
      "source_image": "C:/.../q1.jpg",
      "ocr_confidence": 0.91,
      "ocr_channels_used": ["tencent", "mathpix"],
      "needs_review": false,
      "review_reason": null,
      "original_image_position": "line_3"
    },
    {
      "number": 2,
      "type": "calculation",
      "stem_latex": "求如图所示电路的等效电阻 \\includegraphics[width=0.4\\textwidth]{q2_circuit.png}",
      "has_image": true,
      "image_path": "C:/.../q2_circuit.png",
      "ocr_confidence": 0.65,
      "ocr_channels_used": ["tencent"],
      "needs_review": true,
      "review_reason": "电路图为图像占位，建议人工核对原图"
    }
  ],
  "ocr_summary": {
    "total_pages": 4,
    "avg_confidence": 0.83,
    "low_confidence_questions": [2, 5],
    "formula_recognition_count": 7,
    "image_placeholder_count": 2
  },
  "warnings": [
    "第 2 题为电路图，已保留原图占位",
    "第 5 题公式识别置信度 0.62，建议核对 Mathpix 输出"
  ]
}
```

### 4.3 OCR Provider 插拔机制

```yaml
# ocr-providers.yaml（学生本地配置）
providers:
  handwriting:
    active: tencent
    available: [tencent, paddleocr_local, llm_vision]
    credentials:
      tencent:
        secret_id: ENV.TENCENT_SECRET_ID
        secret_key: ENV.TENCENT_SECRET_KEY
      paddleocr_local:
        model_path: ~/.local/paddleocr/handwriting/
  printed:
    active: tencent
    available: [tencent, baidu, paddleocr_local]
  formula:
    active: mathpix
    credentials:
      mathpix:
        app_id: ENV.MATHPIX_APP_ID
        app_key: ENV.MATHPIX_APP_KEY
```

Skill 启动时读这份配置，按 `active` 选择 provider。学生可临时切换或自部署。

---

## 5. Skill B: 考点预测器（核心）

### 5.1 输入输出契约

**输入**：
```json
{
  "ppt_paths": ["C:/.../ch1.pptx", "C:/.../ch3.pptx"],
  "past_exam_questions": [
    {"number": 1, "stem_latex": "...", "type": "choice", "source": "2023_final"}
  ],
  "review_materials": ["C:/.../notes.md"],
  "focus_topics": ["第三章"],
  "config": {
    "algorithm": "tfidf_textrank_llm | pure_llm",
    "top_keywords_n": 20,
    "predicted_questions_n": 15
  }
}
```

**输出**：
```json
{
  "keywords": [
    {
      "term": "中心极限定理",
      "weight": 0.92,
      "source": "PPT:ch3.pptx (12次) + 真题:2023 (3次)",
      "recency_trend": "stable"
    }
  ],
  "predicted_questions": [
    {
      "id": "P1",
      "type": "calculation",
      "topic": "假设检验",
      "weight": 0.88,
      "rationale": "近 3 年出现 5 次，PPT 第三章重点",
      "sample_question_latex": "设总体 X ~ N(μ, σ²)，...",
      "expected_difficulty": "medium",
      "covers_keywords": ["原假设", "p-value", "显著性水平"]
    }
  ],
  "topic_distribution": {"choice": 5, "fill": 3, "short_answer": 4, "calculation": 3},
  "explainability": {
    "method": "TF-IDF 提取候选词 → TextRank 计算关联度 → 共现矩阵加权 → 本地 LLM 归纳题型",
    "evidence_sources": ["ch3.pptx", "2023_final.tex", "2022_final.tex"]
  }
}
```

### 5.2 算法思路（借鉴而非照搬）

1. **文本预处理**：从 PPT 提取纯文本（python-pptx），从 LaTeX/JSON 提取题干
2. **TF-IDF 关键词提取**：候选词按文档频率加权
3. **TextRank 关联度计算**：用共现图计算关键词关联强度
4. **真题权重叠加**：近 N 年真题中出现的关键词额外加权
5. **LLM 归纳**：把"关键词 + 关联度 + 真题样本"喂给本地 LLM，生成预测题 + 解释
6. **不训练**：所有"算法"都是经典 NLP 工具的组合，零模型训练

---

## 6. Skill C: LaTeX 试卷生成（直接对接 exampaper.cls）

### 6.1 设计决策

**不复造模板**，直接引入 `sunflower070203/SEU-Test-Latex-Template` 作为 submodule。学生也可以替换为自己的模板。

### 6.2 数据 → 命令映射

Skill C 内部维护一张映射表，把 JSON 题库转为 `\examquestion` / `\examsection` 等命令：

```python
def render_question(q):
    if q["type"] == "choice":
        return render_choice(q)
    elif q["type"] == "fill":
        return "\\underline{\\hspace{2cm}}" * q["blank_count"]
    elif q["type"] == "calculation":
        return render_calculation(q)
    elif q["type"] == "image_question":
        return f"\\examfigure[{q['image_width']}]{{{q['image_caption']}}}{{{q['image_path']}}}"

def render_exam(q_list, header):
    sections = []
    for group in group_by_type(q_list):
        section_title = f"{type_to_chinese(group.type)}(本题共 {len(group)} 小题，满分 {group.total_score} 分)"
        sections.append(f"\\examsection{{{section_title}}}")
        sections.append("\\begin{examquestions}[7cm]")
        for q in group:
            sections.append(render_question(q))
        sections.append("\\end{examquestions}")
    return wrap_with_exampaper(header, sections)
```

### 6.3 输入输出契约

**输入**：
```json
{
  "questions": [
    {"number": 1, "type": "choice", "stem_latex": "...", "options": [...], "score": 5}
  ],
  "header": {
    "course_name": "概率论与数理统计",
    "course_code": "ST203",
    "semester": "2025-2026-2",
    "major": "信息工程",
    "exam_type": "闭卷",
    "duration_minutes": 120,
    "exam_title": "期末考试(A 卷)"
  },
  "answer_sheet_included": false,
  "two_column_layout": false
}
```

**输出**：
```json
{
  "tex_source": "\\documentclass[12pt,a4paper]{exampaper}\n...",
  "tex_file_path": "C:/.../predicted_exam_2026.tex",
  "compile_required_packages": ["ctex", "amsmath", "graphicx"],
  "warnings": []
}
```

---

## 7. Skill D: Overleaf 集成

复用现有 `overleaf-webbridge-check` skill 的浏览器桥能力，扩展命令集支持"上传 + 编译 + 等待 + 下载"。

**输入**：
```json
{
  "overleaf_project_url": "https://www.overleaf.com/project/abc123",
  "tex_content": "...",
  "compile_strategy": "replace_main | upload_new_file"
}
```

**输出**：
```json
{
  "pdf_path": "C:/.../predicted_exam_2026.pdf",
  "compile_log": "...",
  "compile_success": true,
  "overleaf_url": "..."
}
```

---

## 8. 风险与权衡

| 风险 | 缓解措施 |
|---|---|
| **OCR 准确率不稳定** | 三路并行 + 投票 + `needs_review` 标记；电路图明确告知占位 |
| **手写公式识别率低** | Mathpix（印刷体）+ LaTeX-OCR（手写）+ 学生人工校对 |
| **考点预测不准** | 输出 `rationale` 字段，让 LLM 解释预测依据 |
| **LaTeX 模板不兼容** | 模板以 submodule 引入，学生可替换 |
| **Overleaf 编译失败** | 返回完整编译日志；学生可手动排查 |
| **多 Agent 适配** | SKILL.md 共用，agents/*.yaml 分发 |
| **API 凭据管理** | OCR provider 配置走本地文件 + 环境变量，不入 Git |

---

## 9. 实施计划

| 阶段 | 内容 | 预估时间 | 前置依赖 |
|---|---|---|---|
| **Phase 1** | GitHub repo 骨架 + SKILL.md + README | 0.5 天 | 用户确认命名 |
| **Phase 2** | Skill C 对接 exampaper.cls | 1 天 | 模板引入 |
| **Phase 3** | Skill B 算法实现（TF-IDF + TextRank + LLM 集成） | 1-2 天 | Phase 1 完成 |
| **Phase 4** | Skill A OCR pipeline（先实现腾讯云手写 + Mathpix） | 2 天 | OCR provider 选型 + 凭据 |
| **Phase 5** | Skill D Overleaf 集成 | 0.5 天 | overleaf-webbridge-check 现状确认 |
| **Phase 6** | WorkBuddy / Codex / Claude Code 三端适配 | 1 天 | SKILL.md 稳定 |
| **Phase 7** | 示例数据 + CI + 文档完善 | 1 天 | Phase 1-6 完成 |

**关键里程碑**：Phase 3 完成即可演示"PPT → 预测考点 → 出 .tex → 编译 PDF"，OCR 部分先用占位符。

---

## 10. 待用户确认事项

1. **仓库名与路径**：建议 `sunflower070203/SEU-review-helper`，确认？
2. **LaTeX 模板引入方式**：Git submodule 还是直接复制 `exampaper.cls` 到 `templates/`？
3. **OCR provider 优先级**：先实现腾讯云手写 + Mathpix，可接受？是否需要 PaddleOCR 本地兜底？
4. **电路图处理深度**：图像占位就够，还是要做 circuitikz 还原？
5. **首发支持的 Agent**：Codex / WorkBuddy / Claude Code 三端都做，还是先做其中一个？
6. **凭据管理**：OCR API 凭据走本地配置文件 + 环境变量，确认？
7. **MIT 许可证**：与参考项目一致？

---

## 11. 评审检查清单（自检）

- [x] 是否明确了项目定位与差异化？
- [x] 是否针对三个 OCR 痛点给出了具体技术方案？
- [x] 是否保证"决策权在学生本地"？
- [x] 是否避免了"端到端黑盒"？
- [x] Skill 契约是否清晰、可独立实现？
- [x] 多 Agent 兼容方案是否清晰？
- [x] 实施计划是否可分阶段交付？
- [x] 风险是否被识别并有缓解措施？
