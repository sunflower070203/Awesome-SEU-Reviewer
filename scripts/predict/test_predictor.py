#!/usr/bin/env python3
"""predictor 的单元测试。

运行：
    python scripts/predict/test_predictor.py -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from predictor import (  # noqa: E402
    MODE_EXAM_ONLY,
    MODE_HYBRID,
    WEIGHT_POSITION,
    WEIGHT_REPEAT,
    apply_merge,
    detect_mode,
    jaccard,
    load_pool,
    predict,
    tokens,
)


def exam(exam_id, questions):
    return {"id": exam_id, "questions": questions}


def fill(number, stem, score=4):
    return {"number": number, "type": "fill", "stem_latex": stem, "score": score}


class TestTokens(unittest.TestCase):
    def test_latex_commands_become_tokens(self):
        t = tokens(r"$\iint_D \arctan(x+y) d\sigma$")
        self.assertIn("iint", t)
        self.assertIn("arctan", t)
        self.assertIn("x", t)
        self.assertIn("y", t)

    def test_jaccard_bounds(self):
        self.assertEqual(jaccard(set("abc"), set("abc")), 1.0)
        self.assertEqual(jaccard(set("abc"), set("xyz")), 0.0)
        self.assertEqual(jaccard(set(), set("a")), 0.0)


class TestClustering(unittest.TestCase):
    def test_identical_questions_fall_into_one_cluster(self):
        stem = r"设 $D=\{(x,y)|x^2+y^2\le 1\}$，则 $\iint_D |x+y|d\sigma=$____"
        data = {"exams": [exam("A", [fill(1, stem)]), exam("B", [fill(1, stem)])]}
        result = predict(data)
        self.assertEqual(len(result["predictions"]), 1)
        top = result["predictions"][0]
        self.assertEqual(top["repeat"], 1.0)
        self.assertEqual(top["exams_seen"], ["A", "B"])

    def test_unrelated_questions_stay_separate(self):
        data = {"exams": [
            exam("A", [fill(1, r"求 $\lim_{n\to\infty} a_n$")]),
            exam("B", [fill(1, r"求曲面 $z=xy$ 的面积")]),
        ]}
        result = predict(data)
        self.assertEqual(len(result["predictions"]), 2)
        self.assertTrue(all(p["repeat"] == 0.5 for p in result["predictions"]))

    def test_shared_math_symbols_cluster_together(self):
        """同类考点（绝对值二重积分）即使数字不同，也应聚在一簇。"""
        data = {"exams": [
            exam("A", [fill(4, r"$\iint_D |y-\sqrt{x}|d\sigma$，$D=[0,1]\times[0,1]$")]),
            exam("B", [fill(4, r"$\iint_D |x+y|d\sigma$，$D=\{(x,y)|x^2+y^2\le1\}$")]),
        ]}
        result = predict(data)
        self.assertEqual(len(result["predictions"]), 1)
        self.assertEqual(result["predictions"][0]["repeat"], 1.0)


class TestScoring(unittest.TestCase):
    def test_score_formula(self):
        """score = 0.75 × repeat + 0.25 × position_stability"""
        stem = r"$\iint_D |x+y|d\sigma$"
        data = {"exams": [exam("A", [fill(4, stem)]), exam("B", [fill(4, stem)])]}
        top = predict(data)["predictions"][0]
        self.assertAlmostEqual(top["repeat"], 1.0)
        self.assertAlmostEqual(top["position_stability"], 1.0)
        expected = WEIGHT_REPEAT * 1.0 + WEIGHT_POSITION * 1.0
        self.assertAlmostEqual(top["score"], round(expected, 3))

    def test_position_stability_lower_when_numbers_differ(self):
        stem = r"$\iint_D |x+y|d\sigma$"
        data = {"exams": [exam("A", [fill(4, stem)]), exam("B", [fill(7, stem)])]}
        top = predict(data)["predictions"][0]
        self.assertAlmostEqual(top["repeat"], 1.0)
        self.assertAlmostEqual(top["position_stability"], 0.5)
        self.assertLess(top["score"], 1.0)

    def test_partial_repeat(self):
        stem = r"$\iint_D |x+y|d\sigma$"
        data = {"exams": [
            exam("A", [fill(4, stem)]),
            exam("B", [fill(4, stem)]),
            exam("C", [fill(1, r"求 $\lim_{n\to\infty} n a_n$")]),
        ]}
        preds = predict(data)["predictions"]
        by_repeat = {p["repeat"]: p for p in preds}
        self.assertIn(0.667, by_repeat)
        self.assertIn(0.333, by_repeat)
        self.assertGreater(by_repeat[0.667]["score"], by_repeat[0.333]["score"])

    def test_predictions_sorted_desc(self):
        data = {"exams": [
            exam("A", [fill(1, r"$\iint_D |x+y|d\sigma$"), fill(2, r"求 $\lim a_n$")]),
            exam("B", [fill(1, r"$\iint_D |x+y|d\sigma$"), fill(2, r"求曲面面积")]),
        ]}
        preds = predict(data)["predictions"]
        scores = [p["score"] for p in preds]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(preds[0]["rank"], 1)


class TestInputMode(unittest.TestCase):
    """试卷与课件不是互斥关系：按实际提供的资料判定模式。"""

    def test_exam_only(self):
        data = {"exams": [exam("A", [fill(1, "x")]), exam("B", [fill(1, "x")])]}
        self.assertEqual(detect_mode(data), MODE_EXAM_ONLY)
        self.assertEqual(predict(data)["mode"], MODE_EXAM_ONLY)

    def test_hybrid_when_both_present(self):
        data = {
            "exams": [exam("A", [fill(1, "x")]), exam("B", [fill(1, "x")])],
            "ppt_paths": ["ch1.pptx"],
        }
        self.assertEqual(detect_mode(data), MODE_HYBRID)
        result = predict(data)
        self.assertEqual(result["mode"], MODE_HYBRID)
        self.assertTrue(result["warnings"], "hybrid 未实现时应给出 warning")

    def test_ppt_only_gives_actionable_error(self):
        with self.assertRaises(ValueError) as ctx:
            predict({"ppt_paths": ["ch1.pptx"]})
        self.assertIn("试卷", str(ctx.exception))

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            predict({})

    def test_single_exam_is_insufficient(self):
        """只有 1 份试卷无法计算跨卷重复度。"""
        with self.assertRaises(ValueError):
            predict({"exams": [exam("A", [fill(1, "x")])]})


class TestTopicMerge(unittest.TestCase):
    """LLM 考点归并后的重新打分（apply_merge）。"""

    def test_recomputes_repeat_after_merge(self):
        """两卷措辞不同但同考点的题，归并后应算作 2/2 覆盖。"""
        data = {"exams": [
            exam("A", [fill(3, r"设 $z=\arctan(xy)$，求 $dz$")]),
            exam("B", [fill(3, r"设 $f(x,x^3)=x^6$，求 $f_y(x,x^3)$")]),
        ]}
        merged = {"topics": [{
            "label": "偏导数/全微分",
            "members": [
                {"exam": "A", "number": 3, "type": "fill"},
                {"exam": "B", "number": 3, "type": "fill"},
            ],
            "rationale": "两卷第 3 题都考偏导",
        }]}
        result = apply_merge(data, merged)
        self.assertEqual(result["mode"], "merged")
        top = result["predictions"][0]
        self.assertEqual(top["topic"], "偏导数/全微分")
        self.assertEqual(top["repeat"], 1.0)
        self.assertEqual(top["position_stability"], 1.0)
        self.assertEqual(top["score"], 1.0)
        self.assertEqual(top["rationale"], "两卷第 3 题都考偏导")

    def test_partial_coverage(self):
        data = {"exams": [
            exam("A", [fill(1, "x")]),
            exam("B", [fill(1, "x")]),
            exam("C", [fill(1, "x")]),
        ]}
        merged = {"topics": [{"label": "T", "members": [
            {"exam": "A", "number": 1, "type": "fill"},
            {"exam": "B", "number": 1, "type": "fill"},
        ]}]}
        top = apply_merge(data, merged)["predictions"][0]
        self.assertAlmostEqual(top["repeat"], 0.667)
        self.assertIsNone(top.get("stem_samples"))

    def test_empty_topics_raises(self):
        with self.assertRaises(ValueError):
            apply_merge({"exams": [exam("A", [fill(1, "x")])]}, {"topics": []})

    def test_sorted_by_score(self):
        data = {"exams": [
            exam("A", [fill(1, "x"), fill(2, "y")]),
            exam("B", [fill(1, "x")]),
        ]}
        merged = {"topics": [
            {"label": "低", "members": [{"exam": "A", "number": 2, "type": "fill"}]},
            {"label": "高", "members": [
                {"exam": "A", "number": 1, "type": "fill"},
                {"exam": "B", "number": 1, "type": "fill"},
            ]},
        ]}
        preds = apply_merge(data, merged)["predictions"]
        self.assertEqual(preds[0]["topic"], "高")
        self.assertEqual(preds[0]["rank"], 1)


class TestLoadPool(unittest.TestCase):
    """输入兼容：池格式与单卷格式（Skill A 的 vision-extract 输出）都能吃。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name, obj):
        p = self.dir / name
        p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return str(p)

    def test_single_exam_format(self):
        p1 = self._write("a.json", {
            "exam_id": "2023-24",
            "questions": [fill(1, r"$x$")],
        })
        p2 = self._write("b.json", {
            "exam_id": "2024-25",
            "questions": [fill(1, r"$x$")],
        })
        pool = load_pool([p1, p2])
        self.assertEqual([e["id"] for e in pool["exams"]], ["2023-24", "2024-25"])
        self.assertEqual(predict(pool)["mode"], MODE_EXAM_ONLY)

    def test_mixed_formats(self):
        pool_file = self._write("pool.json", {"exams": [exam("A", [fill(1, "x")])]})
        single = self._write("s.json", {"exam_id": "B", "questions": [fill(1, "x")]})
        pool = load_pool([pool_file, single])
        self.assertEqual([e["id"] for e in pool["exams"]], ["A", "B"])

    def test_unrecognised_raises(self):
        bad = self._write("bad.json", {"foo": 1})
        with self.assertRaises(ValueError):
            load_pool([bad])


if __name__ == "__main__":
    unittest.main(verbosity=2)
