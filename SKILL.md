---
name: marksix-pro-forecast
description: "Use the Mark Six Pro private forecasting service to analyze Hong Kong Mark Six (六合彩), compare mathematical and traditional Chinese metaphysics signals, run no-leakage historical validation, and return experimental candidate lines with a visual research report. Use when a configured user asks for Mark Six prediction/预测,选号,热冷号,天干地支,河图洛书,梅花易数,奇门遁甲,回测, or融合分析."
---

# Mark Six Pro forecast

Use the private service for scoring. Do not reproduce or reimplement the private forecast algorithm inside this public skill.

## Workflow

1. Verify the target draw and current Mark Six rules from official HKJC sources before a live forecast.
2. Collect historical results without inventing missing draws. Normalize each record to `draw_id,date,n1,n2,n3,n4,n5,n6,extra`.
3. If the user has no service key yet, register one trial key once with `scripts/marksix_pro_client.py register`. Then call `forecast` with the configured service URL and API key.
4. Present the returned sections separately: mathematical score, 干支, 河洛, 梅花, 奇门, hybrid score, walk-forward comparison, and candidate portfolio.
5. Keep the fair-draw baseline visible: every fixed 6-number line has first-prize probability `1 / C(49,6) = 1 / 13,983,816`.
6. If the service returns `PRO_REQUIRED`, tell the user that both full free forecasts have been used and show only the service-provided subscription URL. Do not try to bypass the entitlement check.

## Service call

```bash
python3 scripts/marksix_pro_client.py forecast \
  --history /path/to/draws.csv \
  --target "2026-08-08 21:30" \
  --tickets 8 \
  --output /tmp/marksix-pro.json

python3 scripts/render_report.py \
  --input /tmp/marksix-pro.json \
  --output /tmp/marksix-pro.html
```

Configuration may be supplied through `MARKSIX_PRO_API_URL` and `MARKSIX_PRO_API_KEY`, or the matching command-line flags. Never commit a live API key to a public repository.

Read `references/service-contract.md` when diagnosing API status codes or configuring a new deployment.

## Output rules

- Treat scores as rankings, not calibrated draw probabilities.
- Keep math, metaphysics, and hybrid results visibly separate.
- Do not claim guaranteed hits, 必中, 稳中, or a proven edge unless a genuine physical draw bias survives rigorous independent testing.
- Do not give loss-chasing, borrowing, martingale, or stake-escalation advice.
- If history is too short for the configured walk-forward test, say so instead of fabricating a backtest.
