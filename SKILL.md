---
name: marksix-hybrid-forecast
description: "Analyze Hong Kong Mark Six (六合彩) in two auditable modes: Chaoshan/潮汕民间买码 research centered on the Extra Number (特码/特别号), dynamic lunar-year zodiac mapping, MES-v2 model arena (legacy MES, Bayesian, EWMA, Markov, HMM), Monte Carlo significance checks, 天干地支/五行 + 河图洛书 + 梅花易数 + 奇门遁甲 fusion, optional pre-forecast 外应Pro inputs, immutable prospective experiment logging, and chronological backtests; or official 6-of-49 main-number research. Use for 潮汕六合彩、买码、特码、特别号、生肖、号码预测、玄学选号、外应、左手边/右手边物品、天气/声音/现场观察、冷热号、历史回测、前向验证、Mark Six rules, or visual forecast reports."
---

# Mark Six hybrid forecast

Treat all forecasts as lottery-research experiments. Never imply that historical or metaphysics features can guarantee an edge in a fair random draw.

## Route the request

- If the user says 潮汕、买码、特码、特别号、生肖, use **Chaoshan special mode** by default. Read references/chaoshan-special.md.
- If the user explicitly asks for official ticket/main-number analysis, use **official main-number mode**.
- If ambiguous after a conversation about 潮汕买码, preserve Chaoshan special mode.

## Mandatory workflow

1. Verify the target draw and current official HKJC rules/schedule before a live forecast. Read references/marksix-rules.md.
2. Acquire real historical results. Prefer HKJC; if a secondary archive is required, cross-check recent draws against HKJC and disclose the source. Normalize to draw_id,date,n1,n2,n3,n4,n5,n6,extra.
3. Never invent missing draws. Validate six distinct main numbers plus one distinct Extra Number in 1–49.
4. Read references/model.md and references/metaphysics.md before interpreting scores.
   If the user wants 外应/现场输入, also read references/external-omen.md and freeze the observation before showing omen-adjusted rankings.
5. Keep math, metaphysics, and hybrid results separate. Do not hide a weak component by averaging it into the hybrid.
6. Backtest chronologically: at draw t, use only draws before t. Use at least 100 prior draws for a scored evaluation unless the user explicitly accepts an exploratory smaller sample. Keep MES-v2 arena candidates individually visible.
7. Compare every hit rate with the exact random baseline and the Monte Carlo one-sided null tail in the backtest. If lift is absent, unstable, or has a large null-tail probability, say so plainly.
8. Produce the appropriate visual report with scripts/render_report.py when the user asks for a forecast or comparison.
9. For genuine future validation, freeze each pre-draw forecast with `special-freeze`, settle it only after verifying the official result, then inspect `special-ledger`. Never overwrite a frozen forecast or settlement.

## Chaoshan special mode

Treat HKJC's Extra Number as the object colloquially called 特码 in Chaoshan/外围 usage. Do not use horse-racing results.

The zodiac-number table is a folk convention, not an HKJC lottery rule. Compute it dynamically:

- switch the year animal at Lunar New Year, not January 1;
- number 1 maps to that lunar-year animal;
- as numbers increase, walk backward through 鼠牛虎兔龙蛇马羊猴鸡狗猪;
- the year animal therefore owns five numbers (1, 13, 25, 37, 49); each other animal owns four.

Require lunar_python for correct Lunar-New-Year boundaries. If unavailable, install version 1.4.8 when permitted. Otherwise stop zodiac scoring rather than silently using a wrong Gregorian-year table.

Run:

~~~bash
python3 scripts/marksix_engine.py special-analyze \
  --csv /path/to/draws.csv \
  --target "2026-08-08 21:30" \
  --output /tmp/marksix-special.json

# Optional one-shot 外应 input (inline JSON or JSON file path)
python3 scripts/marksix_engine.py special-analyze \
  --csv /path/to/draws.csv \
  --target "2026-08-08 21:30" \
  --omen-json '{"左物":"植物","左色":"绿","方位":"东","数字":3}' \
  --output /tmp/marksix-special-omen.json

