#!/usr/bin/env python3
"""生成「电子电路基础（模电）」期中试卷的电路插图（SVG 源 + PDF）。

绘图约定（所有图统一）：
  - 导线：黑色 1.2px；元件符号同色
  - 文字标注：12px 衬线体（与 exampaper 正文一致）
  - 坐标系：各图独立视口，元素按左上角绝对定位

输出：
  figures/circuit/*.svg   —— 可预览、可编辑
  figures/circuit/*.pdf   —— LaTeX \\includegraphics 用
"""

import argparse
from pathlib import Path

S = "#111"          # 主色
W = 1.4             # 线宽
F = 'font-family="serif" font-size="13"'


def head(w, h):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" '
            'width="{}" height="{}">').format(w, h, w, h)


def line(x1, y1, x2, y2, w=W):
    return '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="{}"/>'.format(
        x1, y1, x2, y2, S, w)


def polyline(pts, w=W, close=False):
    d = " ".join("{},{}".format(x, y) for x, y in pts)
    tag = "polygon" if close else "polyline"
    fill = S if close else "none"
    return '<{} points="{}" fill="{}" stroke="{}" stroke-width="{}"/>'.format(
        tag, d, fill, S, w)


def rect(x, y, w, h, fill="none"):
    return '<rect x="{}" y="{}" width="{}" height="{}" fill="{}" stroke="{}" stroke-width="{}"/>'.format(
        x, y, w, h, fill, S, W)


def circle(cx, cy, r, fill="none"):
    return '<circle cx="{}" cy="{}" r="{}" fill="{}" stroke="{}" stroke-width="{}"/>'.format(
        cx, cy, r, fill, S, W)


def text(x, y, s, anchor="start", size=13, style=""):
    """绘制标注，自动识别 LaTeX 风格的下标。

    支持 `$R_C$`、`$R_{B1}$`、`$V_{DD}$` 这类写法——因为 svglib 不支持
    tspan 的 baseline-shift，下标用独立小字元素手工偏移，保证 SVG 与
    PDF 表现一致。

    Sizing note: 粗略按 0.56em 估宽，够用即可，不追求精确对齐。
    """
    import re as _re
    core = s.strip()
    if core.startswith("$") and core.endswith("$") and len(core) > 2:
        core = core[1:-1]
    m = _re.match(r"^([^_]+)_\{?([^}]+)\}?$", core)
    if m:
        main, sub_ = m.group(1), m.group(2)
        ss = max(int(size * 0.7), 8)
        main_w = len(main) * size * 0.56
        sub_w = len(sub_) * ss * 0.56
        if anchor == "middle":
            x0 = x - (main_w + sub_w) / 2
        elif anchor == "end":
            x0 = x - (main_w + sub_w)
        else:
            x0 = x
        return (text(x0, y, main, size=size, style=style) +
                text(x0 + main_w + 0.5, y + size * 0.3, sub_, size=ss, style=style))
    return ('<text x="{}" y="{}" {} text-anchor="{}" font-size="{}" {}>{}</text>'
            ).format(x, y, F, anchor, size, style, core)


def resistor_h(cx, cy, label="", half=18):
    """水平电阻：矩形符号。"""
    parts = [rect(cx - half, cy - 7, half * 2, 14, fill="white")]
    if label:
        parts.append(text(cx, cy - 12, label, anchor="middle"))
    return "".join(parts)


def resistor_v(cx, cy, label="", side="right", half=18):
    parts = [rect(cx - 7, cy - half, 14, half * 2, fill="white")]
    if label:
        if side == "right":
            parts.append(text(cx + 14, cy + 4, label))
        else:
            parts.append(text(cx - 14, cy + 4, label, anchor="end"))
    return "".join(parts)


def cap_h(cx, cy, label=""):
    """水平电容：两条竖线。"""
    parts = [line(cx - 5, cy - 12, cx - 5, cy + 12),
             line(cx + 5, cy - 12, cx + 5, cy + 12)]
    if label:
        parts.append(text(cx, cy - 18, label, anchor="middle"))
    return "".join(parts)


def cap_v(cx, cy, label="", side="right"):
    parts = [line(cx - 12, cy - 5, cx + 12, cy - 5),
             line(cx - 12, cy + 5, cx + 12, cy + 5)]
    if label:
        if side == "right":
            parts.append(text(cx + 18, cy + 4, label))
        else:
            parts.append(text(cx - 18, cy + 4, label, anchor="end"))
    return "".join(parts)


