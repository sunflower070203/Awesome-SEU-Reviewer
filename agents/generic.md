# 通用 Agent 适配说明

本 Skill 不绑定特定 Agent。**任何能读 Markdown 指令、能执行 Python、且具备视觉能力的 Agent 都可以用。**

## 安装

把仓库放到 Agent 的 skills 目录即可（目录名建议 `seu-review-helper`）：

| Agent | 推荐位置 | 说明 |
|---|---|---|
| Claude Code | `~/.claude/skills/seu-review-helper/` | 读 `SKILL.md` 的 YAML frontmatter 自动识别 |
| Codex | `~/.codex/skills/seu-review-helper/` | 另见 `agents/openai.yaml` |
| WorkBuddy | 由 SkillManage 导入 | 另见 `agents/workbuddy.yaml` |
| Cursor / Cline / 其他 | 项目内 `skills/` 或系统提示引用 | 直接引用 `SKILL.md` |
| 纯命令行 / 本地脚本 | 不适用 | 直接用 `scripts/` 下的脚本（见下） |

## 触发机制

`SKILL.md` 顶部有 YAML frontmatter：

```yaml
name: seu-review-helper
description: |
  从历年真题（PDF/照片/扫描件）与课件生成复习预测试卷。……
  触发场景：「复习」「考点预测」「期末试卷」「真题整理」……
```

**支持 frontmatter 的 Agent**（Claude Code、WorkBuddy 等）会按 `description` 自动匹配触发。
**不支持的**（部分 IDE 插件），把 `description` 里的触发词抄进系统提示即可。

## 能力要求与降级

| 能力 | 用途 | 缺失时的降级方案 |
|---|---|---|
| **视觉识别** | 读试卷 PNG 产出题目 JSON | ① 试 PDF 文本层（可能是乱码）；② 让学生贴文字；③ 接腾讯云 OCR / Mathpix（`assets/ocr-providers.example.yaml`） |
| 执行 Python | 渲染、打分、生成 .tex | 必需，无法降级 |
| 联网 | Overleaf 编译 | 可跳过——输出 `.tex` 让学生自己上传 |

**注意**：本 Skill **不要求** Agent 有视觉能力也能用——`render.py` 会给出提示（见 `manifest.json` 的 `recommended` 字段），Agent 应据此选择路径。

## 纯脚本用法（不使用 Agent 时）

四个环节都能单独跑：

```bash
# ① 渲染
python scripts/ocr/render.py --input exam.pdf --outdir .tmp-render

# ② 视觉提取 —— 这一步需要「会看图」的东西
#    · 有视觉能力的 Agent：按 assets/prompt-templates/vision-extract.txt 读 PNG
#    · 没有：接外部 OCR，把结果整理成同样格式

# ③ 预测
python scripts/predict/predictor.py --input a.json --input b.json --output candidates.json
python scripts/predict/predictor.py --input a.json --input b.json --merge topics.json --format text

# ④ 生成 LaTeX
python scripts/latex/exampaper_adapter.py --input exam.json --output paper.tex
```

## 额度消耗说明

| 环节 | 消耗 | 说明 |
|---|---|---|
| ① 渲染 | **0** | 本地 Python，秒级 |
| ② 视觉提取 | Agent 视觉额度 | 唯一的大头。**压降办法**：只渲染/识别需要的页（`render.py` 支持单文件输入），跳过空白页与答案页 |
| ③ 预测（统计部分） | **0** | 本地 Python |
| ③ 预测（考点归并） | Agent 文本额度 | 一次归并只需读题号 + 题干摘要，不必读全文 |
| ④ 生成 .tex | **0** | 本地 Python |
| ④ Overleaf 编译 | **0**（API 费用） | 浏览器自动化，不调用付费接口 |

**全流程零外部 API 调用。** 主要成本是视觉识别，且可通过「只处理需要的页面」控制。