python3 scripts/marksix_engine.py special-backtest \
  --csv /path/to/draws.csv \
  --min-train 100 \
  --output /tmp/marksix-special-backtest.json

# Optional: immutable prospective experiment database
python3 scripts/marksix_engine.py special-freeze \
  --csv /path/to/draws.csv --target "2026-08-08 21:30" \
  --omen-json '{"左物":"裤头绳","左色":"黄色"}' \
  --db /path/to/marksix-forward.sqlite

python3 scripts/marksix_engine.py special-settle \
  --db /path/to/marksix-forward.sqlite --target "2026-08-08 21:30" \
  --actual-extra 3  # example only: replace with the verified official Extra Number

python3 scripts/marksix_engine.py special-ledger \
  --db /path/to/marksix-forward.sqlite

python3 scripts/render_report.py \
  --input /tmp/marksix-special.json \
  --output /tmp/marksix-special.html
~~~

For Chaoshan mode, report:

1. target draw, data cutoff, sample size, and current lunar-year zodiac table;
2. strict walk-forward scorecard for 生肖 Top1/Top3 and 特码号码 Top1/Top5/Top10;
3. exact random baselines: a fixed k-number set hits the Extra Number with probability k/49; zodiac baselines use the actual 4- or 5-number zodiac coverage;
4. separate MES-v2 arena candidates / math / 干支 / 河洛 / 梅花 / 奇门 / hybrid scores, plus Monte Carlo null-tail results;
   if 外应 is supplied, also show the pre-omen hybrid and the omen-adjusted hybrid; never pretend historical backtests contain unrecorded omen data;
5. top candidate zodiacs first, then candidate Extra Numbers within the current zodiac mapping;
6. an explicit statement when the model fails to beat random out of sample.

## Official main-number mode

Run:

~~~bash
python3 scripts/marksix_engine.py analyze \
  --csv /path/to/draws.csv \
  --target "2026-08-08 21:30" \
  --tickets 8 \
  --output /tmp/marksix-report.json

python3 scripts/marksix_engine.py backtest \
  --csv /path/to/draws.csv \
  --min-train 100 \
  --output /tmp/marksix-backtest.json
~~~

Every exact six-number main line has first-prize probability 1 / C(49,6) = 1 / 13,983,816 under a fair draw.

## Model separation

- math: in official mode, main-number frequency/EWMA/recency; in Chaoshan mode use MES-v2. Put legacy MES-v1, Dirichlet-Bayesian shrinkage, multi-scale EWMA, strongly smoothed residue-state transition, and a two-state/seven-residue HMM into a nested prequential model arena. Eliminate or downweight candidates that fail the uniform null checks using past data only, then blend the surviving math signal with dynamic Extra-zodiac history.
- metaphysics: 干支五行、河洛、梅花、奇门 kept auditable as separate cultural heuristics. Chaoshan mode additionally projects them onto the current zodiac table and uses生肖五行/日时支 relations.
- hybrid: fixed 55% math + 45% metaphysics blend. Never tune these weights on the same final holdout used to claim performance.
- optional 外应Pro: keep it separate and cap it at 10% of the final ranking (`90% base hybrid + 10% omen`). Accept only deterministic encodings documented in references/external-omen.md; leave unknown observations unscored. It is prospective, not retrospectively backtestable unless observations were genuinely recorded before each draw.

## Safety and honesty

Do not provide loss-chasing, borrowing, martingale, stake escalation, underground-bookmaker instructions, or claims such as 必中/稳中. Mainland underground Mark Six is illegal private gambling; keep Chaoshan mode to historical analysis, probability education, cultural research, and experimental forecasting rather than facilitating illegal wagering.

## References

- references/marksix-rules.md: official game mechanics and exact probability baseline.
- references/chaoshan-special.md: 特码/生肖 mapping convention and Chaoshan-mode evaluation.
- references/model.md: MES-v2 arena/HMM, Monte Carlo validation, prospective ledger, and walk-forward discipline.
- references/metaphysics.md: four metaphysics engines and zodiac projection.
- references/external-omen.md: 外应Pro one-shot protocol and deterministic encoding.
