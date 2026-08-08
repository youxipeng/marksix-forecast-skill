#!/usr/bin/env python3
"""Auditable Mark Six research engine: math + traditional metaphysics features.

The output scores are rankings, not calibrated draw probabilities.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


P_MAIN = 6 / 49
P_EXTRA = 1 / 49
ALL_NUMBERS = tuple(range(1, 50))
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
ZODIACS = ("鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪")
ZODIAC_ELEMENT = {
    "鼠": "水", "牛": "土", "虎": "木", "兔": "木", "龙": "土", "蛇": "火",
    "马": "火", "羊": "土", "猴": "金", "鸡": "金", "狗": "土", "猪": "水",
}
ZODIAC_LIUHE = {
    "鼠": "牛", "牛": "鼠", "虎": "猪", "猪": "虎", "兔": "狗", "狗": "兔",
    "龙": "鸡", "鸡": "龙", "蛇": "猴", "猴": "蛇", "马": "羊", "羊": "马",
}
ZODIAC_CHONG = {
    "鼠": "马", "马": "鼠", "牛": "羊", "羊": "牛", "虎": "猴", "猴": "虎",
    "兔": "鸡", "鸡": "兔", "龙": "狗", "狗": "龙", "蛇": "猪", "猪": "蛇",
}
ZODIAC_TRINES = (
    frozenset(("鼠", "龙", "猴")),
    frozenset(("牛", "蛇", "鸡")),
    frozenset(("虎", "马", "狗")),
    frozenset(("兔", "羊", "猪")),
)
STEM_ELEMENT = dict(zip(STEMS, ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]))
BRANCH_ELEMENT = dict(zip(BRANCHES, ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]))
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
TRIGRAM = {1: "乾", 2: "兑", 3: "离", 4: "震", 5: "巽", 6: "坎", 7: "艮", 8: "坤"}
TRIGRAM_ELEMENT = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}
PALACE_ELEMENT = {1: "水", 2: "土", 3: "木", 4: "木", 5: "土", 6: "金", 7: "金", 8: "土", 9: "火"}
QIMEN_STEMS = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]

# Standard hourly-Qimen solar-term / three-yuan Ju table used for the
# deliberately narrow Earth-plate feature described in references/metaphysics.md.
QIMEN_JU = {
    "冬至": (True, (1, 7, 4)), "小寒": (True, (2, 8, 5)), "大寒": (True, (3, 9, 6)),
    "立春": (True, (8, 5, 2)), "雨水": (True, (9, 6, 3)), "惊蛰": (True, (1, 7, 4)),
    "春分": (True, (3, 9, 6)), "清明": (True, (4, 1, 7)), "谷雨": (True, (5, 2, 8)),
    "立夏": (True, (4, 1, 7)), "小满": (True, (5, 2, 8)), "芒种": (True, (6, 3, 9)),
    "夏至": (False, (9, 3, 6)), "小暑": (False, (8, 2, 5)), "大暑": (False, (7, 1, 4)),
    "立秋": (False, (2, 5, 8)), "处暑": (False, (1, 4, 7)), "白露": (False, (9, 3, 6)),
    "秋分": (False, (7, 1, 4)), "寒露": (False, (6, 9, 3)), "霜降": (False, (5, 8, 2)),
    "立冬": (False, (6, 9, 3)), "小雪": (False, (5, 8, 2)), "大雪": (False, (4, 7, 1)),
}

LEGACY_MES_V1_WEIGHTS = {"bayes": 0.45, "ewma": 0.40, "transition": 0.15}
MES_BASE_WEIGHTS = {"mes_v1": 0.35, "bayes": 0.20, "ewma": 0.20, "transition": 0.10, "hmm": 0.15}
MES_ARENA_VALIDATION_STEPS = 48
MES_ARENA_MIN_TRAIN = 60
MONTE_CARLO_TRIALS = 50000
OMEN_HYBRID_WEIGHT = 0.10
COLOR_ELEMENT_KEYWORDS = {
    "木": ("青", "绿", "绿色", "青色"),
    "火": ("红", "紫", "粉", "橙", "红色", "紫色", "粉色", "橙色"),
    "土": ("黄", "棕", "咖啡", "米色", "黄色", "棕色"),
    "金": ("白", "金", "银", "灰", "白色", "金色", "银色", "灰色"),
    "水": ("黑", "蓝", "深蓝", "黑色", "蓝色"),
}
OBJECT_ELEMENT_KEYWORDS = {
    "木": ("树", "植物", "花", "木", "竹", "纸", "书"),
    "火": ("灯", "火", "蜡烛", "手机", "电脑", "屏幕", "电视", "电器"),
    "土": ("土", "石", "砖", "陶", "瓷", "墙", "山"),
    "金": ("金属", "铁", "钢", "铜", "钥匙", "刀", "剪", "硬币", "车"),
    "水": ("水", "饮料", "雨", "河", "海", "鱼", "水池"),
}
DIRECTION_ELEMENT = {
    "东": "木", "东南": "木", "南": "火", "西南": "土", "东北": "土", "中": "土",
    "西": "金", "西北": "金", "北": "水",
}
SOUND_ELEMENT_KEYWORDS = {
    "木": ("风", "鸟", "树叶", "枝", "木声"),
    "火": ("爆", "喇叭", "提示音", "警报", "电流"),
    "土": ("脚步", "敲墙", "石", "陶", "闷响"),
    "金": ("铃", "金属", "钥匙", "硬币", "刀", "剪"),
    "水": ("雨", "流水", "水声", "海浪", "滴水"),
}
WEATHER_ELEMENT_KEYWORDS = {
    "木": ("风", "大风", "微风"),
    "火": ("晴", "太阳", "炎热", "高温", "烈日"),
    "土": ("沙尘", "扬尘", "干燥"),
    "金": ("霜", "冰雹"),
    "水": ("雨", "雪", "雾", "阴", "潮湿"),
}


@dataclass(frozen=True)
class Draw:
    draw_id: str
    date: datetime
    main: Tuple[int, ...]
    extra: int


def parse_dt(value: str, default_time: Tuple[int, int] = (21, 30)) -> datetime:
    value = value.strip().replace("/", "-")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"无法解析日期时间: {value}") from exc
    if "T" not in value and " " not in value:
        dt = dt.replace(hour=default_time[0], minute=default_time[1])
    return dt


def load_draws(path: str) -> List[Draw]:
    draws: List[Draw] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"date", "n1", "n2", "n3", "n4", "n5", "n6", "extra"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV 缺少字段: {', '.join(sorted(missing))}")
        for idx, row in enumerate(reader, start=2):
            nums = tuple(sorted(int(row[f"n{i}"]) for i in range(1, 7)))
            extra = int(row["extra"])
            if len(set(nums)) != 6 or any(n not in ALL_NUMBERS for n in nums):
                raise ValueError(f"CSV 第 {idx} 行主号码非法: {nums}")
            if extra not in ALL_NUMBERS or extra in nums:
                raise ValueError(f"CSV 第 {idx} 行特别号非法: {extra}")
            draws.append(Draw(row.get("draw_id", "") or str(idx - 1), parse_dt(row["date"]), nums, extra))
    draws.sort(key=lambda d: d.date)
    if len({(d.draw_id, d.date) for d in draws}) != len(draws):
        raise ValueError("CSV 存在重复 draw_id/date 记录")
    return draws


def minmax(scores: Dict[int, float]) -> Dict[int, float]:
    lo, hi = min(scores.values()), max(scores.values())
    if math.isclose(lo, hi):
        return {n: 50.0 for n in scores}
    return {n: round(100 * (v - lo) / (hi - lo), 4) for n, v in scores.items()}


def clamp(x: float, lo: float = -4.0, hi: float = 4.0) -> float:
    return min(hi, max(lo, x))


def _normalize_distribution(values: Dict[int, float]) -> Dict[int, float]:
    cleaned = {n: max(1e-12, float(values.get(n, 0.0))) for n in ALL_NUMBERS}
    total = sum(cleaned.values())
    return {n: cleaned[n] / total for n in ALL_NUMBERS}


def _extra_bayes_probs(
    draws: Sequence[Draw], window: int = 160, prior_strength: float = 49.0
) -> Dict[int, float]:
    """Dirichlet-multinomial posterior for the one-of-49 Extra Number."""
    recent = draws[-window:]
    counts = Counter(d.extra for d in recent)
    alpha = prior_strength / 49.0
    denom = len(recent) + prior_strength
    return {n: (counts[n] + alpha) / denom for n in ALL_NUMBERS}


def _extra_multiscale_ewma_probs(
    draws: Sequence[Draw], prior_strength: float = 10.0
) -> Dict[int, float]:
    """Blend short/medium/long exponentially weighted categorical histories."""
    horizons = ((8.0, 0.50), (21.0, 0.30), (55.0, 0.20))
    blended = {n: 0.0 for n in ALL_NUMBERS}
    for half_life, horizon_weight in horizons:
        decay = 0.5 ** (1.0 / half_life)
        counts = {n: 0.0 for n in ALL_NUMBERS}
        total_weight = 0.0
        for age, draw in enumerate(reversed(draws)):
            weight = decay ** age
            counts[draw.extra] += weight
            total_weight += weight
        denom = total_weight + prior_strength
        for n in ALL_NUMBERS:
            p = (counts[n] + prior_strength / 49.0) / denom
            blended[n] += horizon_weight * p
    return _normalize_distribution(blended)


def _extra_transition_probs(
    draws: Sequence[Draw], modulus: int = 7, prior_strength: float = 49.0
) -> Tuple[Dict[int, float], int]:
    """Smoothed first-order transition from the previous Extra Number's residue state.

    Using seven residue states avoids a sparse 49x49 transition table while still making
    serial dependence a testable hypothesis. The strong symmetric prior pulls weak states
    back toward 1/49.
    """
    if len(draws) < 2:
        return {n: P_EXTRA for n in ALL_NUMBERS}, 0
    state = (draws[-1].extra - 1) % modulus
    counts = Counter()
    support = 0
    for prev, nxt in zip(draws[:-1], draws[1:]):
        if (prev.extra - 1) % modulus == state:
            counts[nxt.extra] += 1
            support += 1
    alpha = prior_strength / 49.0
    denom = support + prior_strength
    return {n: (counts[n] + alpha) / denom for n in ALL_NUMBERS}, support


@lru_cache(maxsize=512)
def _hmm_residue_forecast(extras: Tuple[int, ...]) -> Tuple[Tuple[float, ...], dict]:
    """Fit a tiny two-state HMM to seven Extra-number residue classes.

    The hidden states are intentionally unlabeled regimes.  Strong transition/emission
    smoothing and a seven-class observation space keep the model identifiable enough for
    a small lottery history; it is a hypothesis generator, not evidence of a real regime.
    """
    obs = tuple((n - 1) % 7 for n in extras[-180:])
    if len(obs) < 35:
        return tuple(1 / 7 for _ in range(7)), {
            "status": "history_too_short",
            "observations": len(obs),
        }

    k = 2
    m = 7
    pi = [0.5, 0.5]
    trans = [[0.88, 0.12], [0.12, 0.88]]

    # Break label symmetry deterministically using first-half vs second-half residue counts.
    mid = len(obs) // 2
    halves = (obs[:mid], obs[mid:])
    emit = []
    for part in halves:
        counts = Counter(part)
        denom = len(part) + 7.0
        emit.append([(counts[r] + 1.0) / denom for r in range(m)])

    last_log_likelihood = None
    for _ in range(12):
        alpha = [[0.0] * k for _ in obs]
        scales = [0.0] * len(obs)
        for s in range(k):
            alpha[0][s] = pi[s] * emit[s][obs[0]]
        scales[0] = max(1e-15, sum(alpha[0]))
        alpha[0] = [v / scales[0] for v in alpha[0]]
        for t in range(1, len(obs)):
            for s in range(k):
                alpha[t][s] = emit[s][obs[t]] * sum(alpha[t - 1][j] * trans[j][s] for j in range(k))
            scales[t] = max(1e-15, sum(alpha[t]))
            alpha[t] = [v / scales[t] for v in alpha[t]]

        beta = [[1.0] * k for _ in obs]
        for t in range(len(obs) - 2, -1, -1):
            for s in range(k):
                beta[t][s] = sum(
                    trans[s][j] * emit[j][obs[t + 1]] * beta[t + 1][j]
                    for j in range(k)
                ) / scales[t + 1]

        gamma = [[0.0] * k for _ in obs]
        for t in range(len(obs)):
            denom = max(1e-15, sum(alpha[t][s] * beta[t][s] for s in range(k)))
            for s in range(k):
                gamma[t][s] = alpha[t][s] * beta[t][s] / denom

        xi_sum = [[0.0] * k for _ in range(k)]
        for t in range(len(obs) - 1):
            denom = max(1e-15, sum(
                alpha[t][i] * trans[i][j] * emit[j][obs[t + 1]] * beta[t + 1][j]
                for i in range(k) for j in range(k)
            ))
            for i in range(k):
                for j in range(k):
                    xi_sum[i][j] += (
                        alpha[t][i] * trans[i][j] * emit[j][obs[t + 1]] * beta[t + 1][j]
                    ) / denom

        pi = [0.5 * 0.5 + 0.5 * gamma[0][s] for s in range(k)]
        pi_total = sum(pi)
        pi = [v / pi_total for v in pi]
        for i in range(k):
            row = []
            for j in range(k):
                prior = 2.0 if i == j else 1.0
                row.append(xi_sum[i][j] + prior)
            total = sum(row)
            trans[i] = [v / total for v in row]
        for s in range(k):
            row = []
            for r in range(m):
                row.append(sum(gamma[t][s] for t, value in enumerate(obs) if value == r) + 1.5)
            total = sum(row)
            emit[s] = [v / total for v in row]

        last_log_likelihood = sum(math.log(max(1e-15, x)) for x in scales)

    posterior = alpha[-1]
    next_hidden = [sum(posterior[i] * trans[i][j] for i in range(k)) for j in range(k)]
    residue = [sum(next_hidden[s] * emit[s][r] for s in range(k)) for r in range(m)]
    total = sum(residue)
    residue = [v / total for v in residue]
    return tuple(residue), {
        "status": "ok",
        "observations": len(obs),
        "hidden_states": 2,
        "residue_classes": 7,
        "filtered_state": [round(v, 6) for v in posterior],
        "next_state": [round(v, 6) for v in next_hidden],
        "next_residue": [round(v, 6) for v in residue],
        "log_likelihood": round(float(last_log_likelihood or 0.0), 6),
    }


def _extra_hmm_probs(draws: Sequence[Draw]) -> Tuple[Dict[int, float], dict]:
    """Forecast exact Extra numbers via HMM residue regime + shrunk within-residue odds."""
    residue, context = _hmm_residue_forecast(tuple(d.extra for d in draws))
    if context.get("status") != "ok":
        return {n: P_EXTRA for n in ALL_NUMBERS}, context
    within = _extra_bayes_probs(draws, window=160, prior_strength=98.0)
    residue_totals = {
        r: sum(within[n] for n in ALL_NUMBERS if (n - 1) % 7 == r)
        for r in range(7)
    }
    probs = {
        n: residue[(n - 1) % 7] * within[n] / residue_totals[(n - 1) % 7]
        for n in ALL_NUMBERS
    }
    return _normalize_distribution(probs), context


@lru_cache(maxsize=512)
def _legacy_mes_v1_cached(draw_tuple: Tuple[Draw, ...]) -> Tuple[Tuple[float, ...], dict]:
    """Reproduce the prior MES-v1 ensemble as one intact arena candidate."""
    draws = draw_tuple
    if not draws:
        return tuple(P_EXTRA for _ in ALL_NUMBERS), {"status": "no_history"}
    current = {
        "bayes": _extra_bayes_probs(draws),
        "ewma": _extra_multiscale_ewma_probs(draws),
        "transition": _extra_transition_probs(draws)[0],
    }
    if len(draws) <= 60:
        weights = dict(LEGACY_MES_V1_WEIGHTS)
        validation = {"validation_steps": 0, "status": "history_too_short"}
    else:
        start = max(60, len(draws) - 36)
        losses = {name: [] for name in LEGACY_MES_V1_WEIGHTS}
        for t in range(start, len(draws)):
            prefix = draws[:t]
            comps = {
                "bayes": _extra_bayes_probs(prefix),
                "ewma": _extra_multiscale_ewma_probs(prefix),
                "transition": _extra_transition_probs(prefix)[0],
            }
            actual = draws[t].extra
            for name, probs in comps.items():
                losses[name].append(-math.log(max(1e-12, probs[actual])))
        baseline = math.log(49)
        mean_loss = {name: sum(vals) / len(vals) for name, vals in losses.items()}
        raw_weights = {}
        for name, base_weight in LEGACY_MES_V1_WEIGHTS.items():
            regret = baseline - mean_loss.get(name, baseline)
            multiplier = math.exp(min(0.8, max(-0.8, 6.0 * regret)))
            raw_weights[name] = base_weight * multiplier
        total = sum(raw_weights.values())
        weights = {name: raw_weights[name] / total for name in raw_weights}
        validation = {
            "validation_steps": len(draws) - start,
            "component_log_loss": {k: round(v, 6) for k, v in mean_loss.items()},
            "status": "legacy_nested_prequential",
        }
    ensemble = _normalize_distribution({
        n: sum(weights[name] * current[name][n] for name in weights)
        for n in ALL_NUMBERS
    })
    return tuple(ensemble[n] for n in ALL_NUMBERS), {
        "weights": {k: round(v, 6) for k, v in weights.items()},
        "validation": validation,
    }


def _legacy_mes_v1_probs(draws: Sequence[Draw]) -> Tuple[Dict[int, float], dict]:
    probs, context = _legacy_mes_v1_cached(tuple(draws))
    return {n: probs[n - 1] for n in ALL_NUMBERS}, context


def _extra_math_components(draws: Sequence[Draw]) -> Tuple[Dict[str, Dict[int, float]], dict]:
    mes_v1, legacy_context = _legacy_mes_v1_probs(draws)
    bayes = _extra_bayes_probs(draws)
    ewma = _extra_multiscale_ewma_probs(draws)
    transition, support = _extra_transition_probs(draws)
    hmm, hmm_context = _extra_hmm_probs(draws)
    return {"mes_v1": mes_v1, "bayes": bayes, "ewma": ewma, "transition": transition, "hmm": hmm}, {
        "legacy_mes_v1": legacy_context,
        "transition_support": support,
        "hmm": hmm_context,
    }


def _entropy_efficiency(probs: Dict[int, float]) -> float:
    entropy = -sum(p * math.log(p) for p in probs.values() if p > 0)
    return entropy / math.log(49)


def _js_divergence(a: Dict[int, float], b: Dict[int, float]) -> float:
    a = _normalize_distribution(a)
    b = _normalize_distribution(b)
    m = {n: 0.5 * (a[n] + b[n]) for n in ALL_NUMBERS}

    def kl(x: Dict[int, float], y: Dict[int, float]) -> float:
        return sum(x[n] * math.log(x[n] / y[n]) for n in ALL_NUMBERS if x[n] > 0)

    return 0.5 * kl(a, m) + 0.5 * kl(b, m)


def _extra_regime_diagnostics(draws: Sequence[Draw]) -> dict:
    """Entropy and recent-vs-prior drift diagnostics; descriptive, never a probability claim."""
    posterior = _extra_bayes_probs(draws)
    recent = draws[-80:]
    if len(recent) >= 40:
        cut = len(recent) // 2
        prior = _extra_bayes_probs(recent[:cut], window=cut, prior_strength=49.0)
        newer = _extra_bayes_probs(recent[cut:], window=len(recent) - cut, prior_strength=49.0)
        drift = _js_divergence(prior, newer)
    else:
        drift = 0.0
    return {
        "entropy_efficiency": round(_entropy_efficiency(posterior), 6),
        "recent_prior_js_divergence": round(drift, 6),
    }


def _adaptive_mes_weights(
    draws: Sequence[Draw], validation_steps: int = MES_ARENA_VALIDATION_STEPS, min_train: int = MES_ARENA_MIN_TRAIN
) -> Tuple[Dict[str, float], dict]:
    """MES-v2 model arena using a nested prequential slice of available past only.

    A component that loses to the uniform null on both multiclass log-loss and Top5 hit
    rate is eliminated for this target. A component winning only one test is downweighted.
    This is deliberately conservative and can fall all the way back to a uniform math model.
    """
    if len(draws) <= min_train:
        return dict(MES_BASE_WEIGHTS), {
            "validation_steps": 0,
            "uniform_log_loss": round(math.log(49), 6),
            "component_log_loss": {},
            "component_top5_rate": {},
            "component_status": {},
            "status": "history_too_short_for_model_arena",
        }
    start = max(min_train, len(draws) - validation_steps)
    losses = {name: [] for name in MES_BASE_WEIGHTS}
    top5_hits = {name: [] for name in MES_BASE_WEIGHTS}
    for t in range(start, len(draws)):
        comps, _ = _extra_math_components(draws[:t])
        actual = draws[t].extra
        for name, probs in comps.items():
            losses[name].append(-math.log(max(1e-12, probs[actual])))
            ranked = sorted(ALL_NUMBERS, key=lambda n: (-probs[n], n))[:5]
            top5_hits[name].append(actual in ranked)
    mean_loss = {name: sum(vals) / len(vals) for name, vals in losses.items() if vals}
    top5_rate = {name: sum(vals) / len(vals) for name, vals in top5_hits.items() if vals}
    baseline = math.log(49)
    top5_baseline = 5 / 49
    raw_weights = {}
    component_status = {}
    for name, base_weight in MES_BASE_WEIGHTS.items():
        loss = mean_loss.get(name, baseline)
        rate5 = top5_rate.get(name, top5_baseline)
        loss_wins = loss < baseline
        top5_wins = rate5 > top5_baseline
        regret = baseline - loss
        top5_lift = rate5 - top5_baseline
        if not loss_wins and not top5_wins:
            multiplier = 0.0
            component_status[name] = "eliminated_below_uniform"
        elif loss_wins and top5_wins:
            multiplier = math.exp(min(0.8, max(-0.4, 4.0 * regret + 1.5 * top5_lift)))
            component_status[name] = "active"
        else:
            multiplier = 0.25 * math.exp(min(0.4, max(-0.6, 3.0 * regret + top5_lift)))
            component_status[name] = "downweighted_mixed_evidence"
        raw_weights[name] = base_weight * multiplier
    total = sum(raw_weights.values())
    if total <= 1e-15:
        weights = {name: 0.0 for name in raw_weights}
        weighted_loss = baseline
        arena_status = "all_candidates_eliminated_use_uniform"
    else:
        weights = {name: raw_weights[name] / total for name in raw_weights}
        weighted_loss = sum(weights[name] * mean_loss.get(name, baseline) for name in weights)
        arena_status = "active_candidates"
    return weights, {
        "validation_steps": len(draws) - start,
        "uniform_log_loss": round(baseline, 6),
        "uniform_top5_rate": round(top5_baseline, 6),
        "component_log_loss": {k: round(v, 6) for k, v in mean_loss.items()},
        "component_top5_rate": {k: round(v, 6) for k, v in top5_rate.items()},
        "component_status": component_status,
        "weighted_component_log_loss": round(weighted_loss, 6),
        "inner_lift_vs_uniform_log_loss": round(baseline - weighted_loss, 6),
        "status": arena_status,
    }


def special_number_mes_scores(draws: Sequence[Draw]) -> Tuple[Dict[int, float], dict]:
    """MES-v2: four candidate math models gated by a nested leakage-free arena."""
    if not draws:
        return {n: 50.0 for n in ALL_NUMBERS}, {"status": "no_history"}
    components, component_context = _extra_math_components(draws)
    weights, validation = _adaptive_mes_weights(draws)
    if sum(weights.values()) <= 1e-15:
        ensemble = {n: P_EXTRA for n in ALL_NUMBERS}
    else:
        ensemble = {n: sum(weights[name] * components[name][n] for name in weights) for n in ALL_NUMBERS}
    ensemble = _normalize_distribution(ensemble)
    # Ranking score only: log lift is monotonic in probability and keeps tiny differences visible.
    scores = minmax({n: math.log(ensemble[n] / P_EXTRA) for n in ALL_NUMBERS})
    diagnostics = {
        "model": "MES-v2",
        "base_weights": MES_BASE_WEIGHTS,
        "arena_weights": {k: round(v, 6) for k, v in weights.items()},
        "arena": validation,
        "regime": _extra_regime_diagnostics(draws),
        **component_context,
        "note": "分数用于排序，不是开奖号概率；竞技场只看目标期之前的内层走步，候选模型可被降权或归零。",
    }
    return scores, diagnostics


def math_scores(draws: Sequence[Draw], window: int = 120, half_life: float = 30.0) -> Dict[int, float]:
    if not draws:
        return {n: 50.0 for n in ALL_NUMBERS}
    recent = draws[-window:]
    counts = Counter(n for d in recent for n in d.main)
    n_draws = len(recent)
    expected = n_draws * P_MAIN
    sd = math.sqrt(max(1e-12, n_draws * P_MAIN * (1 - P_MAIN)))
    shrink = n_draws / (n_draws + 50.0)
    alpha = 1 - 0.5 ** (1 / half_life)
    ewma = {n: P_MAIN for n in ALL_NUMBERS}
    for d in draws:
        present = set(d.main)
        for n in ALL_NUMBERS:
            ewma[n] = (1 - alpha) * ewma[n] + alpha * (1.0 if n in present else 0.0)
    ewma_sd = math.sqrt(max(1e-12, P_MAIN * (1 - P_MAIN) * alpha / (2 - alpha)))
    mean_gap = (1 - P_MAIN) / P_MAIN
    gap_sd = math.sqrt(1 - P_MAIN) / P_MAIN
    raw: Dict[int, float] = {}
    for n in ALL_NUMBERS:
        freq_z = ((counts[n] - expected) / sd) * shrink
        ewma_z = (ewma[n] - P_MAIN) / ewma_sd
        gap = 0
        for d in reversed(draws):
            if n in d.main:
                break
            gap += 1
        gap_z = (gap - mean_gap) / gap_sd
        raw[n] = 0.45 * clamp(freq_z) + 0.45 * clamp(ewma_z) + 0.10 * clamp(gap_z)
    return minmax(raw)


def special_number_math_scores(
    draws: Sequence[Draw], window: int = 120, half_life: float = 30.0
) -> Dict[int, float]:
    """Score the Extra Number (潮汕俗称特码) using prior Extra Numbers only."""
    if not draws:
        return {n: 50.0 for n in ALL_NUMBERS}
    recent = draws[-window:]
    counts = Counter(d.extra for d in recent)
    n_draws = len(recent)
    expected = n_draws * P_EXTRA
    sd = math.sqrt(max(1e-12, n_draws * P_EXTRA * (1 - P_EXTRA)))
    shrink = n_draws / (n_draws + 80.0)
    alpha = 1 - 0.5 ** (1 / half_life)
    ewma = {n: P_EXTRA for n in ALL_NUMBERS}
    for d in draws:
        for n in ALL_NUMBERS:
            ewma[n] = (1 - alpha) * ewma[n] + alpha * (1.0 if d.extra == n else 0.0)
    ewma_sd = math.sqrt(max(1e-12, P_EXTRA * (1 - P_EXTRA) * alpha / (2 - alpha)))
    raw: Dict[int, float] = {}
    for n in ALL_NUMBERS:
        freq_z = ((counts[n] - expected) / sd) * shrink
        ewma_z = (ewma[n] - P_EXTRA) / ewma_sd
        raw[n] = 0.50 * clamp(freq_z) + 0.50 * clamp(ewma_z)
    return minmax(raw)


def zodiac_math_scores(
    draws: Sequence[Draw], target: datetime, window: int = 120, half_life: float = 30.0
) -> Dict[str, float]:
    """Score historical Extra-Number zodiac frequency with changing lunar-year tables."""
    if not draws:
        return {z: 50.0 for z in ZODIACS}
    recent = draws[-window:]
    counts = Counter(zodiac_of_number(d.extra, d.date) for d in recent)
    expected = {z: 0.0 for z in ZODIACS}
    variance = {z: 0.0 for z in ZODIACS}
    for d in recent:
        table = zodiac_table(d.date)
        for z in ZODIACS:
            p = len(table[z]) / 49
            expected[z] += p
            variance[z] += p * (1 - p)
    shrink = len(recent) / (len(recent) + 60.0)
    alpha = 1 - 0.5 ** (1 / half_life)
    residual_ewma = {z: 0.0 for z in ZODIACS}
    ewma_var = {z: 0.0 for z in ZODIACS}
    for d in draws:
        table = zodiac_table(d.date)
        actual = zodiac_of_number(d.extra, d.date)
        for z in ZODIACS:
            p = len(table[z]) / 49
            residual_ewma[z] = (1 - alpha) * residual_ewma[z] + alpha * ((1.0 if actual == z else 0.0) - p)
            ewma_var[z] = (1 - alpha) * ewma_var[z] + alpha * p * (1 - p)
    raw: Dict[str, float] = {}
    for z in ZODIACS:
        freq_z = ((counts[z] - expected[z]) / math.sqrt(max(1e-12, variance[z]))) * shrink
        ewma_sd = math.sqrt(max(1e-12, ewma_var[z] * alpha / (2 - alpha)))
        ewma_z = residual_ewma[z] / ewma_sd
        raw[z] = 0.50 * clamp(freq_z) + 0.50 * clamp(ewma_z)
    return minmax(raw)  # type: ignore[arg-type, return-value]


def hetu_element(n: int) -> str:
    digit = n % 10
    if digit in (1, 6):
        return "水"
    if digit in (2, 7):
        return "火"
    if digit in (3, 8):
        return "木"
    if digit in (4, 9):
        return "金"
    return "土"


def palace_of(n: int) -> int:
    return (n - 1) % 9 + 1


def digital_root(n: int) -> int:
    return (n - 1) % 9 + 1 if n > 0 else 9


def element_relation_score(candidate: str, fields: Sequence[str]) -> float:
    parts = []
    for field in fields:
        if candidate == field:
            parts.append(1.0)
        elif SHENG[field] == candidate:
            parts.append(0.65)
        elif SHENG[candidate] == field:
            parts.append(0.35)
        elif KE[field] == candidate:
            parts.append(-0.35)
        elif KE[candidate] == field:
            parts.append(-0.20)
        else:
            parts.append(0.0)
    return sum(parts) / max(1, len(parts))


def _keyword_element(value: object, mapping: Dict[str, Tuple[str, ...]]) -> Optional[str]:
    text = str(value or "").strip().lower()
    if not text:
        return None
    for element, keywords in mapping.items():
        if any(keyword.lower() in text for keyword in keywords):
            return element
    return None


def parse_omen_input(value: Optional[str]) -> Optional[dict]:
    """Parse inline JSON or a JSON file path for a one-shot external-omen observation."""
    if not value:
        return None
    candidate = Path(value)
    try:
        payload = candidate.read_text(encoding="utf-8") if candidate.is_file() else value
        obj = json.loads(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法解析 --omen-json: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError("--omen-json 必须是 JSON 对象")
    return obj


def _first_positive_int(value: object) -> Optional[int]:
    match = re.search(r"\d+", str(value or ""))
    if not match:
        return None
    number = int(match.group(0))
    return number if number > 0 else None


def _zodiac_keyword(value: object) -> Optional[str]:
    text = str(value or "")
    return next((z for z in ZODIACS if z in text), None)


def omen_scores(
    omen: Optional[dict], target: Optional[datetime] = None
) -> Tuple[Optional[Dict[int, float]], dict, List[str]]:
    """Encode a frozen pre-forecast observation as a separate cultural heuristic.

    Unknown objects/text are left unscored instead of being hashed into arbitrary numbers.
    Pro fields extend the original left/right/color/number protocol without changing its cap.
    """
    if not omen:
        return None, {}, []
    aliases = {
        "left_object": ("left_object", "左物", "左边物品"),
        "left_color": ("left_color", "左色", "左边颜色"),
        "right_object": ("right_object", "右物", "右边物品"),
        "right_color": ("right_color", "右色", "右边颜色"),
        "direction": ("direction", "方位", "朝向"),
        "number": ("number", "数字", "第一数字"),
        "count": ("count", "数量", "声音次数"),
        "first_sight": ("first_sight", "第一眼", "第一眼物品", "第一眼看到"),
        "first_sound": ("first_sound", "第一声", "第一声声音", "听到的声音"),
        "person_animal": ("person_animal", "人动物", "突然出现的人动物", "动物"),
        "movement": ("movement", "运动方向", "移动方向"),
        "weather": ("weather", "天气"),
        "location_direction": ("location_direction", "所在方位", "位置方位"),
        "phone_number": ("phone_number", "手机数字", "手机第一眼数字"),
        "random_text": ("random_text", "随机文字", "第一眼文字"),
        "observation_time": ("observation_time", "观察时间", "发生时间"),
    }

    def get(name: str):
        for key in aliases[name]:
            if key in omen and omen[key] not in (None, ""):
                return omen[key]
        return None

    fields: List[Tuple[str, float, str]] = []
    warnings: List[str] = []
    recognized = []
    left_object, right_object = get("left_object"), get("right_object")
    left_color, right_color = get("left_color"), get("right_color")
    direction = get("direction")
    first_sight = get("first_sight")
    first_sound = get("first_sound")
    weather = get("weather")
    movement = get("movement")
    location_direction = get("location_direction")
    random_text = get("random_text")
    for value, mapping, weight, source in (
        (left_object, OBJECT_ELEMENT_KEYWORDS, 0.85, "左物"),
        (left_color, COLOR_ELEMENT_KEYWORDS, 1.00, "左色"),
        (right_object, OBJECT_ELEMENT_KEYWORDS, 0.70, "右物"),
        (right_color, COLOR_ELEMENT_KEYWORDS, 0.85, "右色"),
        (first_sight, OBJECT_ELEMENT_KEYWORDS, 0.75, "第一眼物品"),
        (first_sound, SOUND_ELEMENT_KEYWORDS, 0.55, "第一声声音"),
        (weather, WEATHER_ELEMENT_KEYWORDS, 0.50, "天气"),
    ):
        if value is None:
            continue
        element = _keyword_element(value, mapping)
        if element:
            fields.append((element, weight, source))
            recognized.append({"source": source, "value": str(value), "element": element, "weight": weight})
        elif source.endswith("物") or source in ("第一声声音", "天气"):
            warnings.append(f"外应未识别{source}“{value}”的五行，未强行编码")
    if left_object is not None or left_color is not None:
        fields.append(("木", 0.20, "左/青龙位"))
        recognized.append({"source": "左/青龙位", "element": "木", "weight": 0.20})
    if right_object is not None or right_color is not None:
        fields.append(("金", 0.15, "右/白虎位"))
        recognized.append({"source": "右/白虎位", "element": "金", "weight": 0.15})
    for direction_value, source, weight in (
        (direction, "朝向", 0.90),
        (movement, "运动方向", 0.60),
        (location_direction, "所在方位", 0.65),
    ):
        if direction_value is None:
            continue
        direction_text = str(direction_value).strip()
        element = next((
            DIRECTION_ELEMENT[key]
            for key in sorted(DIRECTION_ELEMENT, key=len, reverse=True)
            if key in direction_text
        ), None)
        if element:
            fields.append((element, weight, source))
            recognized.append({"source": source, "value": direction_text, "element": element, "weight": weight})
        else:
            warnings.append(f"外应未识别{source}“{direction_value}”，未强行编码")

    # Random text is accepted only when it contains an explicit element/color/material cue.
    if random_text is not None:
        explicit_map = {e: (e,) for e in ("木", "火", "土", "金", "水")}
        element = (
            _keyword_element(random_text, explicit_map)
            or _keyword_element(random_text, COLOR_ELEMENT_KEYWORDS)
            or _keyword_element(random_text, OBJECT_ELEMENT_KEYWORDS)
        )
        if element:
            fields.append((element, 0.35, "随机文字"))
            recognized.append({"source": "随机文字", "value": str(random_text), "element": element, "weight": 0.35})
        else:
            warnings.append(f"外应随机文字“{random_text}”无明确五行/颜色/材质词，未强行编码")

    seen_number = get("number")
    phone_number = get("phone_number")
    count = get("count")
    try:
        seen_number_int = int(seen_number) if seen_number is not None else None
    except (TypeError, ValueError):
        seen_number_int = None
        warnings.append(f"外应数字“{seen_number}”不是整数，已忽略")
    try:
        count_int = int(count) if count is not None else None
    except (TypeError, ValueError):
        count_int = None
        warnings.append(f"外应数量“{count}”不是整数，已忽略")

    phone_number_int = _first_positive_int(phone_number) if phone_number is not None else None
    if phone_number is not None and phone_number_int is None:
        warnings.append(f"手机第一眼数字“{phone_number}”没有可识别正整数，已忽略")

    direct_zodiacs: List[Tuple[str, float, str]] = []
    for value, weight, source in (
        (get("person_animal"), 0.75, "出现的人/动物"),
        (random_text, 0.35, "随机文字生肖"),
    ):
        if value is None:
            continue
        z = _zodiac_keyword(value)
        if z:
            direct_zodiacs.append((z, weight, source))
            recognized.append({"source": source, "value": str(value), "zodiac": z, "weight": weight})

    observation_time = get("observation_time")
    observation_palace = None
    observation_hour_zodiac = None
    if observation_time is not None:
        text_time = str(observation_time).strip()
        try:
            if re.fullmatch(r"\d{1,2}:\d{2}", text_time):
                hour, minute = (int(x) for x in text_time.split(":"))
            else:
                obs_dt = datetime.fromisoformat(text_time.replace("/", "-"))
                hour, minute = obs_dt.hour, obs_dt.minute
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("time range")
            observation_palace = digital_root(hour * 100 + minute)
            branch_index = ((hour + 1) // 2) % 12
            observation_hour_zodiac = ZODIACS[branch_index]
            fields.append((BRANCH_ELEMENT[BRANCHES[branch_index]], 0.30, "观察时辰"))
            direct_zodiacs.append((observation_hour_zodiac, 0.20, "观察时支"))
            recognized.append({
                "source": "观察时间", "value": text_time, "palace": observation_palace,
                "hour_zodiac": observation_hour_zodiac,
            })
        except (TypeError, ValueError):
            warnings.append(f"外应观察时间“{observation_time}”无法解析，已忽略")

    raw = {n: 0.0 for n in ALL_NUMBERS}
    total_field_weight = sum(weight for _, weight, _ in fields)
    for n in ALL_NUMBERS:
        if total_field_weight:
            raw[n] += sum(
                weight * element_relation_score(hetu_element(n), [element])
                for element, weight, _ in fields
            ) / total_field_weight
        for observed_number, weight in ((seen_number_int, 1.0), (phone_number_int, 0.65)):
            if observed_number is None or observed_number <= 0:
                continue
            if 1 <= observed_number <= 49 and n == observed_number:
                raw[n] += 1.00 * weight
            if palace_of(n) == palace_of(observed_number):
                raw[n] += 0.45 * weight
            if (n - 1) % 12 == (observed_number - 1) % 12:
                raw[n] += 0.20 * weight
        if count_int is not None and count_int > 0 and palace_of(n) == digital_root(count_int):
            raw[n] += 0.35
        if observation_palace is not None and palace_of(n) == observation_palace:
            raw[n] += 0.20
        if target is not None:
            for zodiac, weight, _ in direct_zodiacs:
                if zodiac_of_number(n, target) == zodiac:
                    raw[n] += 0.55 * weight

    if not fields and seen_number_int is None and phone_number_int is None and count_int is None and not direct_zodiacs:
        warnings.append("外应输入没有可编码字段，因此未参与融合")
        return None, {"input": omen, "recognized": recognized}, warnings
    return minmax(raw), {
        "input": omen,
        "recognized": recognized,
        "seen_number": seen_number_int,
        "phone_number": phone_number_int,
        "count": count_int,
        "direct_zodiacs": [
            {"zodiac": z, "weight": w, "source": source} for z, w, source in direct_zodiacs
        ],
        "observation_palace": observation_palace,
        "observation_hour_zodiac": observation_hour_zodiac,
        "hybrid_cap": OMEN_HYBRID_WEIGHT,
        "protocol": "开奖预测前一次性冻结观察；不因看到候选结果而重选现场信息",
    }, warnings


def helu_scores(target: datetime) -> Tuple[Dict[int, float], dict]:
    primary = digital_root(target.year + target.month + target.day)
    secondary = digital_root(target.year + target.month + target.day + target.hour)
    field_elements = [PALACE_ELEMENT[primary], PALACE_ELEMENT[secondary]]
    raw = {}
    for n in ALL_NUMBERS:
        p = palace_of(n)
        v = element_relation_score(hetu_element(n), field_elements)
        if p == primary:
            v += 1.0
        if p == secondary:
            v += 0.6
        if PALACE_ELEMENT[p] == PALACE_ELEMENT[primary]:
            v += 0.2
        raw[n] = v
    return minmax(raw), {"主宫": primary, "辅宫": secondary, "主宫五行": PALACE_ELEMENT[primary]}


def _lunar_context(target: datetime) -> Tuple[Optional[dict], Optional[str]]:
    try:
        from lunar_python import Solar  # type: ignore
    except ImportError:
        return None, "缺少 lunar_python：精确干支、梅花时间卦、奇门时盘特征未计算"
    try:
        lunar = Solar.fromYmdHms(target.year, target.month, target.day, target.hour, target.minute, 0).getLunar()
        year_gz = lunar.getYearInGanZhiExact()
        month_gz = lunar.getMonthInGanZhiExact()
        day_gz = lunar.getDayInGanZhiExact()
        hour_gz = lunar.getTimeInGanZhi()
        return {
            "lunar": lunar,
            "四柱": [year_gz, month_gz, day_gz, hour_gz],
            "农历年干支": lunar.getYearInGanZhi(),
            "农历生肖": lunar.getYearShengXiao(),
            "农历月": abs(lunar.getMonth()),
            "农历日": lunar.getDay(),
            "年支序": BRANCHES.index(year_gz[1]) + 1,
            "时支序": BRANCHES.index(hour_gz[1]) + 1,
        }, None
    except Exception as exc:
        return None, f"历法换算失败: {exc}"


@lru_cache(maxsize=4096)
def zodiac_mapping(target: datetime) -> Tuple[str, Tuple[Tuple[str, Tuple[int, ...]], ...]]:
    """Return the folk Mark Six zodiac table for the lunar year of target.

    Number 1 maps to the lunar-year animal; increasing numbers walk backward
    through the traditional 12-animal cycle.  This is a folk/外围 convention,
    not an HKJC betting rule.
    """
    lunar_ctx, warning = _lunar_context(target)
    if not lunar_ctx:
        raise RuntimeError(warning or "无法取得农历生肖")
    year_zodiac = lunar_ctx["农历生肖"]
    year_idx = ZODIACS.index(year_zodiac)
    buckets = {z: [] for z in ZODIACS}
    for n in ALL_NUMBERS:
        z = ZODIACS[(year_idx - (n - 1)) % 12]
        buckets[z].append(n)
    frozen = tuple((z, tuple(buckets[z])) for z in ZODIACS)
    return year_zodiac, frozen


def zodiac_table(target: datetime) -> Dict[str, Tuple[int, ...]]:
    return dict(zodiac_mapping(target)[1])


def zodiac_of_number(number: int, target: datetime) -> str:
    for zodiac, numbers in zodiac_mapping(target)[1]:
        if number in numbers:
            return zodiac
    raise ValueError(f"号码不在 1-49: {number}")


def _zodiac_relation(a: str, b: str) -> float:
    """Small deterministic score for same/六合/三合/冲 relations."""
    if a == b:
        return 0.80
    if ZODIAC_LIUHE[a] == b:
        return 0.65
    if any(a in group and b in group for group in ZODIAC_TRINES):
        return 0.40
    if ZODIAC_CHONG[a] == b:
        return -0.60
    return 0.0


def ganzi_scores(ctx: dict) -> Tuple[Dict[int, float], dict]:
    year_gz, month_gz, day_gz, hour_gz = ctx["四柱"]
    fields = [STEM_ELEMENT[day_gz[0]], STEM_ELEMENT[hour_gz[0]], BRANCH_ELEMENT[day_gz[1]], BRANCH_ELEMENT[hour_gz[1]]]
    raw = {n: element_relation_score(hetu_element(n), fields) for n in ALL_NUMBERS}
    return minmax(raw), {"四柱": ctx["四柱"], "日时五行场": fields}


def _mod(n: int, base: int) -> int:
    r = n % base
    return r if r else base


def meihua_scores(ctx: dict) -> Tuple[Dict[int, float], dict]:
    total = ctx["年支序"] + ctx["农历月"] + ctx["农历日"]
    up_num = _mod(total, 8)
    down_num = _mod(total + ctx["时支序"], 8)
    moving = _mod(total + ctx["时支序"], 6)
    up, down = TRIGRAM[up_num], TRIGRAM[down_num]
    if moving <= 3:
        body, use = up, down
    else:
        body, use = down, up
    body_el, use_el = TRIGRAM_ELEMENT[body], TRIGRAM_ELEMENT[use]
    raw = {}
    for n in ALL_NUMBERS:
        v = 0.0
        cls8 = _mod(n, 8)
        cls6 = _mod(n, 6)
        if cls8 == up_num:
            v += 0.75
        if cls8 == down_num:
            v += 0.65
        if cls6 == moving:
            v += 0.30
        elem = hetu_element(n)
        if elem == body_el:
            v += 0.55
        if elem == use_el:
            v += 0.35
        raw[n] = v
    return minmax(raw), {
        "上卦": f"{up}({up_num})", "下卦": f"{down}({down_num})", "动爻": moving,
        "体": f"{body}({body_el})", "用": f"{use}({use_el})",
    }


def _solar_to_datetime(solar) -> datetime:
    return datetime(solar.getYear(), solar.getMonth(), solar.getDay(), solar.getHour(), solar.getMinute(), solar.getSecond())


def qimen_scores(ctx: dict, target: datetime) -> Tuple[Dict[int, float], dict]:
    lunar = ctx["lunar"]
    candidates = []
    for name, solar in lunar.getJieQiTable().items():
        if name in QIMEN_JU:
            dt = _solar_to_datetime(solar)
            if dt <= target:
                candidates.append((dt, name))
    if not candidates:
        raise ValueError("无法定位目标时刻之前的节气")
    term_time, term = max(candidates)
    yang, ju_table = QIMEN_JU[term]
    elapsed = max(0.0, (target - term_time).total_seconds() / 86400.0)
    yuan = min(2, int(elapsed // 5))
    ju = ju_table[yuan]
    earth: Dict[int, str] = {}
    for idx, stem in enumerate(QIMEN_STEMS):
        delta = idx if yang else -idx
        palace = (ju - 1 + delta) % 9 + 1
        earth[palace] = stem
    day_gz, hour_gz = ctx["四柱"][2], ctx["四柱"][3]
    fields = [STEM_ELEMENT[day_gz[0]], STEM_ELEMENT[hour_gz[0]]]
    raw = {}
    for n in ALL_NUMBERS:
        palace = palace_of(n)
        stem = earth[palace]
        v = element_relation_score(PALACE_ELEMENT[palace], fields)
        v += 0.45 * element_relation_score(STEM_ELEMENT[stem], fields)
        if stem in ("乙", "丙", "丁"):
            v += 0.75
        if palace == ju:
            v += 0.35
        raw[n] = v
    return minmax(raw), {
        "节气": term,
        "交节": term_time.isoformat(sep=" "),
        "遁": "阳遁" if yang else "阴遁",
        "元": ("上元", "中元", "下元")[yuan],
        "局": ju,
        "地盘": {str(k): v for k, v in sorted(earth.items())},
        "说明": "时家奇门地盘九宫实验特征；不是完整星门神断局",
    }


def metaphysics_scores(target: datetime) -> Tuple[Dict[int, float], Dict[str, Dict[int, float]], dict, List[str]]:
    components: Dict[str, Dict[int, float]] = {}
    context: dict = {}
    warnings: List[str] = []
    helu, helu_ctx = helu_scores(target)
    components["河洛"] = helu
    context["河洛"] = helu_ctx
    lunar_ctx, warning = _lunar_context(target)
    if warning:
        warnings.append(warning)
    if lunar_ctx:
        g, gc = ganzi_scores(lunar_ctx)
        m, mc = meihua_scores(lunar_ctx)
        components["干支"] = g
        components["梅花"] = m
        context["干支"] = gc
        context["梅花"] = mc
        try:
            q, qc = qimen_scores(lunar_ctx, target)
            components["奇门"] = q
            context["奇门"] = qc
        except Exception as exc:
            warnings.append(f"奇门特征未计算: {exc}")
    raw = {n: sum(comp[n] for comp in components.values()) / len(components) for n in ALL_NUMBERS}
    return minmax(raw), components, context, warnings


def zodiac_metaphysics_scores(
    target: datetime,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]], dict, List[str]]:
    """Project the four metaphysics families onto the current lunar-year zodiac table."""
    _, number_components, context, warnings = metaphysics_scores(target)
    table = zodiac_table(target)
    lunar_ctx, warning = _lunar_context(target)
    if warning and warning not in warnings:
        warnings.append(warning)
    components: Dict[str, Dict[str, float]] = {}
    for name, scores in number_components.items():
        projected = {
            z: sum(scores[n] for n in table[z]) / len(table[z])
            for z in ZODIACS
        }
        components[name] = minmax(projected)  # type: ignore[arg-type, assignment]

    # For 干支, add a direct animal-branch layer: day/hour relations plus five elements.
    # This is a transparent project convention, not a classical lottery rule.
    if lunar_ctx:
        day_gz, hour_gz = lunar_ctx["四柱"][2], lunar_ctx["四柱"][3]
        day_zodiac = ZODIACS[BRANCHES.index(day_gz[1])]
        hour_zodiac = ZODIACS[BRANCHES.index(hour_gz[1])]
        field_elements = [BRANCH_ELEMENT[day_gz[1]], BRANCH_ELEMENT[hour_gz[1]]]
        direct_raw = {
            z: (
                0.55 * element_relation_score(ZODIAC_ELEMENT[z], field_elements)
                + 0.30 * _zodiac_relation(z, day_zodiac)
                + 0.15 * _zodiac_relation(z, hour_zodiac)
            )
            for z in ZODIACS
        }
        direct = minmax(direct_raw)  # type: ignore[arg-type]
        if "干支" in components:
            components["干支"] = minmax({
                z: 0.50 * components["干支"][z] + 0.50 * direct[z]
                for z in ZODIACS
            })  # type: ignore[arg-type, assignment]
        else:
            components["干支"] = direct  # type: ignore[assignment]
        context["生肖干支"] = {
            "农历生肖": lunar_ctx["农历生肖"],
            "日支生肖": day_zodiac,
            "时支生肖": hour_zodiac,
            "说明": "生肖五行 + 日时支六合/三合/冲的实验评分",
        }

    raw = {
        z: sum(comp[z] for comp in components.values()) / len(components)
        for z in ZODIACS
    }
    return minmax(raw), components, context, warnings  # type: ignore[arg-type, return-value]


def _combine_named_scores(
    a: Dict[str, float], b: Dict[str, float], a_weight: float = 0.55
) -> Dict[str, float]:
    raw = {key: a_weight * a[key] + (1 - a_weight) * b[key] for key in a}
    return minmax(raw)  # type: ignore[arg-type, return-value]


def special_prediction(
    draws: Sequence[Draw], target: datetime, omen: Optional[dict] = None
) -> Tuple[
    Dict[str, Dict[int, float]],
    Dict[str, Dict[str, float]],
    Dict[str, Dict[str, float]],
    dict,
    List[str],
]:
    """Return math/meta/hybrid scores for Extra Number and Extra zodiac."""
    extra_math, math_diagnostics = special_number_mes_scores(draws)
    zodiac_history_math = zodiac_math_scores(draws, target)
    number_meta_base, number_meta_components, meta_context, warnings = metaphysics_scores(target)
    zodiac_meta, zodiac_components, zodiac_context, zodiac_warnings = zodiac_metaphysics_scores(target)
    warnings = list(dict.fromkeys(warnings + zodiac_warnings))
    meta_context.update(zodiac_context)
    table = zodiac_table(target)

    projected_mes = minmax({
        z: sum(extra_math[n] for n in table[z]) / len(table[z])
        for z in ZODIACS
    })
    zodiac_math = minmax({
        z: 0.60 * zodiac_history_math[z] + 0.40 * projected_mes[z]
        for z in ZODIACS
    })
    math_diagnostics["zodiac_blend"] = {
        "historical_zodiac": 0.60,
        "projected_mes_number_score": 0.40,
    }
    meta_context["数学MES"] = math_diagnostics

    number_math_raw = {}
    number_meta_raw = {}
    for n in ALL_NUMBERS:
        z = zodiac_of_number(n, target)
        number_math_raw[n] = 0.75 * extra_math[n] + 0.25 * zodiac_math[z]
        number_meta_raw[n] = 0.70 * number_meta_base[n] + 0.30 * zodiac_meta[z]
    number_math = minmax(number_math_raw)
    number_meta = minmax(number_meta_raw)
    number_component_blends: Dict[str, Dict[int, float]] = {}
    for name, component in number_meta_components.items():
        if name not in zodiac_components:
            continue
        number_component_blends[name] = minmax({
            n: 0.70 * component[n] + 0.30 * zodiac_components[name][zodiac_of_number(n, target)]
            for n in ALL_NUMBERS
        })
    meta_context["特码玄学分项"] = number_component_blends
    number_hybrid_base = combine_scores(number_math, number_meta)
    zodiac_hybrid_base = _combine_named_scores(zodiac_math, zodiac_meta)

    omen_number, omen_context, omen_warnings = omen_scores(omen, target)
    warnings = list(dict.fromkeys(warnings + omen_warnings))
    if omen_context:
        meta_context["外应"] = omen_context
    if omen_number:
        omen_zodiac = minmax({
            z: sum(omen_number[n] for n in table[z]) / len(table[z])
            for z in ZODIACS
        })
        number_hybrid = minmax({
            n: (1 - OMEN_HYBRID_WEIGHT) * number_hybrid_base[n] + OMEN_HYBRID_WEIGHT * omen_number[n]
            for n in ALL_NUMBERS
        })
        zodiac_hybrid = minmax({
            z: (1 - OMEN_HYBRID_WEIGHT) * zodiac_hybrid_base[z] + OMEN_HYBRID_WEIGHT * omen_zodiac[z]
            for z in ZODIACS
        })
    else:
        omen_number = {}
        omen_zodiac = {}
        number_hybrid = number_hybrid_base
        zodiac_hybrid = zodiac_hybrid_base
    number_scores = {
        "math": number_math,
        "metaphysics": number_meta,
        "hybrid_base": number_hybrid_base,
        "omen": omen_number,
        "hybrid": number_hybrid,
    }
    zodiac_scores = {
        "math": zodiac_math,
        "metaphysics": zodiac_meta,
        "hybrid_base": zodiac_hybrid_base,
        "omen": omen_zodiac,
        "hybrid": zodiac_hybrid,
    }
    meta_context["生肖映射"] = {
        "农历生肖": zodiac_mapping(target)[0],
        "号码": {z: list(table[z]) for z in ZODIACS},
        "切换口径": "农历新年，不按公历1月1日",
    }
    return number_scores, zodiac_scores, zodiac_components, meta_context, warnings


def combine_scores(math_s: Dict[int, float], meta_s: Dict[int, float], math_weight: float = 0.55) -> Dict[int, float]:
    raw = {n: math_weight * math_s[n] + (1 - math_weight) * meta_s[n] for n in ALL_NUMBERS}
    return minmax(raw)


def top_line(scores: Dict[int, float]) -> Tuple[int, ...]:
    return tuple(sorted(sorted(ALL_NUMBERS, key=lambda n: (-scores[n], n))[:6]))


def _weighted_line(scores: Dict[int, float], rng: random.Random) -> Tuple[int, ...]:
    pool = list(ALL_NUMBERS)
    chosen = []
    while len(chosen) < 6:
        weights = [math.exp((scores[n] - 50) / 24.0) for n in pool]
        pick = rng.choices(pool, weights=weights, k=1)[0]
        chosen.append(pick)
        pool.remove(pick)
    return tuple(sorted(chosen))


def line_stats(line: Sequence[int]) -> dict:
    return {
        "sum": sum(line),
        "odd": sum(n % 2 for n in line),
        "low_1_24": sum(n <= 24 for n in line),
        "adjacent_pairs": sum(1 for a, b in zip(line, line[1:]) if b == a + 1),
    }


def build_portfolio(math_s: Dict[int, float], meta_s: Dict[int, float], hybrid_s: Dict[int, float], tickets: int, seed: int) -> List[dict]:
    anchors = [("数学主导", top_line(math_s)), ("玄学主导", top_line(meta_s)), ("融合Top6", top_line(hybrid_s))]
    out: List[dict] = []
    seen = set()
    for label, line in anchors[:max(0, tickets)]:
        if line in seen:
            continue
        seen.add(line)
        out.append({"label": label, "numbers": list(line), "avg_hybrid": round(sum(hybrid_s[n] for n in line) / 6, 2), **line_stats(line)})
    rng = random.Random(seed)
    attempts = 0
    while len(out) < tickets and attempts < 2000:
        attempts += 1
        line = _weighted_line(hybrid_s, rng)
        if line in seen:
            continue
        max_overlap = max((len(set(line) & set(x["numbers"])) for x in out), default=0)
        if max_overlap > 3 and attempts < 1200:
            continue
        seen.add(line)
        out.append({"label": "融合分散", "numbers": list(line), "avg_hybrid": round(sum(hybrid_s[n] for n in line) / 6, 2), **line_stats(line)})
    return out


def probability_baseline() -> dict:
    combos = math.comb(49, 6)
    p_ge3 = sum(math.comb(6, k) * math.comb(43, 6 - k) / combos for k in range(3, 7))
    return {
        "all_main_combinations": combos,
        "first_prize_probability": 1 / combos,
        "first_prize_odds": f"1 / {combos:,}",
        "expected_main_matches": 36 / 49,
        "random_rate_ge3_main": p_ge3,
    }


def _one_prediction(train: Sequence[Draw], target: datetime) -> Tuple[Dict[int, float], Dict[int, float], Dict[int, float]]:
    ms = math_scores(train)
    meta, _, _, _ = metaphysics_scores(target)
    hy = combine_scores(ms, meta)
    return ms, meta, hy


def _metric_summary(values: List[int]) -> dict:
    if not values:
        return {"n": 0, "mean_hits": None, "rate_ge3": None, "hit_histogram": {}}
    hist = Counter(values)
    return {
        "n": len(values),
        "mean_hits": round(sum(values) / len(values), 6),
        "rate_ge3": round(sum(v >= 3 for v in values) / len(values), 6),
        "hit_histogram": {str(k): hist.get(k, 0) for k in range(7)},
    }


def backtest_draws(draws: Sequence[Draw], min_train: int = 100, max_steps: Optional[int] = None) -> dict:
    if len(draws) <= min_train:
        return {"status": "insufficient_history", "needed_prior_draws": min_train, "available": len(draws)}
    start = min_train
    if max_steps is not None:
        start = max(start, len(draws) - max_steps)
    hits = {"math": [], "metaphysics": [], "hybrid": []}
    for t in range(start, len(draws)):
        target_draw = draws[t]
        ms, meta, hy = _one_prediction(draws[:t], target_draw.date)
        actual = set(target_draw.main)
        hits["math"].append(len(actual & set(top_line(ms))))
        hits["metaphysics"].append(len(actual & set(top_line(meta))))
        hits["hybrid"].append(len(actual & set(top_line(hy))))
    baseline = probability_baseline()
    out = {name: _metric_summary(vals) for name, vals in hits.items()}
    out["random_baseline"] = {
        "expected_mean_hits": round(baseline["expected_main_matches"], 6),
        "rate_ge3": round(baseline["random_rate_ge3_main"], 6),
    }
    for name in ("math", "metaphysics", "hybrid"):
        out[name]["mean_lift_vs_random"] = round(out[name]["mean_hits"] - baseline["expected_main_matches"], 6)
    out["range"] = {"from": draws[start].date.date().isoformat(), "to": draws[-1].date.date().isoformat(), "steps": len(draws) - start}
    return out


def _top_keys(scores: Dict, n: int) -> List:
    return sorted(scores, key=lambda key: (-scores[key], str(key)))[:n]


def _rate(values: Sequence[bool]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _mc_tail_probability(
    observed_hits: int,
    null_probabilities: Sequence[float],
    label: str,
    trials: int = MONTE_CARLO_TRIALS,
) -> dict:
    """One-sided Monte Carlo P(null hits >= observed), with a deterministic research seed."""
    if not null_probabilities:
        return {"status": "no_samples"}
    seed = 20260808 + sum((i + 1) * ord(ch) for i, ch in enumerate(label))
    rng = random.Random(seed)
    ge = 0
    for _ in range(trials):
        hits = sum(1 for p in null_probabilities if rng.random() < p)
        if hits >= observed_hits:
            ge += 1
    return {
        "trials": trials,
        "observed_hits": observed_hits,
        "expected_random_hits": round(sum(null_probabilities), 4),
        "p_ge_observed": round((ge + 1) / (trials + 1), 6),
        "tail": "one-sided",
    }


def special_backtest_draws(
    draws: Sequence[Draw], min_train: int = 100, max_steps: Optional[int] = None
) -> dict:
    """Strict walk-forward backtest for Chaoshan-style Extra Number/zodiac research."""
    if len(draws) <= min_train:
        return {"status": "insufficient_history", "needed_prior_draws": min_train, "available": len(draws)}
    start = min_train
    if max_steps is not None:
        start = max(start, len(draws) - max_steps)
    model_names = ("math", "metaphysics", "hybrid")
    raw = {
        name: {
            "number_top1": [], "number_top5": [], "number_top10": [],
            "zodiac_top1": [], "zodiac_top3": [],
            "random_zodiac_top1": [], "random_zodiac_top3": [],
        }
        for name in model_names
    }
    arena_raw = {
        name: {"number_top1": [], "number_top5": [], "number_top10": []}
        for name in MES_BASE_WEIGHTS
    }
    for t in range(start, len(draws)):
        target_draw = draws[t]
        number_scores, zodiac_scores, _, _, _ = special_prediction(draws[:t], target_draw.date)
        actual_number = target_draw.extra
        actual_zodiac = zodiac_of_number(actual_number, target_draw.date)
        table = zodiac_table(target_draw.date)
        arena_components, _ = _extra_math_components(draws[:t])
        for component_name, probs in arena_components.items():
            ranked = sorted(ALL_NUMBERS, key=lambda n: (-probs[n], n))[:10]
            arena_raw[component_name]["number_top1"].append(actual_number == ranked[0])
            arena_raw[component_name]["number_top5"].append(actual_number in ranked[:5])
            arena_raw[component_name]["number_top10"].append(actual_number in ranked[:10])
        for name in model_names:
            ranked_numbers = _top_keys(number_scores[name], 10)
            ranked_zodiacs = _top_keys(zodiac_scores[name], 3)
            raw[name]["number_top1"].append(actual_number == ranked_numbers[0])
            raw[name]["number_top5"].append(actual_number in ranked_numbers[:5])
            raw[name]["number_top10"].append(actual_number in ranked_numbers[:10])
            raw[name]["zodiac_top1"].append(actual_zodiac == ranked_zodiacs[0])
            raw[name]["zodiac_top3"].append(actual_zodiac in ranked_zodiacs[:3])
            raw[name]["random_zodiac_top1"].append(len(table[ranked_zodiacs[0]]) / 49)
            raw[name]["random_zodiac_top3"].append(
                sum(len(table[z]) for z in ranked_zodiacs[:3]) / 49
            )
    out = {
        "mode": "chaoshan-special",
        "status": "ok",
        "range": {
            "from": draws[start].date.date().isoformat(),
            "to": draws[-1].date.date().isoformat(),
            "steps": len(draws) - start,
            "min_train": min_train,
        },
        "fixed_random_baseline": {
            "number_top1": round(1 / 49, 6),
            "number_top5": round(5 / 49, 6),
            "number_top10": round(10 / 49, 6),
        },
    }
    for name in model_names:
        z1_base = sum(raw[name]["random_zodiac_top1"]) / len(raw[name]["random_zodiac_top1"])
        z3_base = sum(raw[name]["random_zodiac_top3"]) / len(raw[name]["random_zodiac_top3"])
        n1 = _rate(raw[name]["number_top1"])
        n5 = _rate(raw[name]["number_top5"])
        n10 = _rate(raw[name]["number_top10"])
        z1 = _rate(raw[name]["zodiac_top1"])
        z3 = _rate(raw[name]["zodiac_top3"])
        out[name] = {
            "number": {
                "top1_rate": n1,
                "top5_rate": n5,
                "top10_rate": n10,
                "top1_lift_pp_vs_random": round(100 * (n1 - 1 / 49), 3),
                "top5_lift_pp_vs_random": round(100 * (n5 - 5 / 49), 3),
                "top10_lift_pp_vs_random": round(100 * (n10 - 10 / 49), 3),
            },
            "zodiac": {
                "top1_rate": z1,
                "top3_rate": z3,
                "random_top1_rate": round(z1_base, 6),
                "random_top3_rate": round(z3_base, 6),
                "top1_lift_pp_vs_random": round(100 * (z1 - z1_base), 3),
                "top3_lift_pp_vs_random": round(100 * (z3 - z3_base), 3),
            },
            "monte_carlo": {
                "number_top1": _mc_tail_probability(
                    sum(raw[name]["number_top1"]), [1 / 49] * len(raw[name]["number_top1"]), f"{name}:n1"
                ),
                "number_top5": _mc_tail_probability(
                    sum(raw[name]["number_top5"]), [5 / 49] * len(raw[name]["number_top5"]), f"{name}:n5"
                ),
                "number_top10": _mc_tail_probability(
                    sum(raw[name]["number_top10"]), [10 / 49] * len(raw[name]["number_top10"]), f"{name}:n10"
                ),
                "zodiac_top1": _mc_tail_probability(
                    sum(raw[name]["zodiac_top1"]), raw[name]["random_zodiac_top1"], f"{name}:z1"
                ),
                "zodiac_top3": _mc_tail_probability(
                    sum(raw[name]["zodiac_top3"]), raw[name]["random_zodiac_top3"], f"{name}:z3"
                ),
            },
        }
    out["arena_components"] = {}
    for name, values in arena_raw.items():
        n1 = _rate(values["number_top1"])
        n5 = _rate(values["number_top5"])
        n10 = _rate(values["number_top10"])
        steps = len(values["number_top1"])
        out["arena_components"][name] = {
            "number": {
                "top1_rate": n1,
                "top5_rate": n5,
                "top10_rate": n10,
                "top1_lift_pp_vs_random": round(100 * (n1 - 1 / 49), 3),
                "top5_lift_pp_vs_random": round(100 * (n5 - 5 / 49), 3),
                "top10_lift_pp_vs_random": round(100 * (n10 - 10 / 49), 3),
            },
            "monte_carlo": {
                "number_top5": _mc_tail_probability(
                    sum(values["number_top5"]), [5 / 49] * steps, f"arena:{name}:n5"
                )
            },
        }
    total = len(draws) - start
    cuts = (0, total // 3, (2 * total) // 3, total)
    windows = []
    for wi in range(3):
        a, b = cuts[wi], cuts[wi + 1]
        if a == b:
            continue
        item = {
            "from": draws[start + a].date.date().isoformat(),
            "to": draws[start + b - 1].date.date().isoformat(),
            "steps": b - a,
        }
        for name in model_names:
            z1_base = sum(raw[name]["random_zodiac_top1"][a:b]) / (b - a)
            z3_base = sum(raw[name]["random_zodiac_top3"][a:b]) / (b - a)
            item[name] = {
                "number_top5": _rate(raw[name]["number_top5"][a:b]),
                "number_top10": _rate(raw[name]["number_top10"][a:b]),
                "zodiac_top1": _rate(raw[name]["zodiac_top1"][a:b]),
                "zodiac_top1_random": round(z1_base, 6),
                "zodiac_top3": _rate(raw[name]["zodiac_top3"][a:b]),
                "zodiac_top3_random": round(z3_base, 6),
            }
        windows.append(item)
    out["subwindows"] = windows
    return out


def special_analyze(draws: Sequence[Draw], target: datetime, omen: Optional[dict] = None) -> dict:
    cutoff_draws = [d for d in draws if d.date < target]
    if not cutoff_draws:
        raise ValueError("目标时间之前没有历史开奖数据")
    number_scores, zodiac_scores, zodiac_components, context, warnings = special_prediction(cutoff_draws, target, omen)
    table = zodiac_table(target)
    top_zodiacs = _top_keys(zodiac_scores["hybrid"], 6)
    top_numbers = _top_keys(number_scores["hybrid"], 15)
    number_components = context.get("特码玄学分项", {})
    z_rows = []
    for z in top_zodiacs:
        z_rows.append({
            "zodiac": z,
            "numbers": list(table[z]),
            "element": ZODIAC_ELEMENT[z],
            "math": round(zodiac_scores["math"][z], 2),
            "干支": round(zodiac_components.get("干支", {}).get(z, 0.0), 2) if "干支" in zodiac_components else None,
            "河洛": round(zodiac_components.get("河洛", {}).get(z, 0.0), 2) if "河洛" in zodiac_components else None,
            "梅花": round(zodiac_components.get("梅花", {}).get(z, 0.0), 2) if "梅花" in zodiac_components else None,
            "奇门": round(zodiac_components.get("奇门", {}).get(z, 0.0), 2) if "奇门" in zodiac_components else None,
            "metaphysics": round(zodiac_scores["metaphysics"][z], 2),
            "base_hybrid": round(zodiac_scores["hybrid_base"][z], 2),
            "omen": round(zodiac_scores["omen"].get(z, 0.0), 2) if zodiac_scores["omen"] else None,
            "hybrid": round(zodiac_scores["hybrid"][z], 2),
        })
    n_rows = []
    for n in top_numbers:
        z = zodiac_of_number(n, target)
        n_rows.append({
            "number": n,
            "zodiac": z,
            "element": hetu_element(n),
            "math": round(number_scores["math"][n], 2),
            "干支": round(number_components.get("干支", {}).get(n, 0.0), 2) if "干支" in number_components else None,
            "河洛": round(number_components.get("河洛", {}).get(n, 0.0), 2) if "河洛" in number_components else None,
            "梅花": round(number_components.get("梅花", {}).get(n, 0.0), 2) if "梅花" in number_components else None,
            "奇门": round(number_components.get("奇门", {}).get(n, 0.0), 2) if "奇门" in number_components else None,
            "metaphysics": round(number_scores["metaphysics"][n], 2),
            "base_hybrid": round(number_scores["hybrid_base"][n], 2),
            "omen": round(number_scores["omen"].get(n, 0.0), 2) if number_scores["omen"] else None,
            "hybrid": round(number_scores["hybrid"][n], 2),
        })
    backtest = special_backtest_draws(cutoff_draws, min_train=100, max_steps=150)
    return {
        "engine": "marksix-hybrid-forecast-v4-mes-v2",
        "mode": "chaoshan-special",
        "target": target.isoformat(sep=" ", timespec="minutes"),
        "data": {
            "draws_used": len(cutoff_draws),
            "from": cutoff_draws[0].date.date().isoformat(),
            "through": cutoff_draws[-1].date.date().isoformat(),
        },
        "target_lunar_zodiac": zodiac_mapping(target)[0],
        "zodiac_mapping": {z: list(table[z]) for z in ZODIACS},
        "top_zodiacs": z_rows,
        "top_special_numbers": n_rows,
        "metaphysics_context": context,
        "external_omen_enabled": bool(number_scores["omen"]),
        "external_omen_weight": OMEN_HYBRID_WEIGHT if number_scores["omen"] else 0.0,
        "warnings": warnings,
        "backtest": backtest,
        "interpretation": (
            "潮汕模式把香港六合彩 Extra Number 作为民间“特码”研究对象。"
            "数学MES-v2把贝叶斯、多尺度EWMA、转移和HMM放入内层走步模型竞技场，弱模型可自动降权或归零；"
            "历史回测同时用Monte Carlo随机模拟检查表面提升是否可能由运气产生。"
            "生肖/玄学/外应评分是实验特征，不改变公平开奖的随机概率；"
            "外应没有历史现场记录，因此不计入历史回测。"
        ),
    }


def _experiment_db(path: str) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS forecasts (
            target TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            engine TEXT NOT NULL,
            data_through TEXT NOT NULL,
            omen_json TEXT,
            prediction_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settlements (
            target TEXT PRIMARY KEY REFERENCES forecasts(target),
            settled_at TEXT NOT NULL,
            actual_extra INTEGER NOT NULL CHECK(actual_extra BETWEEN 1 AND 49),
            actual_zodiac TEXT NOT NULL
        );
        """
    )
    return conn