def diode_up(cx, cy, label="", size=11):
    """二极管（阴极在上，指向上）：三角 + 横线。"""
    parts = [polyline([(cx - size, cy + size * 0.9), (cx + size, cy + size * 0.9),
                       (cx, cy - size * 0.6)], close=True),
             line(cx - size, cy - size * 0.6, cx + size, cy - size * 0.6)]
    if label:
        parts.append(text(cx + size + 8, cy + 4, label))
    return "".join(parts)


def zener_down(cx, cy, label="", size=11):
    """稳压管（指向下，带折线阴极）：常用于稳压电路。"""
    parts = [polyline([(cx - size, cy - size * 0.9), (cx + size, cy - size * 0.9),
                       (cx, cy + size * 0.6)], close=True),
             polyline([(cx - size - 5, cy + size * 0.6 + 5),
                       (cx - size, cy + size * 0.6),
                       (cx + size, cy + size * 0.6),
                       (cx + size + 5, cy + size * 0.6 - 5)])]
    if label:
        parts.append(text(cx + size + 10, cy + 4, label))
    return "".join(parts)


def source_circle(cx, cy, label="", r=20, rlabel=""):
    """电压源：圆 + 正负号。"""
    parts = [circle(cx, cy, r), text(cx, cy + 5, label, anchor="middle", size=13)]
    if rlabel:
        parts.append(text(cx, cy - r - 8, rlabel, anchor="middle", size=12))
    return "".join(parts)


def ground(x, y):
    """接地符号。"""
    return (line(x, y, x, y + 10) +
            line(x - 12, y + 10, x + 12, y + 10) +
            line(x - 8, y + 15, x + 8, y + 15) +
            line(x - 4, y + 20, x + 4, y + 20))


def arrow(x1, y1, x2, y2):
    """带箭头的线。"""
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    L, spread = 8, 0.42
    p1 = (x2 - L * math.cos(ang - spread), y2 - L * math.sin(ang - spread))
    p2 = (x2 - L * math.cos(ang + spread), y2 - L * math.sin(ang + spread))
    return line(x1, y1, x2, y2) + polyline([p1, (x2, y2), p2], close=True)


# ---------------------------------------------------------------- 各图

def fig_clamp():
    """图 1(a)：二极管钳位电路。"""
    s = [head(300, 210)]
    s.append(source_circle(60, 120, "v_I", r=20))
    s.append(line(60, 100, 60, 60))
    s.append(line(60, 60, 120, 60))
    s.append(cap_h(140, 60, "C"))
    s.append(line(155, 60, 250, 60))
    s.append(line(250, 60, 250, 170))
    s.append(line(250, 120, 190, 120))
    s.append(rect(160, 108, 30, 24, fill="white"))
    s.append(text(175, 125, "R_L", anchor="middle", size=12))
    s.append(line(160, 120, 60, 120))
    s.append(diode_up(205, 148, ""))
    s.append(line(205, 120, 205, 130))
    s.append(line(205, 160, 205, 170))
    s.append(line(205, 170, 250, 170))
    s.append(text(76, 58, "+", size=14))
    s.append(text(76, 186, "−", size=16))
    s.append(text(258, 66, "+", size=14))
    s.append(text(258, 176, "−", size=16))
    s.append(text(205, 190, "v_o", anchor="middle", size=12))
    s.append("</svg>")
    return "".join(s)


def fig_clamp_wave():
    """图 1(b)：钳位电路的输入正弦波形（用足够多的采样点逼近正弦）。"""
    import math
    s = [head(340, 200)]
    X0, X1, MID = 48, 300, 96
    AMP, CYCLES = 58, 2.5
    s.append(line(30, MID, 322, MID))
    s.append(line(X0, 18, X0, 178))
    pts = []
    for i in range(181):
        x = X0 + (X1 - X0) * i / 180.0
        ph = 2 * math.pi * CYCLES * i / 180.0
        pts.append((x, MID - AMP * math.sin(ph)))
    s.append(polyline(pts))
    s.append(polyline([(322, MID - 4), (330, MID), (322, MID + 4)], close=True))
    s.append(polyline([(X0 - 4, 18), (X0, 10), (X0 + 4, 18)], close=True))
    s.append(text(332, MID + 4, "ωt", size=12))
    s.append(text(X0 - 6, 24, "$v_I$", anchor="end", size=12))
    s.append(line(X0, MID - AMP, 96, MID - AMP, w=0.7))
    s.append(text(100, MID - AMP - 4, "$V_m$", size=12))
    s.append(line(X0, MID + AMP, 96, MID + AMP, w=0.7))
    s.append(text(100, MID + AMP + 14, "$-V_m$", size=12))
    s.append(text(306, 176, "(b)", size=12))
    s.append("</svg>")
    return "".join(s)


