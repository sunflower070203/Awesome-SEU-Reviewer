#!/usr/bin/env python3
"""predictor 的单元测试。

运行：
    python scripts/predict/test_predictor.py -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from predictor import (  # noqa: E402
    WEIGHT_POSITION,
    WEIGHT_REPEAT,
    jaccard,
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
