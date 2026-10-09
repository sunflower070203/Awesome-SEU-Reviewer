#!/usr/bin/env python3
"""生成「信号与系统」试卷插图的 SVG 源文件，并转换为 LaTeX 可用的 PDF。

为什么要用脚本而不是直接手写 SVG：
  - 所有图共用同一套坐标系统一风格（轴、刻度、标注格式）
  - 参数一改全图重生成，不用逐个文件改
  - 同时产出 SVG（可预览/可编辑）与 PDF（LaTeX 用）

依赖：
    pip install svglib reportlab

用法：
    python scripts/latex/make_signal_figures.py --outdir figures/signal
"""

import argparse
from pathlib import Path

W, H = 340, 180
OX, OY = 52, 128          # 原点
XLEN, YLEN = 250, 98      # 轴长
STROKE = "#111"
AXIS_W = 1.0
CURVE_W = 1.6


def t2x(t, tmax=2.5):
    return OX + XLEN * t / tmax


def v2y(v, vmax=1.0):
    return OY - YLEN * v / vmax


def head(w, h):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" '
            'width="{}" height="{}">').format(w, h, w, h)


def tail():
    return "</svg>"


def axis(tmax=2.5, vmax=1.0, xlabel="t", ylabel=None):
    """画坐标轴 + 箭头。"""
    x_end, y_end = OX + XLEN, OY - YLEN
    parts = [
        '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="{}"/>'.format(
            OX, OY, x_end + 8, OY, STROKE, AXIS_W),
        '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="{}"/>'.format(
            OX, OY, OX, y_end - 8, STROKE, AXIS_W),
        # 箭头
        '<path d="M{} {} l-4 -3 l4 3 l-4 3 z" fill="{}"/>'.format(x_end + 8, OY, STROKE),
        '<path d="M{} {} l-3 -4 l3 4 l3 -4 z" fill="{}"/>'.format(OX, y_end - 8, STROKE),
        '<text x="{}" y="{}" font-size="12" font-family="serif">0</text>'.format(OX - 10, OY + 14),
        '<text x="{}" y="{}" font-size="12" font-family="serif">{}</text>'.format(
            x_end + 10, OY + 16, xlabel),
    ]
    if ylabel:
        parts.append('<text x="{}" y="{}" font-size="12" font-family="serif">{}</text>'.format(
            OX + 8, y_end - 12, ylabel))
    return "".join(parts)


def xtick(t, label=None):
    x = t2x(t)
    lab = label if label is not None else ("{}".format(t).rstrip("0").rstrip("."))
    return ('<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="{s}" stroke-width="{w}"/>'
            '<text x="{x}" y="{ty}" font-size="12" font-family="serif" text-anchor="middle">{lab}</text>'
            ).format(x=x, y0=OY, y1=OY + 4, s=STROKE, w=AXIS_W, ty=OY + 16, lab=lab)


def ytick(v, label=None):
    y = v2y(v)
    lab = label if label is not None else ("{}".format(v).rstrip("0").rstrip("."))
    return ('<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{s}" stroke-width="{w}"/>'
            '<text x="{tx}" y="{y4}" font-size="12" font-family="serif" text-anchor="end">{lab}</text>'
            ).format(x0=OX - 4, x1=OX, y=y, s=STROKE, w=AXIS_W,
                     tx=OX - 7, y4=y + 4, lab=lab)


def vline(t, label=""):
    x = t2x(t)
    parts = ['<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="{s}" stroke-width="0.7" '
             'stroke-dasharray="4,3"/>'.format(x=x, y0=OY, y1=OY - YLEN, s=STROKE)]
    if label:
        parts.append('<text x="{}" y="{}" font-size="12" font-family="serif" '
                     'text-anchor="middle">{}</text>'.format(x, OY + 16, label))
    return "".join(parts)


