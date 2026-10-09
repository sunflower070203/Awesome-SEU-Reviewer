# templates/ — LaTeX 试卷模板

本目录内容来自 **[sunflower070203/SEU-Test-Latex-Template](https://github.com/sunflower070203/SEU-Test-Latex-Template)**（MIT 许可）。

## 文件清单

| 文件 | 说明 |
|---|---|
| `exampaper.cls` | 自定义文档类：A4/12pt、正文宋体、栏目标题黑体、左侧竖排密封线、自动中文大题序号、页脚「试卷名 共 X 页 第 Y 页」 |
| `latexmkrc` | latexmk 配置（指定 XeLaTeX） |
| `LICENSE.upstream` | 上游 MIT 许可证原文 |

## 为什么用「直接复制」而非 submodule

目标用户是学生，clone 本仓库后应**开箱可用**。submodule 要求 `git clone --recursive`，容易漏掉导致模板缺失。直接复制省一次心智负担。

代价是上游更新不会自动同步——见下节手动同步方式。

## 同步上游更新

```bash
git clone --depth 1 https://github.com/sunflower070203/SEU-Test-Latex-Template.git /tmp/upstream
cp /tmp/upstream/exampaper.cls templates/exampaper.cls
```

## 换成自己的模板

本 Skill 不绑定特定模板。替换方式：

1. 把你的 `.cls` 或 `.tex` 模板放进本目录
2. 改 `scripts/latex/exampaper_adapter.py` 的 `render_*` 函数，映射到你的模板命令
3. 或保留本 Skill 的 `questions` JSON 中间格式，只替换渲染层

## 编译要求

| 要求 | 说明 |
|---|---|
| **编译器** | **必须 XeLaTeX**（或 LuaLaTeX）。pdfLaTeX 会报 `CTeX fontset 'fandol' is unavailable` |
| **编译遍数** | **两遍**（页脚总页数由 lastpage 提供，第二遍才正确） |
| **字体集** | 默认自动检测（Windows→windows，macOS→mac，Linux→fandol）；可显式指定 `\documentclass[fontset=fandol]{exampaper}` |
| **Overleaf** | 上传后须在 Settings → Compiler 切为 XeLaTeX |

## 命令速查

| 命令 | 说明 |
|---|---|
| `\examsection{栏目标题}` | 大题标题，自动加「一、」「二、」并重置小题号 |
| `\examquestion` | 小题编号（自动 1. 2. 3.…） |
| `\begin{examquestions}[7cm] … \end{examquestions}` | 小题区。参数是 `\parskip`（段间距）。⚠️ **不要用它留答题空间**：留白会错落在第一题之前，且最后一题之后不留白。改用每题后 `\par\vspace{...}`，详见 `references/question-types.md` |
| `\begin{examproblem} … \end{examproblem}` | 无编号的单个大题 |
| `\examfigure[0.6\textwidth]{图题}{图片路径}` | 插图并自动编号 |
| `\examfield[宽度]{项目名}{内容}` | 抬头信息栏一项 |
| `\examscoretable[N]` | 评分表，N = 大题数 |
| `\examtitle{…}` / `\examname{…}` | 试卷大标题 / 页脚试卷名 |
| `\examsidebarfalse` | 关闭左侧密封线 |
