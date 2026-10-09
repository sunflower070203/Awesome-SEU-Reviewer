#!/usr/bin/env python3
"""predictor.py — Skill B：从历年试卷预测考点。

输入：多份试卷的 questions（与 Skill A 的输出格式对齐）
输出：按信号强度排序的考点簇 + 依据链

信号强度 = 0.75 × 跨卷重复度 + 0.25 × 位置稳定性

设计依据见 docs/dataset-observations.md：
  - 三份同课程试卷中，填空题 9 题里有 8 题完全相同 → 重复考察是主信号
  - 小样本（2-4 份）下 TF-IDF 的 IDF 失效 → 不采用统计词权
  - 题号位置稳定（第 4 题连年考绝对值积分）→ 位置是辅助强特征

用法：
    python predictor.py --input pool.json --output predictions.json
    python predictor.py --input pool.json --threshold 0.4 --format text
"""

import argparse
import json
import re
import sys
from collections import Counter

DEFAULT_THRESHOLD = 0.5
WEIGHT_REPEAT = 0.75
WEIGHT_POSITION = 0.25

# 输入模式：试卷与课件不是互斥关系，按实际提供的资料判定
MODE_EXAM_ONLY = "exam_only"
MODE_PPT_ONLY = "ppt_only"
MODE_HYBRID = "hybrid"
MODE_INSUFFICIENT = "insufficient"

_CJK = r"[\u4e00-\u9fff]"
_TOKEN_RE = re.compile(_CJK + r"|[A-Za-z]+|\d+")


def normalize(stem):
    """去掉 LaTeX 排版噪声，保留语义信息（含命令名，如 iint / arctan）。"""
    s = re.sub(r"\\([A-Za-z]+)", r" \1 ", stem)
    s = re.sub(r"[${}\\^_&]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(stem):
    """切 token：中文按字、英文与数字按词。"""
    return set(_TOKEN_RE.findall(normalize(stem)))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cluster_questions(exams, threshold):
    """把跨卷的相似题聚成簇（贪心，与簇内任一成员相似即归入）。"""
    clusters = []
    for exam in exams:
        for q in exam["questions"]:
            item = {
                "exam": exam["id"],
                "number": q["number"],
                "type": q.get("type", "unknown"),
                "stem": q["stem_latex"],
                "tokens": tokens(q["stem_latex"]),
            }
            best, best_sim = None, 0.0
            for c in clusters:
                sim = max(jaccard(item["tokens"], m["tokens"]) for m in c["members"])
                if sim > best_sim:
                    best, best_sim = c, sim
            if best is not None and best_sim >= threshold:
                best["members"].append(item)
            else:
                clusters.append({"members": [item]})
    return clusters


def build_rationale(repeat, n_exams, exams_seen, stability, positions):
    parts = ["在 {}/{} 份试卷中出现".format(round(repeat * n_exams), n_exams)]
    if stability >= 0.6 and positions:
        (qtype, number), count = max(positions.items(), key=lambda kv: kv[1])
        if count > 1:
            parts.append("{} 次位于第 {} 题（{}）".format(count, number, qtype))
    if repeat == 1.0:
        parts.append("未缺席，判为必考")
    elif repeat >= 0.6:
        parts.append("高频，判为高可能")
    else:
        parts.append("低频，仅作参考")
    return "；".join(parts)


def score_cluster(cluster, n_exams):
    members = cluster["members"]
    exams_seen = {m["exam"] for m in members}
    repeat = len(exams_seen) / n_exams

    positions = Counter((m["type"], m["number"]) for m in members)
    top_count = positions.most_common(1)[0][1]
    stability = top_count / len(members)

    score = WEIGHT_REPEAT * repeat + WEIGHT_POSITION * stability

    return {
        "score": round(score, 3),
        "repeat": round(repeat, 3),
        "exams_seen": sorted(exams_seen),
        "position_stability": round(stability, 3),
        "positions": {"{}#{}".format(t, n): c for (t, n), c in positions.items()},
        "n_members": len(members),
        "type": members[0]["type"],
        "rationale": build_rationale(repeat, n_exams, sorted(exams_seen), stability, positions),
        "stem_samples": [m["stem"] for m in members],
    }


def detect_mode(data):
    """按实际提供的资料判定模式——试卷与课件不是二选一的关系。

    用户可能只有试卷、只有课件，或两者都有；此处只做判定，不做取舍。
    """
    exams = data.get("exams") or []
    has_ppt = bool(data.get("ppt_paths") or data.get("ppt_text"))
    if len(exams) >= 2 and has_ppt:
        return MODE_HYBRID
    if len(exams) >= 2:
        return MODE_EXAM_ONLY
    if has_ppt:
        return MODE_PPT_ONLY
    return MODE_INSUFFICIENT


def predict(data, threshold=DEFAULT_THRESHOLD):
    mode = detect_mode(data)
    if mode == MODE_INSUFFICIENT:
        raise ValueError(
            "输入资料不足：至少需要 2 份历年试卷，或 1 份课件。"
            "试卷与课件并不互斥，提供任意一种即可（两者都有时会尝试融合）。"
        )
    if mode == MODE_PPT_ONLY:
        raise ValueError(
            "当前版本仅实现「试卷模式」。检测到你只提供了课件（无试卷）——"
            "请补充至少 2 份历年试卷；仅课件模式（知识点覆盖面分析）尚未实现。"
        )

    exams = data["exams"]
    n = len(exams)
    clusters = cluster_questions(exams, threshold)
    scored = [score_cluster(c, n) for c in clusters]
    scored.sort(key=lambda x: (-x["score"], -x["n_members"]))
    for i, p in enumerate(scored, 1):
        p["rank"] = i

    warnings = []
    if mode == MODE_HYBRID:
        warnings.append("hybrid 模式尚未实现，本次仅按试卷重复度计算，课件未参与打分")

    return {
        "mode": mode,
        "n_exams": n,
        "exam_ids": [e["id"] for e in exams],
        "threshold": threshold,
        "warnings": warnings,
        "predictions": scored,
    }


def format_text(result):
    lines = [
        "试卷数：{}（{}）".format(result["n_exams"], ", ".join(result["exam_ids"])),
        "相似度阈值：{}".format(result["threshold"]),
        "",
    ]
    for p in result["predictions"]:
        lines.append("[{}] 信号 {:.3f}  {}".format(p["rank"], p["score"], p["type"]))
        lines.append("     依据：{}".format(p["rationale"]))
        lines.append("     样例：{}".format(p["stem_samples"][0][:70]))
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="预测考点（Skill B）")
    ap.add_argument("--input", required=True, help="试卷池 JSON")
    ap.add_argument("--output", help="输出 JSON（缺省写到 stdout）")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="聚类相似度阈值")
    ap.add_argument("--format", choices=["json", "text"], default="json")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    result = predict(data, args.threshold)

    if args.format == "text":
        rendered = format_text(result)
    else:
        rendered = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as f:
            f.write(rendered)
        print("written: " + args.output, file=sys.stderr)
    else:
        sys.stdout.write(rendered + "\n")


if __name__ == "__main__":
    main()
