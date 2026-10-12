#!/usr/bin/env python3
"""preprocess.py 的单元测试。

运行：
    python scripts/ocr/test_preprocess.py -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from preprocess import content_bbox, estimate, process_one  # noqa: E402


def make_image(path, size, content_box=None, bg=40, fg=230):
    """造一张测试图：默认整幅背景色；给定 content_box 时在框内画深色内容。"""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", size, (bg, bg, bg))
    if content_box:
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = content_box
        # 画横条模拟文字行，产生强边缘
        for y in range(y0, y1, 12):
            d.rectangle([x0, y, x1, y + 5], fill=(fg, fg, fg))
    im.save(path)
    return path


class TestContentBbox(unittest.TestCase):
    def test_detects_inner_content(self):
        """四周留白的内容区应被识别出来。"""
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            p = make_image(Path(td) / "a.png", (400, 400), content_box=(100, 100, 300, 300))
            with Image.open(p) as im:
                x0, y0, x1, y1 = content_bbox(im)
        # 容许一定误差，但应明显收进画面内部
        self.assertLess(x0, 110)
        self.assertGreater(x0, 60)
        self.assertGreater(x1, 290)
        self.assertLess(x1, 340)
        self.assertGreater(y0, 60)
        self.assertLess(y1, 340)

    def test_blank_image_returns_full(self):
        """没有内容的图不应裁成空。"""
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            p = make_image(Path(td) / "b.png", (200, 200))
            with Image.open(p) as im:
                box = content_bbox(im)
        self.assertEqual(box, (0, 0, 200, 200))


class TestProcessOne(unittest.TestCase):
    def test_scales_down_to_max_side(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            p = make_image(td / "big.png", (4000, 3000), content_box=(100, 100, 3900, 2900))
            rec = process_one(p, td, max_side=1600, do_crop=False, quality=88)
        self.assertEqual(rec["final"][0], 1600)
        self.assertEqual(rec["final"][1], 1200)

    def test_no_upscale(self):
        """比目标小的图不应被放大。"""
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            p = make_image(td / "small.png", (800, 600), content_box=(50, 50, 750, 550))
            rec = process_one(p, td, max_side=1600, do_crop=False, quality=88)
        self.assertEqual(rec["final"], [800, 600])

    def test_crop_reduces_area(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            p = make_image(td / "c.png", (1200, 1200), content_box=(300, 300, 900, 900))
            rec = process_one(p, td, max_side=0, do_crop=True, quality=88)
        ow, oh = rec["orig"]
        cw, ch = rec["cropped"]
        self.assertLess(cw * ch, ow * oh)
        self.assertGreater(cw, 400)   # 不该把内容裁没


class TestEstimate(unittest.TestCase):
    def test_reports_both_schemes(self):
        rec = {"orig": [4000, 3000], "final": [1600, 1200]}
        est = estimate(rec)
        self.assertEqual(set(est), {"openai_before", "openai_after",
                                    "claude_before", "claude_after"})
        # Claude 按面积：应显著下降
        self.assertLess(est["claude_after"], est["claude_before"] * 0.4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