def curve(points, tmax=2.5, vmax=1.0):
    pts = " ".join("{:.1f},{:.1f}".format(t2x(t, tmax), v2y(v, vmax)) for t, v in points)
    return ('<polyline points="{}" fill="none" stroke="{}" stroke-width="{}"/>'
            ).format(pts, STROKE, CURVE_W)


# ---------------------------------------------------------------- 各图定义

def fig1():
    """图 1：单个三角脉冲 f(t)，峰在 t=1 处。"""
    s = [head(W, H), axis(), xtick(1), xtick(2), ytick(1)]
    s.append(curve([(0, 0), (1, 1), (2, 0)]))
    s.append(tail())
    return "".join(s)


def fig2():
    """图 2：周期 T=2 的三角波。"""
    s = [head(W, H), axis(tmax=5.0), xtick(1), xtick(2), xtick(3), xtick(4), ytick(1)]
    pts = []
    for k in range(3):
        base = 2 * k
        pts += [(base, 0), (base + 1, 1), (base + 2, 0)]
    s.append(curve(pts, tmax=5.0))
    s.append('<text x="{}" y="{}" font-size="12" font-family="serif" '
             'font-style="italic">…</text>'.format(OX + 228, OY + 16))
    s.append('<text x="{}" y="{}" font-size="12" font-family="serif" '
             'font-style="italic">…</text>'.format(OX - 22, OY + 16))
    s.append(tail())
    return "".join(s)


def fig3():
    """图 3：梯形脉冲（-2→-1 上升，-1→1 平台，1→2 下降）。"""
    s = [head(W, H), axis(tmax=2.5, vmax=1.0), ytick(1)]
    for t, lab in ((-2, "-2"), (-1, "-1"), (0, "0"), (1, "1"), (2, "2")):
        s.append('<text x="{:.1f}" y="{}" font-size="12" font-family="serif" '
                 'text-anchor="middle">{}</text>'.format(t2x(t), OY + 16, lab))
        s.append('<line x1="{:.1f}" y1="{}" x2="{:.1f}" y2="{}" stroke="{}" '
                 'stroke-width="{}"/>'.format(t2x(t), OY, t2x(t), OY + 4, STROKE, AXIS_W))
    s.append(curve([(0, 0), (0.5, 0.0), (1.0, 1.0), (3.5, 1.0), (4.0, 0.0), (5.0, 0.0)]))
    s.append(tail())
    return "".join(s)


def fig4():
    """图 4：f(t) 在 [-1,2] 上先升后降的折线。"""
    s = [head(W, H), axis(tmax=3.0, vmax=2.0), ytick(2)]
    for t, lab in ((-1, "-1"), (0, "0"), (1, "1"), (2, "2")):
        s.append('<text x="{:.1f}" y="{}" font-size="12" font-family="serif" '
                 'text-anchor="middle">{}</text>'.format(t2x(t, 3.0), OY + 16, lab))
        s.append('<line x1="{:.1f}" y1="{}" x2="{:.1f}" y2="{}" stroke="{}" '
                 'stroke-width="{}"/>'.format(t2x(t, 3.0), OY, t2x(t, 3.0), OY + 4, STROKE, AXIS_W))
    s.append(vline(1, "1"))
    s.append(curve([(0.0, 0), (1.0, 2), (1.5, 2), (2.5, 0), (3.0, 0)], tmax=3.0, vmax=2.0))
    s.append(tail())
    return "".join(s)