def fig_zener():
    """图 2：稳压管电路（两只稳压管串联，接在 20V 电源经 R 之后）。

    稳压管画成标准符号：三角 + 带折线的阴极横杠。
    """
    s = [head(320, 250)]
    LEFT, RIGHT, TOP, BOT = 60, 270, 90, 216

    # 电源
    s.append(circle(LEFT, 155, 24))
    s.append(text(LEFT, 160, "20V", anchor="middle", size=12))
    s.append(line(LEFT, 131, LEFT, TOP))
    s.append(line(LEFT, TOP, 118, TOP))
    s.append(resistor_h(146, TOP, "$R$", half=28))
    s.append(line(174, TOP, RIGHT, TOP))

    # 右侧竖线
    s.append(line(RIGHT, TOP, RIGHT, BOT))
    # 电源下方
    s.append(line(LEFT, 179, LEFT, BOT))
    s.append(line(LEFT, BOT, RIGHT, BOT))

    # 串联的两只稳压管：中间竖线上，自上而下
    MID, Y0, Y1 = 205, 110, 130
    s.append(line(RIGHT, Y1, MID, Y1))
    s.append(circle(RIGHT, Y1, 2.6, fill=S))
    s.append(line(MID, Y1, MID, 138))
    s.append(zener(MID, 152, "$D_1$"))
    s.append(line(MID, 166, MID, 186))
    s.append(zener(MID, 200, "$D_2$"))
    s.append(line(MID, 214, MID, BOT))

    # 输出端
    s.append(line(RIGHT, Y1, 296, Y1))
    s.append(text(300, Y1 - 6, "+", size=13))
    s.append(text(300, BOT + 2, "−", size=15))
    s.append("</svg>")
    return "".join(s)


def zener(cx, cy, label="", size=11):
    """稳压管：三角 + 折线阴极杠（竖直放置，电流自上而下）。"""
    parts = [polyline([(cx - size, cy - size * 0.9), (cx + size, cy - size * 0.9),
                       (cx, cy + size * 0.6)], close=True),
             polyline([(cx - size - 6, cy + size * 0.6 + 6),
                       (cx - size, cy + size * 0.6),
                       (cx + size, cy + size * 0.6),
                       (cx + size + 6, cy + size * 0.6 - 6)])]
    if label:
        parts.append(text(cx + size + 12, cy + 4, label))
    return "".join(parts)


def fig_cmos_amp():
    """图 3：CMOS 集成放大器（T2 为 PMOS 负载，T1 为 NMOS 驱动）。"""
    s = [head(300, 260)]
    # T2（上，PMOS）
    s.append(line(90, 40, 90, 60))
    s.append(line(60, 60, 120, 60))
    s.append(text(150, 45, "$V_{DD}$", size=13))
    s.append(line(90, 60, 90, 72))
    s.append(line(78, 78, 102, 78))
    s.append(line(90, 78, 90, 96))  # T2 沟道示意
    s.append(rect(70, 72, 40, 24, fill="none"))
    s.append(text(140, 90, "$T_2$", size=13))
    # 中间输出节点
    s.append(line(90, 96, 90, 140))
    s.append(line(90, 118, 190, 118))
    s.append(circle(90, 118, 2.6, fill=S))
    s.append(text(200, 122, "$v_o$", size=13))
    s.append(line(190, 118, 190, 160))
    # T1（下，NMOS）
    s.append(rect(70, 140, 40, 24, fill="none"))
    s.append(text(140, 158, "$T_1$", size=13))
    s.append(line(90, 140, 90, 164))
    s.append(line(90, 164, 90, 200))
    s.append(line(60, 176, 78, 176))
    s.append(text(30, 180, "$v_I$", size=13))
    # 接地
    s.append(ground(90, 200))
    s.append("</svg>")
    return "".join(s)


