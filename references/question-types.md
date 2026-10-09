# 题型规范（question-types）

本 Skill 支持的题型与 LaTeX 渲染约定。

## 支持的题型

| 题型 | JSON `type` | LaTeX 命令 | 说明 |
|---|---|---|---|
| 选择题 | `choice` | `\examquestion` + 自定义选项 | 4 个选项，1 个正确答案 |
| 填空题 | `fill` | `\examquestion` + `\underline` | 题干含 `\underline{\hspace{2cm}}` |
| 计算题 | `calculation` | `\examquestion` | 完整数学表达式 |
| 简答题 | `short_answer` | `\examquestion` + `\examquestions[7cm]` | 题后留答题空间 |
| 图像题 | `image_question` | `\examfigure` | 题干含图，图自动编号 |
| 电路题 | `circuit_question` | `\examfigure` + 占位 | 保留原图占位 |

## 题干 LaTeX 规范

### 数学公式

- 行内公式：`$x^2 + y^2 = r^2$`
- 行间公式：`$$x^2 + y^2 = r^2$$`
- **禁止**用 `\[ ... \]`（部分模板兼容性差）

### 物理/化学符号

- 上标：`X^{2+}`、`H_2O`
- 希腊字母：`\alpha`、`\beta`、`\mu`、`\sigma`
- 特殊符号：`\sim`、`\approx`、`\rightarrow`、`\Rightarrow`

### 选择题选项

```latex
\begin{enumerate}[label=\Alph*.]
\item 选项 A 内容
\item 选项 B 内容
\item 选项 C 内容
\item 选项 D 内容
\end{enumerate}
```

### 填空题空位

```latex
\underline{\hspace{2cm}}
```

可叠加表示多个空：
```latex
\underline{\hspace{2cm}}、\underline{\hspace{2cm}}、\underline{\hspace{2cm}}
```

### 电路图占位

```latex
\begin{center}
\includegraphics[width=0.5\textwidth]{figures/circuit_q5.png}
\end{center}
```

学生可在 Skill 输出后替换为 circuitikz 代码或微调原图。

## 题号管理

- `\examsection{栏目标题}` 自动添加"一、"、"二、"、"三、"并把小题号重置为 1
- `\examquestion` 自动输出"1."、"2."、"3."...
- **禁止**手动编号（如"1."、"2."）

## 大题分组规则

| 类型 | 推荐放在 |
|---|---|
| 选择题 | `\examsection{一、选择题...}` |
| 填空题 | `\examsection{二、填空题...}` |
| 计算题 | `\examsection{三、计算题...}` |
| 简答题 | `\examsection{四、简答题...}` |

## 分值标注

每个 `\examsection{...}` 的标题必须包含分值信息：

```latex
\examsection{选择题(本题共 5 小题，每小题 4 分，满分 20 分)}
```

## 答题空间

- 选择题、填空题：不需要答题空间
- 计算题：建议 `\begin{examquestions}[7cm]`
- 简答题：建议 `\begin{examquestions}[10cm]`
