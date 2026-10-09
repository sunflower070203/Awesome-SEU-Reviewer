#!/usr/bin/env python3
"""render.py — Skill A 第一步：把 PDF / 图片渲染为规范化 PNG。

为什么需要这一步（见 docs/dataset-observations.md 的实测结论）：
  - 真实试卷 PDF 的文本层可能是**乱码**（CID 字形索引，非 Unicode）
  - 也可能是**纯扫描件**（完全没有文本层）
  - 但渲染成图片后，视觉模型能准确还原公式、分式、求和号

所以本 Skill 的统一入口是「先渲染成图片」，文本层只作参考、不作依赖。

渲染档位（--profile）：
    quality   2.0x  默认。识别质量优先，手拍件/复杂公式最稳
    balanced  1.5x  折中
    fast      1.0x  省 token（Claude 类可省 ~75%），电子版 PDF 足够

    注：OpenAI 类模型按 512px 分块计费，2.0x 与 1.5x 落在同一档，
    只有降到 1.0x 才省钱。详见 docs/token-optimization.md。
    **默认取 quality**——质量优先，降档请显式指定。

依赖：
    pip install pypdfium2 pillow

用法：
    python render.py --input exam.pdf --outdir .tmp-render                 # 默认高质量
    python render.py --input exam.pdf --outdir .tmp-render --profile fast  # 省 token
    python render.py --input scans/ --outdir .tmp-render                   # 目录批量
    python render.py --input page1.jpg --outdir .tmp-render --scale 1.5    # 自定义倍率
"""

import argparse
import json
import sys
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

PROFILES = {
    "quality": 2.0,   # 默认：识别质量优先
    "balanced": 1.5,
    "fast": 1.0,
}
DEFAULT_PROFILE = "quality"
DEFAULT_SCALE = PROFILES[DEFAULT_PROFILE]


def _load_pdfium():
    try:
        import pypdfium2  # noqa: PLC0415
    except ImportError:
        sys.exit("缺少依赖：pip install pypdfium2 pillow")
    return pypdfium2


def render_pdf(path, outdir, scale):
    pdfium = _load_pdfium()
    pdf = pdfium.PdfDocument(str(path))
    stem = path.stem
    pages = []
    for i, page in enumerate(pdf):
        img = page.render(scale=scale).to_pil()
        out = outdir / "{}-p{:02d}.png".format(stem, i + 1)
        img.save(out)
        try:
            text_chars = len(page.get_textpage().get_text_range())
        except Exception:
            text_chars = -1
        pages.append({
            "page": i + 1,
            "file": out.name,
            "width": img.size[0],
            "height": img.size[1],
            "text_chars": text_chars,
        })
    return {"source": path.name, "kind": "pdf", "pages": pages}


def render_image(path, outdir, scale):
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        sys.exit("缺少依赖：pip install pillow")
    img = Image.open(path)
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    out = outdir / "{}.png".format(path.stem)
    img.save(out)
    return {"source": path.name, "kind": "image", "pages": [{
        "page": 1, "file": out.name,
        "width": img.size[0], "height": img.size[1], "text_chars": 0,
    }]}


def assess(entry):
    """给出识别路径建议。文本层只作参考——实测中它既可能缺失，也可能是乱码。"""
    notes = []
    if entry["kind"] == "pdf":
        chars = [p["text_chars"] for p in entry["pages"]]
        if all(c == 0 for c in chars):
            notes.append("无文本层（纯扫描件），必须走视觉识别")
        elif all(c >= 0 for c in chars):
            notes.append("存在文本层，但实测可能是 CID 乱码——建议仍以视觉识别为准")
    entry["recommended"] = "vision"
    entry["notes"] = notes
    return entry


def main():
    ap = argparse.ArgumentParser(description="Skill A: PDF/图片 → 规范化 PNG")
    ap.add_argument("--input", required=True, help="PDF、图片或目录")
    ap.add_argument("--outdir", required=True, help="输出目录")
    ap.add_argument("--scale", type=float, help="自定义渲染倍率（覆盖 --profile）")
    ap.add_argument("--profile", choices=list(PROFILES), default=DEFAULT_PROFILE,
                    help="渲染档位：quality=2.0（默认）/ balanced=1.5 / fast=1.0")
    args = ap.parse_args()
    scale = args.scale if args.scale else PROFILES[args.profile]

    src = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if src.is_dir():
        files = sorted(p for p in src.iterdir() if p.suffix.lower() in IMAGE_EXT | {".pdf"})
    else:
        files = [src]

    if not files:
        sys.exit("没有可处理的文件：" + str(src))

    entries = []
    for f in files:
        if f.suffix.lower() == ".pdf":
            entries.append(assess(render_pdf(f, outdir, scale)))
        elif f.suffix.lower() in IMAGE_EXT:
            entries.append(assess(render_image(f, outdir, scale)))
        else:
            print("skipped (unsupported): " + f.name, file=sys.stderr)

    manifest = {"outdir": str(outdir), "scale": scale,
                "profile": args.profile if not args.scale else "custom",
                "sources": entries}
    mpath = outdir / "manifest.json"
    with open(mpath, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, ensure_ascii=False, indent=2)

    total_pages = sum(len(e["pages"]) for e in entries)
    print("rendered: {} source(s), {} page(s) -> {}".format(len(entries), total_pages, outdir))
    print("manifest: " + str(mpath))


if __name__ == "__main__":
    main()
