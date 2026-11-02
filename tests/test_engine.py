"""Ground truth hand-check: each answer is re-derived here with literal arithmetic,
independently of the engine, so a bug in engine.py cannot silently change an answer."""
import unittest
from decimal import Decimal
from billbench.tasks import TASKS

HAND = {
    "t01": 0.20 * (142.60 + 38.15),                                   # 36.15
    "t02": 612.40 + (750 - 612.40) + 0.20 * (187.30 - (750 - 612.40)), # 759.94
    "t03": min(0.30 * 2400 + 0.30 * 640 + 40, 900),                    # 900.00 (OOP cap)
    "t04": min(0.20 * 800, 120) + 95,                                  # 215.00
    "t05": 35 + 0 + 0.10 * 21.40,                                      # 37.14
    "t06": 350 + 0.20 * (980 - 350) + 0.20 * 145,                      # 505.00
    "t07": 0.20 * 4000 + 0.20 * 1150,                                  # 1030.00
    "t08": (200 + 0.20 * (450 - 200)) + 300,                           # 550.00
    "t09": (400 + 0.20 * (2100 - 400)) + 0.20 * 3600 - 300,            # 1160.00
    "t10": 0 + 30 + 42 + 0,                                            # 72.00
}

class TestGroundTruth(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(TASKS), 10)
        self.assertEqual(len({t["id"] for t in TASKS}), 10)

    def test_hand_check(self):
        for t in TASKS:
            with self.subTest(t["id"]):
                self.assertEqual(Decimal(str(t["answer"])), Decimal(str(round(HAND[t["id"]], 2))).quantize(Decimal("0.01")))

    def test_each_mistake_changes_answer(self):
        from billbench.engine import compute
        for t in TASKS:
            for m in t["mistakes"]:
                with self.subTest(task=t["id"], mistake=m):
                    self.assertNotEqual(compute(t["visits"], t["plan"], t["prior"], m), Decimal(str(t["answer"])).quantize(Decimal("0.01")))

    def test_prompt_states_rules(self):
        for t in TASKS:
            self.assertIn("FINAL: $X.XX", t["prompt"])
            self.assertIn("ALLOWED amount", t["prompt"])

if __name__ == "__main__":
    unittest.main()

class TestExpert(unittest.TestCase):
    HAND = {"x01": 1030.00, "x04": 66.50, "x05": 120.00, "x06": 3472.00,
            "x09": 980.00, "x10": 30.00, "x11": 4500.00, "x12": 8246.00, "x13": 68.00, "x14": 3906.00}
    def test_expert_answers(self):
        from billbench.expert import EXPERT
        self.assertEqual(len(EXPERT), 10)
        for t in EXPERT:
            with self.subTest(t["id"]):
                self.assertAlmostEqual(t["answer"], self.HAND[t["id"]], places=2)
                for m, v in t["mistake_values"].items():
                    self.assertNotEqual(float(v), t["answer"], m)
                self.assertTrue(t["source"])

class TestControls(unittest.TestCase):
    def test_controls(self):
        from billbench.expert import CONTROLS
        want = {"x02": 1680.00, "r03": 3000.00, "x07": 331.00, "r08": 1170.00}
        self.assertEqual({t["id"]: t["answer"] for t in CONTROLS}, want)
