#!/usr/bin/env python3
"""
exampaper_adapter.py — Skill C: 把 questions JSON 渲染为 exampaper.cls 格式的 .tex

用法：
    python exampaper_adapter.py --input exam.json --output paper.tex
    python exampaper_adapter.py --input exam.json          # 输出到 stdout
    python exampaper_adapter.py < exam.json > paper.tex

输入 JSON：
    {
      "header": {
        "school_name": "东南大学",
        "exam_title": "东南大学试卷（A 卷）",
        "course_name": "概率论与数理统计",
        "course_code": "ST203",
        "semester": "2025-2026-2",
        "major": "信息工程",
        "exam_type": "闭卷",
        "duration_minutes": 120
      },
      "questions": [
        {"number": 1, "type": "choice", "stem_latex": "...",
         "options": [{"label": "A", "latex": "..."}], "score": 4},
        {"number": 2, "type": "calculation", "stem_latex": "...", "score": 10}
      ],
      "options": {
        "include_score_table": true,
        "sidebar_seal_line": true,
        "fontset": null
      }
    }

兼容说明：header 也可写作 exam_meta（与 assets/exam-config.example.json 对齐）。
"""

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

# 题型 → 中文栏目标题
TYPE_TITLES = {
    "choice": "单项选择题",
    "fill": "填空题",
    "calculation": "计算题",
    "short_answer": "简答题",
    "proof": "证明题",
    "image_question": "应用题",
    "circuit_question": "电路题",
}

# 题型 → 答题空间（None 表示不需要额外留白）
ANSWER_SPACE = {
    "choice": None,
    "fill": None,
    "calculation": "7cm",
    "short_answer": "10cm",
    "proof": "8cm",
    "image_question": "6cm",
    "circuit_question": "6cm",
}

# 抬头信息栏字段：(header 键, 显示名, 下划线宽度)
INFO_FIELDS = [
    ("course_name", "课程名称", "3.4cm"),
    ("course_code", "课程代码", "2.2cm"),
    ("semester", "考试学期", "1.8cm"),
    ("major", "适用专业", "4.4cm"),
    ("exam_type", "考试形式", "2.0cm"),
    ("duration_minutes", "考试时长", "1.9cm"),
]


def render_title(header):
    title = header.get("exam_title")
    if not title:
        school = header.get("school_name", "")
        title = f"{school}试卷" if school else "试卷"
    return f"\\examtitle{{{title}}}"


def render_exam_type(value):
    """'闭卷' → '闭\\hspace{0.5em}卷'；其它形式原样输出。"""
    text = value or "闭卷"
    if text == "闭卷":
        return "闭\\hspace{0.5em}卷"
    if text == "开卷":
        return "开\\hspace{0.5em}卷"
    return text


def render_duration(minutes):
    if not minutes:
        return ""
    return f"{minutes}\\hspace{{0.4em}}分钟"


def render_info_bar(header):
    """抬头信息栏：3 个字段一行，共两行。"""
    rendered = []
    for key, label, width in INFO_FIELDS:
        if key == "exam_type":
            value = render_exam_type(header.get(key))
        elif key == "duration_minutes":
            value = render_duration(header.get(key))
        else:
            value = header.get(key, "")
        rendered.append((label, value, width))

    def line(items):
        parts = [f"  \\examfield[{w}]{{{label}}}{{{value}}}" for label, value, w in items]
        return "\\hspace{0.4em}%\n".join(parts)

    return (
        "\\begin{center}\n"
        f"{line(rendered[:3])}\\\\[0.4em]\n"
        f"{line(rendered[3:])}\n"
        "\\end{center}"
    )


def section_title(type_key, group):
    title = TYPE_TITLES.get(type_key, type_key)
    n = len(group)
    scores = [q.get("score") for q in group if q.get("score")]
    if len(scores) == n and n > 0:
        if len(set(scores)) == 1:
            return f"{title}（本题共 {n} 小题，每小题 {scores[0]} 分，满分 {sum(scores)} 分）"
        return f"{title}（本题共 {n} 小题，满分 {sum(scores)} 分）"
    return f"{title}（本题共 {n} 小题）"