def fig5a():
    """图 5(a)：低通幅频特性。"""
    s = [head(W, H), axis(tmax=3.0, vmax=1.0), ytick(1)]
    for t, lab in ((-3, "-3"), (-2, "-2"), (-1, "-1"), (0, "0"), (1, "1"), (2, "2"), (3, "3")):
        s.append('<text x="{:.1f}" y="{}" font-size="12" font-family="serif" '
                 'text-anchor="middle">{}</text>'.format(t2x(t, 3.0) if False else 0, OY + 16, ""))
    # 用自定义刻度（横轴为 ω）
    xs = []
    for w in (-2, -1, 1, 2):
        x = OX + XLEN * (w + 3) / 6.0
        xs.append('<line x1="{:.1f}" y1="{}" x2="{:.1f}" y2="{}" stroke="{}" '
                  'stroke-width="{}"/>'.format(x, OY, x, OY + 4, STROKE, AXIS_W))
        xs.append('<text x="{:.1f}" y="{}" font-size="12" font-family="serif" '
                  'text-anchor="middle">{}</text>'.format(x, OY + 16, w))
    xs.append('<text x="{:.1f}" y="{}" font-size="12" font-family="serif">0</text>'
              .format(OX - 10, OY + 16))
    xs.append('<text x="{}" y="{}" font-size="12" font-family="serif">ω</text>'
              .format(OX + XLEN + 10, OY + 16))
    xs.append('<text x="{}" y="{}" font-size="12" font-family="serif">H(jω)</text>'
              .format(OX + 8, OY - YLEN - 2))
    s.extend(xs)
    # 矩形低通
    def w2x(w):
        return OX + XLEN * (w + 3) / 6.0
    s.append('<polyline points="{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f}" '
             'fill="none" stroke="{}" stroke-width="{}"/>'.format(
                 w2x(-2), OY, w2x(-2), v2y(1), w2x(2), v2y(1), w2x(2), OY, STROKE, CURVE_W))
    s.append(tail())
    return "".join(s)


def fig5b():
    """图 5(b)：周期性矩形脉冲。"""
    s = [head(W, H), axis(tmax=5.0), xtick(1), xtick(2), xtick(3), xtick(4), ytick(1)]
    for k in range(4):
        x0 = t2x(k * 1.5 - 1.5, 5.0)
        x1 = t2x(k * 1.5 - 0.9, 5.0)
        s.append('<polyline points="{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f}" '
                 'fill="none" stroke="{}" stroke-width="{}"/>'.format(
                     x0, OY, x0, v2y(1), x1, v2y(1), x1, OY, STROKE, CURVE_W))
    s.append('<text x="{}" y="{}" font-size="12" font-family="serif" font-style="italic">…</text>'
             .format(OX + 236, OY + 16))
    s.append(tail())
    return "".join(s)


def fig6():
    """图 6：单三角脉冲（叠加示意）。"""
    s = [head(W, H), axis(tmax=2.5, vmax=1.0), xtick(1), xtick(2), ytick(1)]
    s.append(curve([(0, 0), (0.8, 1), (1.8, 0), (2.2, 0)]))
    s.append(tail())
    return "".join(s)


def fig7a():
    """图 7(a)：带限信号频谱 E(jω)，三角谱。"""
    s = [head(W, H), axis(tmax=3.0, vmax=1.0), ytick(1)]
    def w2x(w):
        return OX + XLEN * (w + 3) / 6.0
    for w in (-2, -1, 1, 2):
        s.append('<line x1="{:.1f}" y1="{}" x2="{:.1f}" y2="{}" stroke="{}" stroke-width="{}"/>'
                 .format(w2x(w), OY, w2x(w), OY + 4, STROKE, AXIS_W))
        s.append('<text x="{:.1f}" y="{}" font-size="12" font-family="serif" '
                 'text-anchor="middle">{}</text>'.format(w2x(w), OY + 16, w))
    s.append('<text x="{:.1f}" y="{}" font-size="12" font-family="serif">0</text>'
             .format(OX - 10, OY + 16))
    s.append('<text x="{}" y="{}" font-size="12" font-family="serif">ω</text>'
             .format(OX + XLEN + 10, OY + 16))
    s.append('<text x="{}" y="{}" font-size="12" font-family="serif">E(jω)</text>'
             .format(OX + 8, OY - YLEN - 2))
    s.append('<polyline points="{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f}" fill="none" '
             'stroke="{}" stroke-width="{}"/>'.format(
                 w2x(-2), OY, w2x(0), v2y(1), w2x(2), OY, STROKE, CURVE_W))
    s.append(tail())
    return "".join(s)


