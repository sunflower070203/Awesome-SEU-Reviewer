# 协作上手说明

> 面向：拿到 fork 后要在**多个 Agent 上跑测评**、并按结果优化的人。
> 大约 10 分钟能跑通第一轮。

---

## 1. 这个项目在干嘛（一分钟版）

把「复习」拆成四个可独立调用的能力，由学生本地的 Agent 自主调度：

| | 能力 | 输入 → 输出 |
|---|---|---|
| **A** | 试卷转结构化题目 | PDF/照片 → `questions.json` |
| **B** | 考点预测 | 多份 `questions.json` → 考点清单 + 依据 |
| **C** | 生成 LaTeX 试卷 | `questions.json` → `.tex` |
| **D** | 编译取 PDF | `.tex` → Overleaf → PDF |

**设计前提**：视觉识别和考点归并都由 Agent 自己做，**不调用任何外部 API**。
所以「换一个 Agent 效果差多少」是这类项目的核心问题——这也是你要测的东西。

---

## 2. 环境准备

```bash
git clone <你的 fork 地址> ~/seu-review
cd ~/seu-review
pip install -r requirements.txt
```

**依赖分层**（详见 `requirements.txt` 注释）：

- 核心三个：`pypdfium2`（渲染）、`Pillow`（图片）、`numpy`（预处理）
- `svglib`/`reportlab` 只在 SVG 转 PDF 时用
- **千万别装 `cairosvg`**——Windows 上能装上，但运行时缺 `libcairo` 直接崩

---

## 3. 自检（30 秒，确认环境正常）

```bash
python scripts/ocr/test_preprocess.py      # 应显示 6 tests OK
python scripts/predict/test_predictor.py   # 应显示 21 tests OK
```

两个都过，说明代码完整、依赖齐了。**不过就别往下走，先查环境。**

---

## 4. 跑评测（核心工作）

### 4.1 标准任务

打开 `benchmark/TASK.md`，里面有一份**固定的任务说明和提示词**。要点：

- **同一份输入文件**（别换，否则不可比）
- **同一段提示词**（原文复制，别改写）
- **每个 Agent 跑 3 次取中位数**（首跑有冷启动差异）

### 4.2 记录什么

打开 `benchmark/results-template.csv`，一行一次运行。列的含义：

| 列 | 怎么填 |
|---|---|
| `input_tokens` / `output_tokens` / `total_tokens` | Agent 有 API 用量就直接抄；没有就用下面的估算 |
| `peak_context_k` | 峰值上下文（千 token）。**这个比总量更能解释差异** |
| `human_interventions` | 你需要澄清/纠正几次。**这是隐性成本** |
| `trigger_cases` | 触发用例命中情况，格式见 `benchmark/trigger-cases.md` |
| `questions_correct` | 识别的题目里，人工核对后正确的条数 |

**没有 token 数据时**，用估算器：

```bash
python scripts/bench/estimate_tokens.py --images <图片目录> --text <产物.json> <产物.tex>
```

它会同时给 **OpenAI 分块口径**和 **Claude 面积口径**两个数——因为两者差很多，跨 Agent 比较时必须标明用的是哪个。

### 4.3 触发测试

`benchmark/trigger-cases.md` 里有 **10 条应触发 + 5 条边界 + 5 条不应触发**。

逐条只发那一句话（可带附件），观察：

- 是否**主动加载技能**（而不是等你说"用那个技能"）
- 是否**走对分支**（该渲染却去调 OCR API 算走错）
- 是否**在低置信处停下来**问你

记录格式：`A1✅ A2⚠️走错分支 A3❌ ...`

### 4.4 汇总

跑完把各 Agent 的 CSV 放一起比对。重点看三件事：

1. **token 差的来源**——是读图次数不同？还是峰值上下文不同？
2. **触发失败的共同点**——哪类措辞大家都不认？
3. **质量差异在哪**——公式还原？图表？还是题目切分？

> **拿到数据之后怎么分析、该先改什么、哪些是常见的误判，见
> [`docs/benchmark-playbook.md`](docs/benchmark-playbook.md)**。
> 那篇是这份说明的下半场，别跳过。

---

## 5. 可认领的工作

### ⭐ P1：把 9 个电路图改写成 circuitikz（推荐先做）

**现状**：电路图是手写 SVG 坐标生成的（`scripts/latex/make_circuit_figures.py`），
效果一般——元件符号自绘、布局靠试、正弦波画成了折线。

**已验证**：`examples/output/circuitikz-test.tex` 里的三个样板（共射放大、
稳压管、正弦波形）在 Overleaf 上**编译通过，0 错误**。

**要做的**：照着样板，把 `figures/circuit/` 下的 9 个图重写成 TikZ 代码。

**验收**：重新编译 `examples/output/ec-midterm-2022-23.pdf`，图形明显更规范。

**注意**：`templates/exampaper.cls` 要加 `\usepackage{circuitikz}`。

### 其他

| 任务 | 说明 | 难度 |
|---|---|---|
| Phase 7：多 Agent 实测对比 | 就是你要做的事，见第 4 节 | 中 |
| 仅课件模式（`ppt_only`） | `predictor.py` 里目前直接报错，需要实现 | 中 |
| 图像重绘扩展到其他学科 | 电路图之外（如力学受力图、化学结构式） | 看学科 |

---

## 6. 已知的坑

### 6.1 别提交真实试卷

`.gitignore` 已排除 `pool.json`，但**图片和 PDF 要自己留意**。
试卷有版权，且含个人信息。测试用的样例请自行准备，不要提交。

### 6.2 `.workbuddy/` 别碰

那是本地工作区元数据，已在 `.gitignore` 里。看到它别删、别提交。

### 6.3 Overleaf 自动化的两个怪癖

如果在本地复现 Skill D（Overleaf 编译）：

- **"New project → Existing project (.zip)" 菜单项，`element.click()` 点不动**，
  必须用 CDP 的 `Input.dispatchMouseEvent` 发真实鼠标事件（含 `mouseMoved`）
- **编辑器会进入 offline 状态**——此时 `fill` 改的内容只留在浏览器里，
  编译用的还是服务器上的旧内容。判据是看 PDF 的 `build/<hash>` 有没有变

### 6.4 LaTeX 转义

在 JSON 里写 LaTeX，**换行要写 `\\\\` 而不是 `\\n`**。
后者会变成 LaTeX 的裸 `\n`（未定义命令），编译直接失败。

### 6.5 OpenAI 和 Claude 的 token 口径完全不同

- OpenAI 按 **512×512 分块**：图只要 >1024px 就固定 4 块（765 token），
  **降分辨率不省**，只有减少张数才省
- Claude 按**面积**：`宽×高/750`，降分辨率线性省

测出来的数字不标明口径，跨 Agent 比较就是错的。

---

## 7. 文档索引

| 想知道什么 | 看这个 |
|---|---|
| 整体设计 | `SKILL.md`、`docs/review-helper-architecture.md` |
| 为什么这么设计（数据依据） | `docs/dataset-observations.md` |
| 回测结果（89% 命中） | `docs/backtest-report.md` |
| token 怎么省 | `docs/token-optimization.md`、`docs/efficiency-and-figures.md` |
| 题型规范 | `references/question-types.md` |
| 考点归并的判断准则 | `references/topic-merge.md` |
| 评测套件 | `benchmark/` |
| **拿到数据后怎么分析、怎么优化** | **`docs/benchmark-playbook.md`** |

---

## 8. 提交前

```bash
python scripts/ocr/test_preprocess.py
python scripts/predict/test_predictor.py
```

**两个都过再提交**。改动涉及新功能的话，补上对应测试。
