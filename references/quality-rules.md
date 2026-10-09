# 题目质量规则（quality-rules）

> Skill B（考点预测器）和 Skill C（LaTeX 生成）必须遵守的质量规则。

## 题目内容规则

### 1. 可追溯性

- 每道预测题必须对应至少 1 个 keywords 中的关键词
- `covers_keywords` 字段非空
- `rationale` 必须引用具体证据（PPT 章节/年份）

### 2. 可解性

- 计算题必须包含完整可解的条件
- 选择题必须给出 4 个选项，且只有一个明显正确
- 填空题必须有明确上下文，无歧义

### 3. 难度标注

- `easy`：直接套公式或回忆定义
- `medium`：需 1-2 步推理
- `hard`：需综合多个知识点或多步推导

### 4. 学科正确性

- 公式 LaTeX 必须可编译
- 物理题单位必须标注
- 化学方程式必须配平

## 题型分布规则

### 推荐分布（理工科期末）

| 题型 | 占比 | 单题分值 |
|---|---|---|
| 选择题 | 20% | 3-5 分 |
| 填空题 | 20% | 4-5 分 |
| 计算题 | 40% | 10-15 分 |
| 简答题 | 20% | 10-15 分 |

### 难度分布

| 难度 | 占比 |
|---|---|
| easy | 30% |
| medium | 50% |
| hard | 20% |

## LaTeX 渲染规则

### 1. 编译必须通过

- `.tex` 文件必须可用 XeLaTeX 编译无 error
- 警告（warning）允许，但必须在 `warnings` 字段列出
- 字体回退：未指定字体时使用宋体

### 2. 公式正确性

- 行内公式必须用 `$...$`
- 行间公式用 `$$...$$`
- 不允许出现 `\[ ... \]`（部分模板不兼容）
- 复杂公式用 `aligned` 环境

### 3. 排版美观

- 每道大题之间空一行
- 小题之间不空行
- 图题用 `\examfigure`，自动编号
- 长题目自动分页（LaTeX 默认行为）

## 反模式（禁止）

### 内容反模式

- ❌ 生成与考点无关的题目（"凑数题"）
- ❌ 出现答案在题干中的题目
- ❌ 选择题出现"以上都对"、"以上都错"
- ❌ 简答题无评分要点

### LaTeX 反模式

- ❌ 手写题号（"1."、"2."）
- ❌ 用 `$$ ... $$` 嵌套在 `\examquestion` 内
- ❌ 图像题用裸 `\includegraphics` 而非 `\examfigure`
- ❌ 中文/英文混排不切换字体

### 算法反模式

- ❌ 纯随机生成题目（必须有 rationale）
- ❌ 复制往年真题一字不改（必须有变化）
- ❌ 关键词权重无依据（必须有 evidence 来源）

## 校验脚本

`scripts/validate_exam.py` 自动检查：

```bash
python scripts/validate_exam.py \
  --questions output/predicted_questions.json \
  --tex output/predicted_exam.tex \
  --check compile && \
  --check traceability && \
  --check difficulty_distribution
```

校验失败时，Skill 必须把错误列表返回给学生 Agent，由学生 Agent 决定是否修改。
