# 潮汕特码 / 生肖模式

## Scope

Use this mode for the Chaoshan folk usage of “买码 / 特码 / 生肖”. It is not a separate official lottery. The settlement reference is the Hong Kong Mark Six draw; the folk analysis focuses on HKJC's Extra Number (特别号), commonly called 特码 in this context.

Do not mix in horse-racing results. HKJC is the lottery operator/source, not a horse-performance feature.

## Zodiac-number convention

生肖映射 is a folk/外围 convention rather than an official HKJC bet type.

Use the animal of the **lunar year** for the draw date:

1. Number 01 maps to the lunar-year animal.
2. Increase the number by 1 and move one step backward through the standard cycle 鼠→牛→虎→兔→龙→蛇→马→羊→猴→鸡→狗→猪.
3. Repeat every 12 numbers.
4. The lunar-year animal owns 01/13/25/37/49 (five numbers); each other animal owns four.
5. Switch the table at Lunar New Year. Do not switch on January 1 and do not use the BaZi 立春 boundary for this folk lottery table.

For example, after Lunar New Year 2026 the year animal is 马, so:

| 生肖 | 号码 |
|---|---|
| 马 | 01 13 25 37 49 |
| 蛇 | 02 14 26 38 |
| 龙 | 03 15 27 39 |
| 兔 | 04 16 28 40 |
| 虎 | 05 17 29 41 |
| 牛 | 06 18 30 42 |
| 鼠 | 07 19 31 43 |
| 猪 | 08 20 32 44 |
| 狗 | 09 21 33 45 |
| 鸡 | 10 22 34 46 |
| 猴 | 11 23 35 47 |
| 羊 | 12 24 36 48 |

Cross-checks used for this convention:

- HKJC 2026 Lunar New Year material explicitly refers to 马年: https://racingnews.hkjc.com/chinese/2026/02/13/2%E5%84%84%E6%B8%AF%E5%85%83%E9%A6%AC%E5%B9%B4%E6%96%B0%E6%98%A5%E9%87%91%E5%A4%9A%E5%AF%B6%E9%80%B1%E6%97%A5%E6%99%9A%E9%96%8B%E5%94%AE%E8%A6%8F%E6%A8%A1%E5%89%B5%E6%96%B0%E7%B4%80%E9%8C%84/
- A public 2026 folk mapping table shows the same 马=01/13/25/37/49 convention: https://kj.123pmz.com/kj/sx.html
- A long-running Mark Six chart site documents the general “current-year animal gets 1/13/25/37/49” rule: https://www.cpzhan.com/liu-he-cai/zodiac

## Statistical target

Treat each draw as exactly one Extra Number outcome in 1–49.

Number-level null probabilities:

- exact Top1 candidate: 1/49;
- fixed Top5 set: 5/49;
- fixed Top10 set: 10/49.

Zodiac-level null probability depends on the predicted zodiac set because one zodiac has five numbers and the other eleven have four. For each walk-forward step, calculate the random baseline as:

candidate-covered numbers / 49.

This avoids falsely comparing a five-number year-animal prediction with a four-number animal as if both had probability 1/12.

## Math features

Use Extra Numbers only:

- legacy MES-v1 as an intact candidate;
- Dirichlet-Bayesian shrinkage over the one-of-49 Extra outcome;
- multi-scale Extra-only EWMA with 8/21/55-draw half-lives;
- a strongly smoothed first-order transition feature on seven numeric residue states;
- a strongly smoothed two-state HMM on the seven residue observations;
- MES-v2 model-arena gating from a 48-step inner prequential slice of prior outcomes only; candidates losing both log-loss and Top5 null checks are eliminated for that target;
- entropy efficiency and Jensen-Shannon drift as diagnostics, not standalone predictive claims;
- a separate zodiac-history layer at zodiac level, converting every historical Extra Number using the zodiac table valid on that draw date, then blending it with projected MES scores.

Never compute 特码 heat from the six main numbers.

Do not make an Extra Number more likely merely because it is “overdue”. A fair independent draw has no memory. See references/model.md for MES-v2 details.

## Metaphysics projection

Start from the same four auditable feature families as the main engine: 干支、河洛、梅花、奇门. Project number-level component scores to the current zodiac buckets by mean score, not sum, so the five-number year animal is not automatically favored.

For 干支, add a separate生肖 branch layer:

-生肖五行: 鼠猪水、虎兔木、蛇马火、猴鸡金、牛龙羊狗土;
- compare candidate生肖 with day/hour branch using same、六合、三合、冲 as transparent heuristic features;
- combine this direct layer with the projected number-level 干支 score.

These are cultural modeling conventions without established predictive validity.

## Optional 外应

For a user who explicitly wants a现场/外应 layer, use the 外应Pro one-shot protocol in references/external-omen.md. Freeze the observation before showing omen-adjusted candidates, keep its score separate, and cap its final influence at 10%. Never fabricate historical omen inputs for backtests.

## Walk-forward report

At target draw t, use only draws before t. Report math, metaphysics, and hybrid separately.

Primary metrics:

- 生肖 Top1 hit rate and its exact coverage baseline;
- 生肖 Top3 hit rate and its exact coverage baseline;
- 特码 Top1 / Top5 / Top10 hit rates;
- percentage-point lift versus random baseline.
- individual MES-v2 arena-candidate results and current active/downweighted/eliminated status;
- one-sided 50,000-trial Monte Carlo null-tail probability for the scored hit metrics.

Prefer at least 100 prior draws before scoring. Do not tune weights using the same final evaluation interval.

For future evidence, prefer `special-freeze` before the draw, `special-settle` after verifying the official Extra Number, and `special-ledger` for cumulative prospective scoring. Frozen rows and settlements must not be overwritten.