def render_choice_options(q):
    """选项串，以 \\qquad 分隔，供另起一行使用（不内联在题干尾部）。"""
    options = q.get("options") or []
    if not options:
        return ""
    parts = []
    for o in options:
        parts.append(o["label"] + ".\\ " + o["latex"])
    return " \\qquad ".join(parts)


def render_question(q, type_key):
    stem = (q.get("stem_latex") or "").strip()
    lines = []

    if type_key == "choice":
        lines.append(f"  \\examquestion {stem}")
        suffix = render_choice_options(q)
        if suffix:
            lines.append("")          # 空行 => \par：选项与题干分成两段，不内联
            lines.append(f"  {suffix}")
    elif q.get("has_image") or q.get("image_path"):
        lines.append(f"  \\examquestion {stem}")
        img = q.get("image_path", "")
        cap = q.get("image_caption", "图")
        width = q.get("image_width", "0.6\\textwidth")
        lines.append("")
        lines.append(f"  \\examfigure[{width}]{{{cap}}}{{{img}}}")
    else:
        lines.append(f"  \\examquestion {stem}")

    return "\n".join(lines)


def render_section(type_key, group):
    """渲染一个大题栏（\\examsection + examquestions）。

    答题留白用模板的 \\examanswerspace{...}（每题之后调用一次），而不是
    \\begin{examquestions}[...] 的参数。后者是 \\parskip（段间距），只在段落
    **之间**生效，会造成「留白跑到第一题之前、最后一题之后反而没有留白」
    （2026-10-09 实测）。故有留白需求的题型用 [0pt] 关掉 \\parskip，逐题显式留白。
    """
    space = ANSWER_SPACE.get(type_key)
    lines = [f"\\examsection{{{section_title(type_key, group)}}}"]
    lines.append("\\begin{examquestions}[0pt]" if space else "\\begin{examquestions}")
    for q in group:
        lines.append(render_question(q, type_key))
        if space:
            lines.append(f"  \\examanswerspace{{{space}}}")
    lines.append("\\end{examquestions}")
    return "\n".join(lines)


def group_questions(questions):
    """按题型分组，保留题型首次出现的顺序。"""
    groups = OrderedDict()
    for q in questions:
        key = q.get("type", "calculation")
        groups.setdefault(key, []).append(q)
    return groups


def render_exam(data):
    header = data.get("header") or data.get("exam_meta") or {}
    questions = data.get("questions") or []
    options = data.get("options") or {}

    if not questions:
        raise ValueError("questions 为空，无法生成试卷")

    groups = group_questions(questions)

    parts = []
    fontset = options.get("fontset")
    class_opts = "[12pt,a4paper]" if not fontset else f"[12pt,a4paper,fontset={fontset}]"
    parts.append(f"\\documentclass{class_opts}{{exampaper}}")
    parts.append(f"\\examname{{{header.get('exam_name') or header.get('course_name') or '试卷'}}}")
    if options.get("sidebar_seal_line") is False:
        parts.append("\\examsidebarfalse")
    parts.append("")
    parts.append("\\begin{document}")
    parts.append("")
    parts.append(render_title(header))
    parts.append("")
    parts.append("\\vspace{0.8em}")
    parts.append("")
    parts.append(render_info_bar(header))

    if options.get("include_score_table", True):
        parts.append("")
        parts.append("\\vspace{0.8em}")
        parts.append("")
        parts.append(f"\\examscoretable[{len(groups)}]")

    for type_key, group in groups.items():
        parts.append("")
        parts.append("\\vspace{0.6em}")
        parts.append("")
        parts.append(render_section(type_key, group))

    parts.append("")
    parts.append("\\end{document}")
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description="questions JSON → exampaper.cls .tex")
    parser.add_argument("--input", help="输入 JSON 路径（缺省从 stdin 读取）")
    parser.add_argument("--output", help="输出 .tex 路径（缺省写到 stdout）")
    args = parser.parse_args()

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    tex = render_exam(data)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(tex)
        print(f"written: {out_path}", file=sys.stderr)
    else:
        sys.stdout.write(tex)


if __name__ == "__main__":
    main()
