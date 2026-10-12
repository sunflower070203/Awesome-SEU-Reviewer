#!/usr/bin/env python3
"""preprocess.py — 识别前的图片瘦身（P0 优化）。

为什么需要它（见 docs/efficiency-and-figures.md 的实测）：
  - 图片消耗与分辨率成**平方关系**：4032x3024 的单张照片在 Claude 计费
    口径下是 16 258 token，8 张就是 8.5 万
  - 而课堂投影照片**字大、信息密度低**，长边降到 1600px 完全够识别
  - 照片四周往往还有大片无关区域（桌面、天花板、幕布黑边）

做法：
  1. 用「边缘强度投影」自动找出真正有内容的区域并裁掉四周
     （对拍屏幕、扫描件、手拍纸张都适用，不依赖背景颜色）
  2. 把长边缩放到目标值（默认 1600）
  3. 输出处理后图片 + 报告（省了多少像素）

用法：
    python scripts/ocr/preprocess.py --input photos/ --outdir .tmp-ocr
    python scripts/ocr/preprocess.py --input a.jpg --outdir out --max-side 1400
    python scripts/ocr/preprocess.py --input photos/ --outdir out --no-crop
"""

import argparse
import json
import sys
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
DEFAULT_MAX_SIDE = 1600
EDGE_KEEP = 0.995      # 保留累计边缘强度前 99.5% 的范围
MIN_MARGIN_RATIO = 0.01  # 裁剪后至少保留 1% 边距，避免贴边


def _load_np():
    try:
        import numpy as np  # noqa: PLC0415
        return np
    except ImportError:
        sys.exit("缺少依赖：pip install numpy pillow")


def _load_pil():
    try:
        from PIL import Image  # noqa: PLC0415
        return Image
    except ImportError:
        sys.exit("缺少依赖：pip install pillow")


def content_bbox(img, edge_keep=EDGE_KEEP):
    """用边缘强度的行/列投影找内容边界。

    思路：文字与线条会产生强边缘；四周的桌面、天花板、幕布黑边
    边缘很弱。按累计强度取分位点，截掉两端几乎无内容的条带。
    """
    np = _load_np()
    gray = np.asarray(img.convert("L"), dtype=np.float32)
    # 一阶差分近似梯度
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    edge = np.zeros_like(gray)
    edge[:, :-1] += gx
    edge[:-1, :] += gy

    col = edge.sum(axis=0)
    row = edge.sum(axis=1)
    if col.sum() <= 0 or row.sum() <= 0:
        return (0, 0, img.width, img.height)

    def span(vec, limit):
        cum = np.cumsum(vec) / vec.sum()
        lo = int(np.searchsorted(cum, (1 - limit) / 2))
        hi = int(np.searchsorted(cum, (1 + limit) / 2))
        return max(lo, 0), min(hi, len(vec))

    x0, x1 = span(col, edge_keep)
    y0, y1 = span(row, edge_keep)
    return (x0, y0, x1, y1)


def process_one(path, outdir, max_side, do_crop, quality):
    Image = _load_pil()
    with Image.open(path) as im:
        im = im.convert("RGB")
        w0, h0 = im.size

        if do_crop:
            box = content_bbox(im)
            # 留一点边距
            mx = int((box[2] - box[0]) * MIN_MARGIN_RATIO)
            my = int((box[3] - box[1]) * MIN_MARGIN_RATIO)
            box = (max(box[0] - mx, 0), max(box[1] - my, 0),
                   min(box[2] + mx, w0), min(box[3] + my, h0))
            if (box[2] - box[0]) >= 50 and (box[3] - box[1]) >= 50:
                im = im.crop(box)

        w1, h1 = im.size
        scale = min(1.0, max_side / max(w1, h1)) if max_side else 1.0
        if scale < 1.0:
            im = im.resize((max(int(w1 * scale), 1), max(int(h1 * scale), 1)),
                           Image.LANCZOS)
        w2, h2 = im.size

        out = outdir / path.name
        if out.suffix.lower() in (".jpg", ".jpeg"):
            im.save(out, quality=quality, optimize=True)
        else:
            im.save(out)

    return {
        "source": path.name,
        "orig": [w0, h0],
        "cropped": [w1, h1],
        "final": [w2, h2],
        "out": str(out),
    }


def estimate(rec):
    """按两种主流口径估算 token，便于对比收益。"""
    def claude(w, h):
        return max(int(w * h / 750), 1)

    def openai(w, h):
        import math
        ww, hh = w, h
        if max(ww, hh) > 2048:
            s = 2048 / max(ww, hh)
            ww, hh = int(ww * s), int(hh * s)
        if min(ww, hh) > 768:
            s = 768 / min(ww, hh)
            ww, hh = int(ww * s), int(hh * s)
        return 85 + 170 * math.ceil(ww / 512) * math.ceil(hh / 512)

    o = rec["orig"]; f = rec["final"]
    return {
        "openai_before": openai(*o), "openai_after": openai(*f),
        "claude_before": claude(*o), "claude_after": claude(*f),
    }


def main():
    ap = argparse.ArgumentParser(description="识别前图片瘦身（裁剪 + 缩放）")
    ap.add_argument("--input", required=True, action="append", help="图片/目录，可多次指定")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--max-side", type=int, default=DEFAULT_MAX_SIDE,
                    help="长边目标像素（默认 1600；0 表示不缩放）")
    ap.add_argument("--no-crop", action="store_true", help="跳过自动裁剪")
    ap.add_argument("--quality", type=int, default=88, help="JPEG 质量（默认 88）")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    files = []
    for raw in args.input:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXT))
        elif p.exists():
            files.append(p)
        else:
            print("skip (not found): " + str(p), file=sys.stderr)
    if not files:
        sys.exit("没有可处理的图片")

    records, tot = [], {"openai_before": 0, "openai_after": 0,
                        "claude_before": 0, "claude_after": 0}
    for f in files:
        try:
            rec = process_one(f, outdir, args.max_side, not args.no_crop, args.quality)
        except Exception as e:  # noqa: BLE001
            print("FAILED {}: {}".format(f.name, e), file=sys.stderr)
            continue
        rec.update(estimate(rec))
        records.append(rec)
        for k in tot:
            tot[k] += rec[k]

    manifest = {"outdir": str(outdir), "max_side": args.max_side,
                "cropped": not args.no_crop, "total": tot, "items": records}
    (outdir / "preprocess.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("processed {} image(s) -> {}".format(len(records), outdir))
    for r in records:
        w0, h0 = r["orig"]; w2, h2 = r["final"]
        print("  {:<28} {}x{} x{}x{}  openai {}->{}  claude {}->{}".format(
            r["source"][:28], w0, h0, w2, h2,
            r["openai_before"], r["openai_after"],
            r["claude_before"], r["claude_after"]))
    if tot["claude_before"]:
        drop = 100 * (1 - tot["claude_after"] / tot["claude_before"])
        print("TOTAL: openai {} -> {}   claude {} -> {}  (saved {:.0f}%)".format(
            tot["openai_before"], tot["openai_after"],
            tot["claude_before"], tot["claude_after"], drop))


if __name__ == "__main__":
    main()