def fig_multistage():
    """图 4：两级放大器交流通路。"""
    s = [head(360, 220)]
    # 信号源
    s.append(source_circle(50, 140, "v_s", r=18))
    s.append(line(50, 122, 50, 100))
    s.append(resistor_v(50, 88, "$R_s$", side="right", half=14))
    s.append(line(50, 74, 50, 60))
    s.append(line(50, 60, 140, 60))
    # T1
    s.append(line(140, 60, 140, 78))
    s.append(polyline([(128, 78), (152, 78), (140, 100)], close=True))
    s.append(line(140, 100, 140, 120))
    s.append(line(140, 108, 118, 108))
    s.append(text(108, 112, "$T_1$", anchor="end", size=13))
    s.append(line(140, 120, 140, 150))
    s.append(line(68, 150, 140, 150))
    s.append(line(68, 140, 68, 160))
    s.append(text(84, 172, "$R_i$", size=12))
    # T2
    s.append(line(140, 60, 210, 60))
    s.append(line(210, 60, 210, 78))
    s.append(polyline([(198, 78), (222, 78), (210, 100)], close=True))
    s.append(text(232, 92, "$T_2$", size=13))
    s.append(line(210, 100, 210, 150))
    # 负载
    s.append(line(210, 60, 280, 60))
    s.append(line(280, 60, 280, 95))
    s.append(resistor_v(280, 110, "$R_L$", side="right", half=15))
    s.append(line(280, 125, 280, 170))
    s.append(line(300, 60, 300, 170))
    s.append(text(320, 120, "$v_o$", size=13))
    s.append(text(310, 75, "+", size=13))
    s.append(text(310, 165, "−", size=14))
    # 公共地
    s.append(line(50, 158, 50, 170))
    s.append(line(50, 170, 280, 170))
    s.append(line(140, 150, 140, 170))
    s.append(line(210, 150, 210, 170))
    s.append(ground(165, 170))
    s.append(text(60, 112, "$v_i$", size=12))
    s.append("</svg>")
    return "".join(s)


def fig_diff():
    """图 5：差分放大电路（带恒流源）。"""
    s = [head(380, 260)]
    # 正电源
    s.append(text(90, 28, "$+6V$", size=13))
    s.append(line(100, 34, 100, 50))
    s.append(line(60, 50, 300, 50))
    # 两侧集电极电阻
    s.append(resistor_v(100, 72, "$R_C$", half=14))
    s.append(resistor_v(240, 72, "$R_C$", half=14))
    s.append(line(100, 86, 100, 110))
    s.append(line(240, 86, 240, 110))
    # 差分对
    s.append(polyline([(88, 110), (112, 110), (100, 132)], close=True))
    s.append(polyline([(228, 110), (252, 110), (240, 132)], close=True))
    s.append(text(120, 126, "$T_1$", size=13))
    s.append(text(272, 126, "$T_2$", size=13))
    s.append(line(100, 132, 100, 150))
    s.append(line(240, 132, 240, 150))
    s.append(line(100, 150, 240, 150))
    # 恒流源 T3
    s.append(line(170, 150, 170, 172))
    s.append(rect(155, 172, 30, 22, fill="none"))
    s.append(text(140, 188, "$T_3$", anchor="end", size=13))
    s.append(line(170, 194, 170, 215))
    s.append(text(120, 230, "$-6V$", size=13))
    # 输入输出
    s.append(line(40, 120, 76, 120))
    s.append(text(28, 112, "$v_{i1}$", anchor="end", size=12))
    s.append(line(264, 120, 310, 120))
    s.append(text(316, 124, "$v_{i2}$", size=12))
    s.append(line(100, 110, 60, 110))
    s.append(text(348, 70, "$v_o$", size=13))
    s.append(line(240, 110, 330, 110))
    s.append("</svg>")
    return "".join(s)


