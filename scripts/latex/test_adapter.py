#!/usr/bin/env python3
"""exampaper_adapter 的边界测试。

运行：
    python scripts/latex/test_adapter.py -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from exampaper_adapter import render_exam  # noqa: E402


class TestRenderExam(unittest.TestCase):
    def test_minimal_input(self):
        """无 header / options 时不应崩溃，试卷名回退为「试卷」。"""
        out = render_exam({"questions": [
            {"number": 1, "type": "calculation", "stem_latex": "求 $x$ 的值。"}
        ]})
        self.assertIn("\\examsection{计算题（本题共 1 小题）}", out)
        self.assertIn("\\examname{试卷}", out)

    def test_image_question(self):
        r"""带 image_path 的题应渲染 \examfigure。"""
        out = render_exam({"questions": [
            {"number": 1, "type": "circuit_question", "stem_latex": "求等效电阻。",
             "image_path": "figures/q1.png", "image_caption": "电路图"}
        ]})
        self.assertIn("\\examfigure[0.6\\textwidth]{电路图}{figures/q1.png}", out)

    def test_empty_questions_raises(self):
        with self.assertRaises(ValueError):
            render_exam({"questions": []})

    def test_type_order_preserved(self):
        """题型分组保持首次出现顺序，分值统计正确。"""
        out = render_exam({"questions": [
            {"type": "fill", "stem_latex": "a", "score": 4},
            {"type": "choice", "stem_latex": "b",
             "options": [{"label": "A", "latex": "1"}], "score": 4},
            {"type": "fill", "stem_latex": "c", "score": 4},
        ]})
        self.assertLess(out.index("填空题"), out.index("单项选择题"))
        self.assertIn("本题共 2 小题，每小题 4 分，满分 8 分", out)

    def test_choice_options_inline(self):
        """选项必须内联渲染，不得使用 enumerate。"""
        out = render_exam({"questions": [
            {"type": "choice", "stem_latex": "题干",
             "options": [{"label": "A", "latex": "$1$"}, {"label": "B", "latex": "$2$"}],
             "score": 4}
        ]})
        self.assertIn("\\quad A.\\ $1$ \\quad B.\\ $2$", out)
        self.assertNotIn("enumerate", out)

    def test_seal_line_disabled(self):
        out = render_exam({
            "questions": [{"type": "fill", "stem_latex": "a", "score": 4}],
            "options": {"sidebar_seal_line": False},
        })
        self.assertIn("\\examsidebarfalse", out)

    def test_exam_meta_alias(self):
        """exam_meta 应可作为 header 的别名。"""
        out = render_exam({
            "exam_meta": {"course_name": "概率论", "duration_minutes": 120},
            "questions": [{"type": "fill", "stem_latex": "a", "score": 4}],
        })
        self.assertIn("\\examname{概率论}", out)
        self.assertIn("120\\hspace{0.4em}分钟", out)

    def test_answer_space_after_every_question(self):
        r"""留白必须跟在**每一题之后**（含最后一题），且第一题之前不留白。

        回归测试：早期实现用 `\begin{examquestions}[7cm]`（即 \parskip），
        结果留白错误地落在第一题之前、且最后一题之后没有留白。
        """
        out = render_exam({"questions": [
            {"type": "calculation", "stem_latex": "题A", "score": 10},
            {"type": "calculation", "stem_latex": "题B", "score": 10},
        ]})
        self.assertIn("\\begin{examquestions}[0pt]", out)
        self.assertEqual(out.count("\\par\\vspace{7cm}"), 2)
        self.assertNotIn("[7cm]", out)
        # 留白必须紧跟在题干之后，而不是在 \examquestion 之前
        body = out.split("\\begin{examquestions}[0pt]")[1]
        first_line = body.strip().splitlines()[0]
        self.assertTrue(first_line.startswith("\\examquestion"),
                        f"第一行应是题干而非留白：{first_line!r}")

    def test_no_answer_space_for_choice_and_fill(self):
        """选择题/填空题不需要答题留白，用默认题间距。"""
        out = render_exam({"questions": [
            {"type": "choice", "stem_latex": "题", "options": [{"label": "A", "latex": "1"}], "score": 4},
            {"type": "fill", "stem_latex": "题", "score": 4},
        ]})
        self.assertIn("\\begin{examquestions}\n", out)
        self.assertNotIn("\\par\\vspace", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
