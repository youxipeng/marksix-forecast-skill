---
name: marksix-hybrid-forecast
description: "Analyze Hong Kong Mark Six (六合彩) with exact lottery probabilities, historical-data diagnostics, walk-forward backtests, experimental mathematical scoring, and traditional Chinese metaphysics features (天干地支、河图洛书、梅花易数、奇门遁甲), then generate candidate lines and a visual report. Use when the user asks for Mark Six rules, historical analysis, number selection, experimental predictions/预测, hot/cold numbers, backtests,玄学选号,混合算法, or可视化分析."
---

# Mark Six hybrid forecast

Treat this as an auditable lottery-research workflow, not a method that can guarantee or reliably create an edge in a fair random draw.

## Mandatory workflow

1. Verify the target draw and current rules from official HKJC sources before any live forecast. Read `references/marksix-rules.md`. If a rule, ticket price, prize, draw time, or schedule may have changed, browse HKJC again.
2. Acquire historical results. Prefer official HKJC results. Never invent or interpolate missing draws. Normalize to `draw_id,date,n1,n2,n3,n4,n5,n6,extra` and validate six distinct main numbers in 1–49 plus a distinct extra number.
3. Establish the mathematical baseline first. Every six-number line has first-prize probability `1 / C(49,6) = 1 / 13,983,816` under a fair draw. Historical frequency does not change that fact.
4. Run the mathematical model and the four metaphysics feature families separately. Read `references/model.md` and `references/metaphysics.md` before interpreting the scores.
5. Backtest chronologically with no future leakage. Compare math-only, metaphysics-only, hybrid, and uniform-random baselines. If there is no stable out-of-sample lift, say so plainly.
6. Generate a small diversified candidate portfolio only after the audit. Label candidates as experimental selections, not winning predictions.
7. Produce the visual report by default when the user asks for a forecast or a comparison. Use `scripts/render_report.py` on the JSON from `scripts/marksix_engine.py`.

## Data and execution

All scoring runs locally. No private API, account, trial counter, subscription, or server is required.

For CSV analysis:

```bash
python3 scripts/marksix_engine.py analyze \
  --csv /path/to/draws.csv \
  --target "2026-08-08 21:30" \
  --tickets 8 \
  --output /tmp/marksix-report.json

python3 scripts/render_report.py \
  --input /tmp/marksix-report.json \
  --output /tmp/marksix-report.html
```

For chronological validation:

```bash
python3 scripts/marksix_engine.py backtest \
  --csv /path/to/draws.csv \
  --min-train 100 \
  --output /tmp/marksix-backtest.json
```

The metaphysics time features use `lunar_python` when available. If missing, install the MIT-licensed package only when package installation is permitted:

```bash
python3 -m pip install lunar_python==1.4.8
```

If installation is unavailable, continue with the mathematical engine and date-based 河图洛书 features, mark precise lunar/干支/梅花/奇门 time features as unavailable, and do not fabricate them.

## Required model separation

Always keep these three views visible:

- `math`: frequency shrinkage + EWMA + recency diagnostics. Treat all historical signals as hypotheses that must beat the random baseline out of sample.
- `metaphysics`: four independent sub-scores—干支五行、河图洛书、梅花易数、奇门遁甲. These are traditional/cultural heuristics without established predictive validity.
- `hybrid`: fixed blend of math and metaphysics scores. Do not optimize weights on the same period used to report performance.

Do not hide a weak component by averaging it into the hybrid. Report component backtests separately.

## Candidate construction

Generate multiple lines with weighted sampling without replacement from 1–49, then diversify the portfolio. Prefer low overlap between lines. Typical-shape constraints (odd/even balance, sum range, spacing) may be used only for portfolio variety; explicitly state that they do not improve the probability of any exact six-number combination.

When discussing prize-sharing expected value, distinguish it from draw probability. Avoiding popular human-picked patterns can reduce collision risk if a jackpot is hit, but it does not make the numbers more likely to be drawn.

## Backtest discipline

- Sort by draw date and predict each draw using only prior draws.
- Use at least 100 prior draws for a scored prediction unless the user explicitly accepts a smaller exploratory sample.
- Report mean matched main numbers per line, rate of 3+ matches, and comparison with the hypergeometric/random baseline.
- Treat one lucky high-hit draw as noise unless performance persists across multiple non-overlapping windows.
- Never select a model because it looked best on the final holdout and then report that same holdout as unbiased evidence.

## Live answer format

For a forecast, present in this order:

1. Target draw, data cutoff, number of historical draws, and whether official data was verified.
2. Backtest scorecard: random baseline vs math vs metaphysics vs hybrid.
3. Top-number table with separate `math / 干支 / 河洛 / 梅花 / 奇门 / hybrid` scores.
4. Candidate portfolio, with one line explicitly identified as math-led, one metaphysics-led, and the remaining lines hybrid/diversified.
5. Short rationale for each metaphysics engine in the target time chart.
6. Visual report.
7. One-line probability warning: no candidate has higher first-prize probability unless evidence of a real physical draw bias survives rigorous testing.

## Safety and honesty

Do not give loss-chasing, borrowing, martingale, or stake-escalation advice. Do not claim guaranteed hits, “必中”, “稳中”, hidden certainty, or a proven edge from astrology/玄学. If the user is under 18 or asks to facilitate illegal betting, do not assist with wagering. Analysis, probability education, and cultural exploration are allowed.

## References

- `references/marksix-rules.md`: current rules, prize tiers, official sources, exact probability model.
- `references/model.md`: statistical features, hybrid scoring, backtest metrics, portfolio construction.
- `references/metaphysics.md`: four metaphysics engines, GitHub research lineage, translation from traditional charts to 1–49 features, and license notes.