def fig_ce_amp():
    """图 6：共射放大电路（分压偏置 + 射极旁路）。正交布局，横平竖直。"""
    s = [head(420, 300)]
    TOP, BOT = 46, 272          # 电源轨与地轨
    TX, TY, TR = 200, 158, 22   # 三极管圆心与半径

    # 电源轨
    s.append(line(120, TOP, 300, TOP))
    s.append(text(305, TOP + 4, "$V_C=9V$", size=12))
    s.append(text(198, TOP - 8, "+", size=13))

    # 集电极支路：TOP -> R_C -> 三极管
    s.append(line(TX, TOP, TX, 62))
    s.append(resistor_v(TX, 82, "$R_C$", side="right", half=20))
    s.append(line(TX, 102, TX, TY - TR))
    s.append(circle(TX, TY - TR + 2, 2.6, fill=S))

    # 输出支路：三极管集电极 -> C_C -> v_o
    s.append(line(TX, TY - TR + 2, 300, TY - TR + 2))
    s.append(cap_h(322, TY - TR + 2, "$C_C$"))
    s.append(line(337, TY - TR + 2, 395, TY - TR + 2))
    s.append(text(400, TY - TR - 2, "+", size=13))
    s.append(text(400, TY - TR + 34, "−", size=15))
    s.append(text(404, TY - TR + 16, "$v_o$", size=12))

    # 三极管（标准 BJT 符号）
    s.append(circle(TX, TY, TR))
    s.append(line(TX - TR - 1, TY - 12, TX - 4, TY - 3))      # 基极引线
    s.append(line(TX - TR - 1, TY + 12, TX - 4, TY + 3))      # 发射极引线（斜）
    s.append(line(TX - 4, TY - 3, TX - 4, TY - TR))           # 内部竖线
    s.append(line(TX - 4, TY + 3, TX - 4, TY + TR))
    s.append(line(TX - 4, TY - 3, TX - 4, TY + 3))
    # 发射极箭头
    s.append(polyline([(TX - 4, TY + 3), (TX + 6, TY + 8), (TX - 1, TY + 13)], close=True))
    s.append(text(TX + 22, TY + 42, "$T$", size=12))

    # 基极分压（R_B1 / R_B2）+ 输入
    BX = 110
    s.append(line(BX, TOP, BX, 66))
    s.append(resistor_v(BX, 86, "$R_{B1}$", side="left", half=20))
    s.append(line(BX, 106, BX, TY))
    s.append(circle(BX, TY, 2.6, fill=S))
    s.append(line(BX, TY, TX - TR - 1, TY))                    # 到基极
    s.append(line(BX, TY, BX, 196))
    s.append(resistor_v(BX, 216, "$R_{B2}$", side="left", half=20))
    s.append(line(BX, 236, BX, BOT))

    # 输入：v_s -> R_s -> C_B -> 基极节点
    s.append(circle(46, TY, 16))
    s.append(text(46, TY + 5, "$v_s$", anchor="middle", size=11))
    s.append(line(46, TY - 16, 46, TY - 28))
    s.append(resistor_v(46, TY - 44, "$R_s$", side="left", half=14))
    s.append(line(46, TY - 58, 46, TY - 58))
    s.append(line(46, TY - 58, 46, TY - 58))
    s.append(line(46, TY - 58, BX, TY - 58))
    s.append(line(BX, TY - 58, BX, TY - 24))
    s.append(cap_v(BX, TY - 12, "$C_B$", side="left"))
    s.append(line(BX, TY - 6, BX, TY - 6))
    s.append(line(46, TY + 16, 46, BOT))

    # 发射极：R_E1 -> (R_E2 ∥ C_E) -> 地
    EX = TX
    s.append(line(TX - 4, TY + TR, TX, TY + TR))
    s.append(line(EX, TY + TR, EX, 190))
    s.append(resistor_v(EX, 210, "$R_{E1}$", side="right", half=20))
    s.append(line(EX, 230, EX, BOT))
    s.append(circle(EX, 240, 2.6, fill=S))
    s.append(line(EX, 240, 268, 240))
    s.append(resistor_v(268, 216, "$R_{E2}$", side="right", half=20))
    s.append(cap_v(310, 240, "$C_E$", side="right"))
    s.append(line(268, 240, 310, 240))
    s.append(line(268, 196, 268, 240))
    s.append(line(268, 196, EX, 196))
    s.append(line(310, 240, 310, BOT))

    # 地轨
    s.append(line(46, BOT, 310, BOT))
    s.append(ground(EX, BOT))
    s.append("</svg>")
    return "".join(s)


