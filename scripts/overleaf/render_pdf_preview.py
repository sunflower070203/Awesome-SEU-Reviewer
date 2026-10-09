#!/usr/bin/env python3
"""把 PDF 渲染为 PNG 预览图（Skill D 辅助工具）。

编译日志只能说明「编译通过」，预览图才能证明「排版正确」。本工具把
Overleaf 编译产物转成逐页 PNG，供 Agent 用 Read 工具肉眼核验。

依赖：
    pip install pypdfium2 pillow

用法：
    python scripts/overleaf/render_pdf_preview.py paper.pdf examples/output/paper
    # → examples/output/paper-p1.png, paper-p2.png ...
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="PDF → 逐页 PNG 预览")
    parser.add_argument("pdf", help="输入 PDF 路径")
    parser.add_argument("prefix", help="输出前缀（生成 <prefix>-p1.png ...）")
    parser.add_argument("--scale", type=float, default=2.0, help="渲染倍率，默认 2.0")
    args = parser.parse_args()

    try:
        import pypdfium2 as pdfium
    except ImportError:
        sys.exit("缺少依赖，请先执行：pip install pypdfium2 pillow")

    pdf = pdfium.PdfDocument(args.pdf)
    print(f"pages: {len(pdf)}")
    for i in range(len(pdf)):
        img = pdf[i].render(scale=args.scale).to_pil()
        out = f"{args.prefix}-p{i + 1}.png"
        img.save(out)
        print(f"saved {out} {img.size}")


if __name__ == "__main__":
    main()
