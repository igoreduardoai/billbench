"""Strict, deterministic grader. No LLM judge.

A response passes only if its LAST line matching `FINAL: $X.XX` equals the ground truth
to the cent. Missing or malformed FINAL lines fail. Wrong answers are attributed to a
named failure mode when they equal the output of a simulated mistake in the engine."""
import re
from decimal import Decimal
from .engine import compute, MISTAKES

FINAL_RE = re.compile(r"FINAL:\s*\**\s*\$\s*(-?[\d,]*\d(?:\.\d{1,2})?)\b")

def extract(text):
    """Return the last FINAL amount as Decimal, or None."""
    if not text:
        return None
    m = FINAL_RE.findall(text.replace("\\$", "$"))
    if not m:
        return None
    raw = m[-1].replace(",", "")
    try:
        return Decimal(raw).quantize(Decimal("0.01"))
    except Exception:
        return None

def grade(text, answer):
    got = extract(text)
    return got is not None and got == Decimal(str(answer)).quantize(Decimal("0.01")), got

def attribute(task, got):
    """Named failure modes whose simulated answer equals the model's answer."""
    if got is None:
        return ["no_final_answer"]
    hits = [m for m, v in task["mistake_values"].items() if Decimal(str(v)).quantize(Decimal("0.01")) == got]
    return hits or ["unexplained_arithmetic_or_reasoning"]

def describe(mode, task=None):
    if task and mode in task.get("mistake_text", {}):
        return task["mistake_text"][mode]
    return MISTAKES.get(mode, {"no_final_answer": "no parseable FINAL: $X.XX line",
                               "unexplained_arithmetic_or_reasoning": "wrong amount not matching any simulated mistake"}.get(mode, mode))