def fig7b():
    """图 7(b)：系统框图 e(t) → [×cos10t] → A → [×cos30t] → B → H(jω) → C。"""
    w, h = 520, 140
    s = [head(w, h)]
    y = 70
    boxes = [
        (40, "e(t)", None),
        (110, "×", "cos10t"),
        (200, "A", None),
        (250, "×", "cos30t"),
        (340, "B", None),
        (400, "H(jω)", None),
        (480, "C", None),
    ]
    # 输入箭头
    s.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1"/>'
             .format(10, y, 96, y, STROKE))
    s.append('<text x="{}" y="{}" font-size="12" font-family="serif">e(t)</text>'
             .format(12, y - 10))
    # 乘法器圆圈
    for cx, lab, sub in ((100, "×", "cos10t"), (240, "×", "cos30t")):
        s.append('<circle cx="{}" cy="{}" r="11" fill="none" stroke="{}" stroke-width="1"/>'
                 .format(cx, y, STROKE))
        s.append('<text x="{}" y="{}" font-size="12" font-family="serif" '
                 'text-anchor="middle">{}</text>'.format(cx, y + 4, lab))
        s.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1"/>'
                 .format(cx, y - 11, cx, y - 34, STROKE))
        s.append('<text x="{}" y="{}" font-size="12" font-family="serif" '
                 'text-anchor="middle">{}</text>'.format(cx, y - 40, sub))
    # 滤波器方框
    s.append('<rect x="{}" y="{}" width="{}" height="{}" fill="none" stroke="{}" '
             'stroke-width="1"/>'.format(375, y - 20, 62, 40, STROKE))
    s.append('<text x="{}" y="{}" font-size="12" font-family="serif" '
             'text-anchor="middle">H(jω)</text>'.format(406, y + 5))
    # 连线与节点
    segs = [(111, 229), (251, 375), (437, 520)]
    for x0, x1 in segs:
        s.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1"/>'
                 .format(x0, y, x1, y, STROKE))
    for x, lab in ((170, "A"), (312, "B"), (480, "C")):
        s.append('<circle cx="{}" cy="{}" r="2.4" fill="{}"/>'.format(x, y, STROKE))
        s.append('<text x="{}" y="{}" font-size="12" font-family="serif" '
                 'text-anchor="middle">{}</text>'.format(x, y - 10, lab))
    s.append(tail())
    return "".join(s)


FIGURES = {
    "fig1-triangle-pulse": fig1,
    "fig2-periodic-triangle": fig2,
    "fig3-trapezoid": fig3,
    "fig4-piecewise": fig4,
    "fig5a-lpf-magnitude": fig5a,
    "fig5b-periodic-rect": fig5b,
    "fig6-pulse": fig6,
    "fig7a-spectrum": fig7a,
    "fig7b-system-block": fig7b,
}


def main():
    ap = argparse.ArgumentParser(description="生成试卷插图（SVG + PDF）")
    ap.add_argument("--outdir", default="figures/signal")
    ap.add_argument("--svg-only", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for name, fn in FIGURES.items():
        svg_path = outdir / (name + ".svg")
        svg_path.write_text(fn(), encoding="utf-8")
        line = "  {}  ({} bytes)".format(svg_path, svg_path.stat().st_size)

        if not args.svg_only:
            try:
                from svglib.svglib import svg2rlg
                from reportlab.graphics import renderPDF
                drawing = svg2rlg(str(svg_path))
                pdf_path = outdir / (name + ".pdf")
                renderPDF.drawToFile(drawing, str(pdf_path))
                line += "  ->  {} ".format(pdf_path)
            except Exception as e:  # noqa: BLE001
                line += "  [PDF 转换失败: {}]".format(e)
        print(line)


if __name__ == "__main__":
    main()
