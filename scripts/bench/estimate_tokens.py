#!/usr/bin/env python3
"""estimate_tokens.py — 估算一次任务大体消耗多少 token。

为什么需要它：多数 Agent 不暴露 token 用量，跨 Agent 对比时缺少共同标尺。
本脚本对「任务输入」与「产物」分别估算，给出可比较的量级。

估算口径（两种主流算法都给出，便于对齐不同 Agent）：
  - openai : 图片按 512×512 分块，每块 170 token，另加 85 基础值
  - claude : 图片按 (宽 × 高) / 750 估算
  文本：中文按 1 字 ≈ 0.9 token，英文/数字按 1 词 ≈ 1.3 token（经验值）

用法：
    python scripts/bench/estimate_tokens.py --images .tmp-render
    python scripts/bench/estimate_tokens.py --text questions.json paper.tex
    python scripts/bench/estimate_tokens.py --summary
"""

import argparse
import math
import re
import sys
from pathlib import Path

TEXT_EXT = {".json", ".tex", ".md", ".txt", ".csv", ".yaml", ".yml", ".py"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def estimate_text(text):
    """文本 token 估算：中文按字、其余按词。"""
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9_]+", text))
    others = max(len(text) - cjk - words, 0)
    return int(cjk * 0.9 + words * 1.3 + others * 0.3), cjk, words


def estimate_image_openai(w, h):
    """OpenAI 分块算法：缩放到 2048 长边内，短边缩到 768，再按 512 分块。"""
    if w > 2048 or h > 2048:
        scale = 2048 / max(w, h)
        w, h = int(w * scale), int(h * scale)
    if min(w, h) > 768:
        scale = 768 / min(w, h)
        w, h = int(w * scale), int(h * scale)
    tiles = math.ceil(w / 512) * math.ceil(h / 512)
    return 85 + 170 * tiles


def estimate_image_claude(w, h):
    return math.ceil(w * h / 750)


def image_size(path):
    """优先用 PIL 读尺寸；没有 PIL 时回退到 PDF 渲染记录。"""
    try:
        from PIL import Image  # noqa: PLC0415
        with Image.open(path) as im:
            return im.size
    except Exception:  # noqa: BLE001
        return None


def collect(paths):
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files.extend(sorted(f for f in p.rglob("*") if f.is_file()))
        elif p.exists():
            files.append(p)
        else:
            print("skip (not found): " + str(p), file=sys.stderr)
    return files


def main():
    ap = argparse.ArgumentParser(description="估算任务的 token 量级")
    ap.add_argument("--images", nargs="*", default=[], help="图片文件或目录")
    ap.add_argument("--text", nargs="*", default=[], help="文本文件或目录")
    args = ap.parse_args()

    if not args.images and not args.text:
        ap.error("至少提供 --images 或 --text")

    total_oai = total_claude = total_text = 0

    imgs = collect(args.images)
    if imgs:
        print("== 图片（视觉识别的主要成本）==")
        for f in imgs:
            if f.suffix.lower() not in IMAGE_EXT:
                continue
            size = image_size(f)
            if not size:
                print("  {:<44} 无法读取尺寸".format(f.name))
                continue
            w, h = size
            o = estimate_image_openai(w, h)
            c = estimate_image_claude(w, h)
            total_oai += o
            total_claude += c
            print("  {:<44} {}x{}  openai≈{:<6} claude≈{}".format(f.name, w, h, o, c))

    txts = collect(args.text)
    if txts:
        print("== 文本（题干、代码、说明）==")
        for f in txts:
            if f.suffix.lower() not in TEXT_EXT:
                continue
            try:
                content = f.read_text(encoding="utf-8")
            except Exception:  # noqa: BLE001
                continue
            t, cjk, words = estimate_text(content)
            total_text += t
            print("  {:<44} {} 字  ≈{} tok".format(f.name, len(content), t))

    print("")
    print("== 合计 ==")
    if imgs:
        print("  图片：openai≈{}  claude≈{}".format(total_oai, total_claude))
    if txts:
        print("  文本：≈{}".format(total_text))
    print("")
    print("  提示：这只是「材料本身」的体量。实际消耗还要加上")
    print("        系统提示 + 技能文档 + 工具返回 + Agent 自己的思考输出，")
    print("        通常是上述数字的 1.5–3 倍。")


if __name__ == "__main__":
    main()
