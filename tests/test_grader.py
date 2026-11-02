"""Grader self-test: known-correct and known-wrong responses (no false pass / false fail)."""
import unittest
from decimal import Decimal
from billbench.grader import extract, grade, attribute
from billbench.tasks import TASKS

T = {t["id"]: t for t in TASKS}

class TestGrader(unittest.TestCase):
    def test_true_passes(self):
        for s in ["work...\nFINAL: $36.15", "FINAL: $36.15", "FINAL:$36.15", "**FINAL: $36.15**", "FINAL: $ 36.15", "FINAL: \\$36.15"]:
            with self.subTest(s=s):
                self.assertTrue(grade(s, 36.15)[0])
        self.assertTrue(grade("FINAL: $1,160.00", 1160.0)[0])
        self.assertTrue(grade("FINAL: $1160", 1160.0)[0])

    def test_true_fails(self):
        for s in ["FINAL: $36.16", "FINAL: $36.1", "The answer is $36.15", "", None, "FINAL: $361.50", "FINAL: 36.15"]:
            with self.subTest(s=s):
                self.assertFalse(grade(s, 36.15)[0])

    def test_last_final_wins(self):
        self.assertFalse(grade("FINAL: $36.15\n...wait, recheck\nFINAL: $119.00", 36.15)[0])
        self.assertTrue(grade("FINAL: $119.00\n...wait, recheck\nFINAL: $36.15", 36.15)[0])

    def test_extract(self):
        self.assertEqual(extract("FINAL: $2,050.00"), Decimal("2050.00"))
        self.assertIsNone(extract("no answer"))

    def test_attribution(self):
        self.assertEqual(attribute(T["t07"], Decimal("3425.00")), ["nsa_ignored"])
        self.assertEqual(attribute(T["t09"], Decimal("1460.00")), ["forget_prior_payment"])
        self.assertEqual(attribute(T["t01"], Decimal("119.00")), ["billed_not_allowed"])
        self.assertEqual(attribute(T["t01"], None), ["no_final_answer"])
        self.assertEqual(attribute(T["t01"], Decimal("1.00")), ["unexplained_arithmetic_or_reasoning"])

    def test_engine_answers_pass_own_grader(self):
        for t in TASKS:
            self.assertTrue(grade(f"FINAL: ${t['answer']:,.2f}", t["answer"])[0])

if __name__ == "__main__":
    unittest.main()