def _prediction_rankings(
    number_scores: Dict[str, Dict[int, float]],
    zodiac_scores: Dict[str, Dict[str, float]],
) -> dict:
    rankings = {}
    for name in ("math", "metaphysics", "hybrid_base", "hybrid"):
        rankings[name] = {
            "number_top10": _top_keys(number_scores[name], 10),
            "zodiac_top3": _top_keys(zodiac_scores[name], 3),
        }
    return rankings


def special_freeze_forecast(
    draws: Sequence[Draw], target: datetime, db_path: str, omen: Optional[dict] = None
) -> dict:
    """Persist an immutable pre-draw forecast for prospective validation."""
    cutoff = [d for d in draws if d.date < target]
    if not cutoff:
        raise ValueError("目标时间之前没有历史开奖数据")
    number_scores, zodiac_scores, _, context, warnings = special_prediction(cutoff, target, omen)
    target_key = target.isoformat(sep=" ", timespec="minutes")
    payload = {
        "target": target_key,
        "data_through": cutoff[-1].date.date().isoformat(),
        "draws_used": len(cutoff),
        "target_lunar_zodiac": zodiac_mapping(target)[0],
        "rankings": _prediction_rankings(number_scores, zodiac_scores),
        "arena": context.get("数学MES", {}).get("arena", {}),
        "arena_weights": context.get("数学MES", {}).get("arena_weights", {}),
        "omen_enabled": bool(number_scores.get("omen")),
        "warnings": warnings,
    }
    conn = _experiment_db(db_path)
    try:
        conn.execute(
            "INSERT INTO forecasts(target,created_at,engine,data_through,omen_json,prediction_json) VALUES(?,?,?,?,?,?)",
            (
                target_key,
                datetime.now().astimezone().isoformat(timespec="seconds"),
                "marksix-hybrid-forecast-v4-mes-v2",
                payload["data_through"],
                json.dumps(omen, ensure_ascii=False, sort_keys=True) if omen else None,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"目标期 {target_key} 已冻结，禁止覆盖旧预测") from exc
    finally:
        conn.close()
    return {"status": "frozen", "database": str(Path(db_path)), **payload}


def special_settle_forecast(db_path: str, target: datetime, actual_extra: int) -> dict:
    """Append an actual Extra Number to a frozen forecast; never overwrite settlement."""
    if actual_extra not in ALL_NUMBERS:
        raise ValueError("--actual-extra 必须在 1-49")
    target_key = target.isoformat(sep=" ", timespec="minutes")
    conn = _experiment_db(db_path)
    try:
        row = conn.execute("SELECT prediction_json FROM forecasts WHERE target=?", (target_key,)).fetchone()
        if not row:
            raise ValueError(f"找不到已冻结预测: {target_key}")
        actual_zodiac = zodiac_of_number(actual_extra, target)
        try:
            conn.execute(
                "INSERT INTO settlements(target,settled_at,actual_extra,actual_zodiac) VALUES(?,?,?,?)",
                (target_key, datetime.now().astimezone().isoformat(timespec="seconds"), actual_extra, actual_zodiac),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"目标期 {target_key} 已验分，禁止覆盖旧结果") from exc
    finally:
        conn.close()
    return {
        "status": "settled",
        "database": str(Path(db_path)),
        "target": target_key,
        "actual_extra": actual_extra,
        "actual_zodiac": actual_zodiac,
    }


def special_experiment_ledger(db_path: str) -> dict:
    """Summarize settled immutable forecasts and compare them with exact random coverage."""
    conn = _experiment_db(db_path)
    try:
        rows = conn.execute(
            "SELECT f.target,f.prediction_json,s.actual_extra,s.actual_zodiac "
            "FROM forecasts f JOIN settlements s USING(target) ORDER BY f.target"
        ).fetchall()
        pending = conn.execute(
            "SELECT COUNT(*) FROM forecasts f LEFT JOIN settlements s USING(target) WHERE s.target IS NULL"
        ).fetchone()[0]
    finally:
        conn.close()
    if not rows:
        return {"status": "no_settled_forecasts", "settled": 0, "pending": pending}

    model_names = ("math", "metaphysics", "hybrid_base", "hybrid")
    raw = {
        name: {
            "n1": [], "n5": [], "n10": [], "z1": [], "z3": [], "z1_base": [], "z3_base": []
        }
        for name in model_names
    }
    for target_text, prediction_json, actual_extra, actual_zodiac in rows:
        prediction = json.loads(prediction_json)
        target = parse_dt(target_text)
        table = zodiac_table(target)
        for name in model_names:
            ranks = prediction["rankings"][name]
            numbers = ranks["number_top10"]
            zodiacs = ranks["zodiac_top3"]
            raw[name]["n1"].append(actual_extra == numbers[0])
            raw[name]["n5"].append(actual_extra in numbers[:5])
            raw[name]["n10"].append(actual_extra in numbers[:10])
            raw[name]["z1"].append(actual_zodiac == zodiacs[0])
            raw[name]["z3"].append(actual_zodiac in zodiacs[:3])
            raw[name]["z1_base"].append(len(table[zodiacs[0]]) / 49)
            raw[name]["z3_base"].append(sum(len(table[z]) for z in zodiacs[:3]) / 49)

    models = {}
    for name, values in raw.items():
        steps = len(values["n1"])
        models[name] = {
            "number_top1_rate": _rate(values["n1"]),
            "number_top5_rate": _rate(values["n5"]),
            "number_top10_rate": _rate(values["n10"]),
            "zodiac_top1_rate": _rate(values["z1"]),
            "zodiac_top3_rate": _rate(values["z3"]),
            "zodiac_top1_random": round(sum(values["z1_base"]) / steps, 6),
            "zodiac_top3_random": round(sum(values["z3_base"]) / steps, 6),
            "monte_carlo": {
                "number_top5": _mc_tail_probability(sum(values["n5"]), [5 / 49] * steps, f"ledger:{name}:n5"),
                "zodiac_top1": _mc_tail_probability(sum(values["z1"]), values["z1_base"], f"ledger:{name}:z1"),
            },
        }
    return {
        "status": "ok",
        "database": str(Path(db_path)),
        "settled": len(rows),
        "pending": pending,
        "models": models,
        "note": "仅统计开奖前已冻结且之后录入真实特别号的前向样本；不允许事后覆盖预测或结果。",
    }


def analyze(draws: Sequence[Draw], target: datetime, tickets: int, seed: int) -> dict:
    cutoff_draws = [d for d in draws if d.date < target]
    if not cutoff_draws:
        raise ValueError("目标时间之前没有历史开奖数据")
    ms = math_scores(cutoff_draws)
    meta, components, meta_context, warnings = metaphysics_scores(target)
    hy = combine_scores(ms, meta)
    top = sorted(ALL_NUMBERS, key=lambda n: (-hy[n], n))[:15]
    rows = []
    for n in top:
        rows.append({
            "number": n,
            "element": hetu_element(n),
            "palace": palace_of(n),
            "math": round(ms[n], 2),
            "干支": round(components.get("干支", {}).get(n, 0.0), 2) if "干支" in components else None,
            "河洛": round(components["河洛"][n], 2),
            "梅花": round(components.get("梅花", {}).get(n, 0.0), 2) if "梅花" in components else None,
            "奇门": round(components.get("奇门", {}).get(n, 0.0), 2) if "奇门" in components else None,
            "metaphysics": round(meta[n], 2),
            "hybrid": round(hy[n], 2),
        })
    backtest = backtest_draws(cutoff_draws, min_train=100, max_steps=150)
    no_edge_note = "任何固定6码在公平开奖下头奖概率相同；以下分数是实验排序，不是中奖概率。"
    if backtest.get("status") != "insufficient_history":
        if backtest["hybrid"]["mean_lift_vs_random"] <= 0:
            no_edge_note += " 当前走步回测未显示融合模型高于随机基线。"
        else:
            no_edge_note += " 即使回测暂高于随机基线，也需更多独立样本确认，不能视为已证明优势。"
    return {
        "engine": "marksix-hybrid-forecast-v1",
        "target": target.isoformat(sep=" ", timespec="minutes"),
        "data": {"draws_used": len(cutoff_draws), "from": cutoff_draws[0].date.date().isoformat(), "through": cutoff_draws[-1].date.date().isoformat()},
        "probability": probability_baseline(),
        "weights": {"math": 0.55, "metaphysics": 0.45, "metaphysics_components": list(components)},
        "metaphysics_context": meta_context,
        "warnings": warnings,
        "top_numbers": rows,
        "portfolio": build_portfolio(ms, meta, hy, tickets, seed),
        "backtest": backtest,
        "interpretation": no_edge_note,
    }


def write_or_print(obj: dict, output: Optional[str]) -> None:
    payload = json.dumps(obj, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(payload, encoding="utf-8")
    else:
        print(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mark Six official + Chaoshan special/zodiac research engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("analyze")
    pa.add_argument("--csv", required=True)
    pa.add_argument("--target", required=True, help='Hong Kong local time, e.g. "2026-08-08 21:30"')
    pa.add_argument("--tickets", type=int, default=8)
    pa.add_argument("--seed", type=int, default=20260806)
    pa.add_argument("--output")
    pb = sub.add_parser("backtest")
    pb.add_argument("--csv", required=True)
    pb.add_argument("--min-train", type=int, default=100)
    pb.add_argument("--max-steps", type=int)
    pb.add_argument("--output")
    ps = sub.add_parser("special-analyze", help="潮汕买码：分析特别号/特码生肖与候选号码")
    ps.add_argument("--csv", required=True)
    ps.add_argument("--target", required=True, help='Hong Kong local time, e.g. "2026-08-08 21:30"')
    ps.add_argument(
        "--omen-json",
        help='可选外应：JSON字符串或JSON文件，如 {"左物":"植物","左色":"绿","方位":"东","数字":3}',
    )
    ps.add_argument("--output")
    pbt = sub.add_parser("special-backtest", help="潮汕特码模式严格走步回测")
    pbt.add_argument("--csv", required=True)
    pbt.add_argument("--min-train", type=int, default=100)
    pbt.add_argument("--max-steps", type=int)
    pbt.add_argument("--output")
    pfreeze = sub.add_parser("special-freeze", help="开奖前冻结预测到前向实验数据库")
    pfreeze.add_argument("--csv", required=True)
    pfreeze.add_argument("--target", required=True)
    pfreeze.add_argument("--db", required=True, help="SQLite前向实验数据库路径")
    pfreeze.add_argument("--omen-json")
    pfreeze.add_argument("--output")
    psettle = sub.add_parser("special-settle", help="把真实特别号写入已冻结的前向实验记录")
    psettle.add_argument("--db", required=True)
    psettle.add_argument("--target", required=True)
    psettle.add_argument("--actual-extra", type=int, required=True)
    psettle.add_argument("--output")
    pledger = sub.add_parser("special-ledger", help="汇总前向实验数据库命中率与随机基线")
    pledger.add_argument("--db", required=True)
    pledger.add_argument("--output")
    args = parser.parse_args()
    if args.cmd == "analyze":
        draws = load_draws(args.csv)
        if not 1 <= args.tickets <= 100:
            raise SystemExit("--tickets 必须在 1-100")
        obj = analyze(draws, parse_dt(args.target), args.tickets, args.seed)
    elif args.cmd == "backtest":
        draws = load_draws(args.csv)
        obj = backtest_draws(draws, args.min_train, args.max_steps)
    elif args.cmd == "special-analyze":
        draws = load_draws(args.csv)
        obj = special_analyze(draws, parse_dt(args.target), parse_omen_input(args.omen_json))
    elif args.cmd == "special-backtest":
        draws = load_draws(args.csv)
        obj = special_backtest_draws(draws, args.min_train, args.max_steps)
    elif args.cmd == "special-freeze":
        draws = load_draws(args.csv)
        obj = special_freeze_forecast(
            draws, parse_dt(args.target), args.db, parse_omen_input(args.omen_json)
        )
    elif args.cmd == "special-settle":
        obj = special_settle_forecast(args.db, parse_dt(args.target), args.actual_extra)
    else:
        obj = special_experiment_ledger(args.db)
    write_or_print(obj, args.output)


if __name__ == "__main__":
    main()
