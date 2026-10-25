#!/usr/bin/env python3
"""summarize.py — 把多个 Agent 的跑测记录汇总成一张对比表。

输入：若干个 results-*.csv（格式见 benchmark/results-template.csv）
输出：Markdown 表格（直接贴到 issue / PR 里）

做法：
  - 同一 Agent 的多轮结果取**中位数**（首跑有冷启动差异，均值会被拉偏）
  - 除绝对值外，还给出「相对最优」的比值，方便一眼看出差距
  - trigger_cases 按 ✅ / ⚠️ / ❌ 计数

用法：
    python scripts/bench/summarize.py benchmark/results-*.csv
    python scripts/bench/summarize.py benchmark/*.csv --format md
"""

import argparse
import csv
import statistics
import sys
from pathlib import Path

NUMERIC = [
    ("total_tokens", "总 token"),
    ("input_tokens", "输入 token"),
    ("output_tokens", "输出 token"),
    ("peak_context_k", "峰值上下文 (k)"),
    ("wall_time_min", "耗时 (min)"),
    ("human_interventions", "人工干预次数"),
    ("pages", "页数"),
    ("questions_correct", "识别正确题数"),
    ("figures_good", "合格图数"),
]


def load(paths):
    rows = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            print("skip (not found): " + str(p), file=sys.stderr)
            continue
        with open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                r["_src"] = p.name
                rows.append(r)
    return rows


def to_num(v):
    try:
        f = float(str(v).strip())
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


def median_of(values):
    vals = [v for v in values if v is not None]
    return statistics.median(vals) if vals else None


def fmt(v):
    if v is None:
        return "—"
    return "{:.1f}".format(v) if isinstance(v, float) and v != int(v) else str(int(v))


def count_trigger(s):
    """统计触发用例的 ✅ / ⚠️ / ❌。"""
    if not s:
        return {"ok": 0, "warn": 0, "fail": 0, "total": 0}
    ok = s.count("✅")
    warn = s.count("⚠️") + s.count("⚠")
    fail = s.count("❌")
    return {"ok": ok, "warn": warn, "fail": fail, "total": ok + warn + fail}


def aggregate(rows):
    """按 agent 聚合，多轮取中位数。"""
    by_agent = {}
    for r in rows:
        name = (r.get("agent") or "unknown").strip()
        by_agent.setdefault(name, []).append(r)

    out = []
    for name, rs in by_agent.items():
        item = {"agent": name, "runs": len(rs)}
        for key, _label in NUMERIC:
            item[key] = median_of([to_num(r.get(key)) for r in rs])
        # 触发统计（取最后一轮，避免重复计数同一批用例）
        last = rs[-1].get("trigger_cases") or ""
        item["trigger"] = count_trigger(last)
        item["compile_ok"] = sum(1 for r in rs if str(r.get("compile_ok", "")).strip() in ("1", "true", "True", "yes"))
        out.append(item)
    out.sort(key=lambda x: (x["total_tokens"] or 1e18))
    return out


def render_md(items):
    if not items:
        return "（没有数据）"

    best_tokens = min([i["total_tokens"] for i in items if i["total_tokens"]] or [None])
    lines = []

    lines.append("## Token 消耗\n")
    head = "| Agent | 轮数 | 总 token | 相对最优 | 输入 | 输出 | 峰值上下文 |"
    sep = "|---|:-:|---:|---:|---:|---:|---:|"
    lines += [head, sep]
    for i in items:
        ratio = ""
        if i["total_tokens"] and best_tokens:
            ratio = "×{:.2f}".format(i["total_tokens"] / best_tokens)
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            i["agent"], i["runs"], fmt(i["total_tokens"]), ratio or "—",
            fmt(i["input_tokens"]), fmt(i["output_tokens"]), fmt(i["peak_context_k"])))

    lines.append("\n## 过程指标\n")
    lines.append("| Agent | 耗时(min) | 人工干预 | 页数 | 识别正确 | 合格图 | 编译通过 |")
    lines.append("|---|--:|--:|--:|--:|--:|:-:|")
    for i in items:
        lines.append("| {} | {} | {} | {} | {} | {} | {}/{} |".format(
            i["agent"], fmt(i["wall_time_min"]), fmt(i["human_interventions"]),
            fmt(i["pages"]), fmt(i["questions_correct"]), fmt(i["figures_good"]),
            i["compile_ok"], i["runs"]))

    lines.append("\n## 触发效果\n")
    lines.append("| Agent | 正确触发 | 有瑕疵 | 失败 | 命中率 |")
    lines.append("|---|--:|--:|--:|--:|")
    for i in items:
        t = i["trigger"]
        rate = "{:.0%}".format(t["ok"] / t["total"]) if t["total"] else "—"
        lines.append("| {} | {} | {} | {} | {} |".format(
            i["agent"], t["ok"], t["warn"], t["fail"], rate))

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="汇总多 Agent 跑测结果")
    ap.add_argument("csv", nargs="+", help="results-*.csv")
    ap.add_argument("--format", choices=["md", "csv"], default="md")
    args = ap.parse_args()

    rows = load(args.csv)
    if not rows:
        sys.exit("没有读到任何数据")

    items = aggregate(rows)

    if args.format == "csv":
        cols = ["agent", "runs"] + [k for k, _ in NUMERIC]
        w = csv.writer(sys.stdout)
        w.writerow(cols)
        for i in items:
            w.writerow([i.get(c) for c in cols])
    else:
        print(render_md(items))
        print("\n---")
        print("说明：同一 Agent 多轮取**中位数**；「相对最优」= 该 Agent / 最低总 token。")
        print("读表提醒：token 口径（OpenAI 分块 vs Claude 面积）差异极大，跨 Agent 比较前请确认一致。")


if __name__ == "__main__":
    main()