def fig_cmos_gate():
    """图 7：CMOS 复合逻辑门（图 a）。"""
    s = [head(320, 300)]
    # 上拉网络（PMOS 并联）
    s.append(line(80, 30, 80, 45))
    s.append(text(60, 26, "$V_{DD}$", size=13))
    s.append(line(80, 45, 80, 60))
    # PMOS A
    s.append(rect(66, 60, 28, 20, fill="none"))
    s.append(text(100, 74, "$A$", size=12))
    s.append(line(50, 70, 66, 70))
    # PMOS B（并联）
    s.append(line(80, 80, 80, 92))
    s.append(line(46, 92, 114, 92))
    s.append(rect(46, 92, 28, 20, fill="none"))
    s.append(rect(86, 92, 28, 20, fill="none"))
    s.append(text(120, 106, "$B$", size=12))
    s.append(text(140, 106, "$C$", size=12))
    s.append(line(60, 112, 60, 126))
    s.append(line(100, 112, 100, 126))
    s.append(line(60, 126, 100, 126))
    # 输出节点
    s.append(line(100, 126, 170, 126))
    s.append(circle(100, 126, 2.6, fill=S))
    s.append(text(180, 130, "$F$", size=14))
    # 下拉网络（NMOS 串联）
    s.append(line(80, 126, 80, 150))
    s.append(rect(66, 150, 28, 20, fill="none"))
    s.append(text(100, 164, "$A$", size=12))
    s.append(line(80, 170, 80, 186))
    s.append(rect(66, 186, 28, 20, fill="none"))
    s.append(text(100, 200, "$B$", size=12))
    s.append(line(80, 206, 80, 222))
    s.append(rect(66, 222, 28, 20, fill="none"))
    s.append(text(100, 236, "$C$", size=12))
    s.append(line(80, 242, 80, 258))
    s.append(ground(80, 258))
    # 输入标记
    s.append(text(30, 74, "$A$", size=12))
    s.append(text(30, 106, "$B$", size=12))
    s.append(text(158, 106, "$C$", size=12))
    s.append(line(114, 136, 150, 136))
    s.append(line(150, 136, 150, 106))
    s.append("</svg>")
    return "".join(s)


def fig_gate_wave():
    """图 8：MOS 逻辑门的输入输出波形（图 b）。"""
    s = [head(360, 320)]
    rows = [("$V_A$", [(0, 1), (1, 0), (2, 1), (3, 0), (4, 1)]),
            ("$V_B$", [(0, 1), (1, 0), (2, 0), (3, 1), (4, 1)]),
            ("$V_C$", [(0, 0), (1, 1), (2, 1), (3, 0), (4, 0)]),
            ("$V_O$", [(0, 0), (1, 1), (2, 0), (3, 0), (4, 0)])]
    y0 = 40
    for i, (label, _) in enumerate(rows):
        top = y0 + i * 72
        base = top + 40
        s.append(text(24, top + 14, label, anchor="end", size=12))
        s.append(line(34, base, 340, base, w=1.0))
        s.append(text(344, base + 4, "t", size=12))
    # 各行的方波
    def wave(idx, levels):
        top = y0 + idx * 72
        base = top + 40
        pts = [(34, base)]
        for k, lv in enumerate(levels):
            x0 = 34 + k * 60
            x1 = x0 + 60
            y = base - (30 if lv else 0)
            pts += [(x0, y), (x1, y)]
        pts.append((340, pts[-1][1]))
        return polyline(pts)
    s.append(wave(0, [1, 0, 1, 0, 1]))
    s.append(wave(1, [1, 0, 0, 1, 1]))
    s.append(wave(2, [0, 1, 1, 0, 0]))
    s.append(wave(3, [0, 1, 0, 0, 0]))
    s.append(text(346, 44, "$V_{DD}$", size=11))
    s.append(text(346, 116, "$V_{DD}$", size=11))
    s.append(text(346, 188, "$V_{DD}$", size=11))
    s.append(text(346, 260, "$V_{DD}$", size=11))
    s.append("</svg>")
    return "".join(s)


FIGURES = {
    "c1-clamp-circuit": fig_clamp,
    "c2-clamp-wave": fig_clamp_wave,
    "c3-zener": fig_zener,
    "c4-cmos-amp": fig_cmos_amp,
    "c5-multistage": fig_multistage,
    "c6-diff-amp": fig_diff,
    "c7-ce-amp": fig_ce_amp,
    "c8-cmos-gate": fig_cmos_gate,
    "c9-gate-wave": fig_gate_wave,
}


def main():
    ap = argparse.ArgumentParser(description="生成模电试卷电路图（SVG + PDF）")
    ap.add_argument("--outdir", default="figures/circuit")
    ap.add_argument("--svg-only", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for name, fn in FIGURES.items():
        svg_path = outdir / (name + ".svg")
        svg_path.write_text(fn(), encoding="utf-8")
        msg = "  {}  ({} bytes)".format(svg_path, svg_path.stat().st_size)
        if not args.svg_only:
            try:
                from svglib.svglib import svg2rlg
                from reportlab.graphics import renderPDF
                pdf_path = outdir / (name + ".pdf")
                renderPDF.drawToFile(svg2rlg(str(svg_path)), str(pdf_path))
                msg += "  -> " + pdf_path.name
            except Exception as e:  # noqa: BLE001
                msg += "  [PDF 失败: {}]".format(e)
        print(msg)


if __name__ == "__main__":
    main()
