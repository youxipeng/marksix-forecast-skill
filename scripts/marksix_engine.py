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
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


P_MAIN = 6 / 49
ALL_NUMBERS = tuple(range(1, 50))
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
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
            "农历月": abs(lunar.getMonth()),
            "农历日": lunar.getDay(),
            "年支序": BRANCHES.index(year_gz[1]) + 1,
            "时支序": BRANCHES.index(hour_gz[1]) + 1,
        }, None
    except Exception as exc:
        return None, f"历法换算失败: {exc}"


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
    parser = argparse.ArgumentParser(description="Mark Six math + metaphysics research engine")
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
    args = parser.parse_args()
    draws = load_draws(args.csv)
    if args.cmd == "analyze":
        if not 1 <= args.tickets <= 100:
            raise SystemExit("--tickets 必须在 1-100")
        obj = analyze(draws, parse_dt(args.target), args.tickets, args.seed)
    else:
        obj = backtest_draws(draws, args.min_train, args.max_steps)
    write_or_print(obj, args.output)


if __name__ == "__main__":
    main()
