"""
Big Five Personality Assessment — Scoring Engine.

Implements the full scoring pipeline:
  1. Reverse-coding (items 5, 11, 20, 22, 38)
  2. Sub-factor scores (mean of 5 items each, 10 sub-factors)
  3. Big Five factor scores (mean of 2 sub-factors each)
  4. 0–100 scale conversion: ((raw - 1) / 4) * 100
  5. Cross-domain comparison pairs
"""

from __future__ import annotations

from statistics import mean

# ──────────────────────────────────────────────
# Reverse-coded item IDs (1-indexed)
# ──────────────────────────────────────────────
REVERSE_ITEMS: set[int] = {5, 11, 20, 22, 38}

# ──────────────────────────────────────────────
# Sub-factor → item ID mapping (1-indexed)
# ──────────────────────────────────────────────
SUBFACTOR_ITEMS: dict[str, list[int]] = {
    # Agreeableness
    "compassion":       [1, 35, 45, 49, 50],
    "politeness":       [8, 11, 20, 22, 34],
    # Openness / Intellect
    "openness":         [2, 7, 10, 21, 48],
    "intellect":        [12, 16, 26, 43, 46],
    # Neuroticism
    "withdrawal":       [3, 24, 25, 28, 30],
    "volatility":       [5, 17, 27, 38, 44],
    # Extraversion
    "assertiveness":    [4, 18, 23, 36, 41],
    "enthusiasm":       [31, 32, 33, 39, 47],
    # Conscientiousness
    "industriousness":  [9, 13, 29, 37, 42],
    "orderliness":      [6, 14, 15, 19, 40],
}

# ──────────────────────────────────────────────
# Big Five factor → constituent sub-factors
# ──────────────────────────────────────────────
FACTOR_SUBFACTORS: dict[str, tuple[str, str]] = {
    "agreeableness":      ("compassion",      "politeness"),
    "openness_intellect": ("openness",        "intellect"),
    "neuroticism":        ("withdrawal",      "volatility"),
    "extraversion":       ("assertiveness",   "enthusiasm"),
    "conscientiousness":  ("industriousness", "orderliness"),
}

# ──────────────────────────────────────────────
# Comparison pairs: (label, left_key, right_key)
#   left/right may be a factor or a sub-factor
# ──────────────────────────────────────────────
COMPARISON_PAIRS: list[tuple[str, str, str]] = [
    ("agreeableness_vs_compassion",          "agreeableness",      "compassion"),
    ("openness_intellect_vs_assertiveness",  "openness_intellect", "assertiveness"),
    ("neuroticism_vs_industriousness",       "neuroticism",        "industriousness"),
    ("extraversion_vs_orderliness",          "extraversion",       "orderliness"),
    ("conscientiousness_vs_openness",        "conscientiousness",  "openness"),
]


def _reverse_code(value: int) -> int:
    """Reverse-code a 1–5 Likert response."""
    return 6 - value


def _to_score100(raw: float) -> float:
    """Convert a 1–5 raw mean to a 0–100 scale."""
    return round(((raw - 1) / 4) * 100, 1)


def calculate_big_five_scores(answers: list[int]) -> dict:
    """
    Full Big Five scoring pipeline.

    Parameters
    ----------
    answers : list[int]
        Exactly 50 integers in the range [1, 5].
        Index 0 = Question 1, Index 49 = Question 50.

    Returns
    -------
    dict with keys:
        "subfactors"   – 10 sub-factor scores (raw 1–5 + score100 0–100)
        "factors"      – 5 Big Five factor scores (raw + score100)
        "comparisons"  – 5 cross-domain comparison diffs

    Raises
    ------
    ValueError
        If input validation fails.
    """
    # ── Validation ──
    if len(answers) != 50:
        raise ValueError(f"모든 문항에 응답해야 합니다. (50개 필요, {len(answers)}개 수신)")

    for i, v in enumerate(answers):
        if not isinstance(v, int) or v < 1 or v > 5:
            raise ValueError(
                f"문항 {i + 1}의 응답은 1–5 사이 정수여야 합니다. (입력값: {v!r})"
            )

    # ── Build 1-indexed response dict with reverse-coding applied ──
    responses: dict[int, int] = {}
    for idx, val in enumerate(answers):
        qid = idx + 1
        responses[qid] = _reverse_code(val) if qid in REVERSE_ITEMS else val

    # ── Sub-factor scores ──
    subfactors: dict[str, dict[str, float]] = {}
    for sf_name, item_ids in SUBFACTOR_ITEMS.items():
        item_scores = [responses[qid] for qid in item_ids]
        raw = round(mean(item_scores), 2)
        subfactors[sf_name] = {
            "raw": raw,
            "score100": _to_score100(raw),
        }

    # ── Big Five factor scores ──
    factors: dict[str, dict[str, float]] = {}
    for factor_name, (sf_a, sf_b) in FACTOR_SUBFACTORS.items():
        raw = round(mean([subfactors[sf_a]["raw"], subfactors[sf_b]["raw"]]), 2)
        factors[factor_name] = {
            "raw": raw,
            "score100": _to_score100(raw),
        }

    # ── Comparison pairs ──
    # Build a lookup combining both factors and subfactors for comparison access
    all_scores: dict[str, float] = {}
    for name, data in factors.items():
        all_scores[name] = data["raw"]
    for name, data in subfactors.items():
        all_scores[name] = data["raw"]

    comparisons: dict[str, dict] = {}
    for label, left_key, right_key in COMPARISON_PAIRS:
        left_val = all_scores[left_key]
        right_val = all_scores[right_key]
        diff = round(left_val - right_val, 2)
        comparisons[label] = {
            "left": left_key,
            "right": right_key,
            "diff": diff,
            "higher": left_key if diff > 0 else (right_key if diff < 0 else "equal"),
        }

    return {
        "subfactors": subfactors,
        "factors": factors,
        "comparisons": comparisons,
    }
