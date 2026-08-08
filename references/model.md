# Mathematical model and validation

## Purpose

Use historical features as auditable hypotheses, not as proof that a fair lottery is predictable. Keep the uniform model as the null hypothesis.

## Number-level math score

For number `i`, over prior draws only:

1. `frequency_z`: shrink the recent inclusion-frequency z-score toward zero. Default window = 120 draws.
2. `ewma_z`: exponentially weighted inclusion rate with half-life 30 draws, centered on `6/49`.
3. `gap_z`: current absence gap relative to the geometric waiting-time mean `(1-p)/p`, with `p=6/49`. Give this low weight because “overdue” reasoning is a classic gambler's-fallacy risk.

Default math raw score:

`0.45*frequency_z + 0.45*ewma_z + 0.10*gap_z`.

Transform the 49 raw values to 0–100 percentile-like scores by min-max normalization. Do not interpret 80 as an 80% draw probability.

## Metaphysics and hybrid score

Metaphysics raw score is the equal-weight mean of available sub-engines: 干支、河洛、梅花、奇门. Normalize to 0–100.

Default hybrid number score:

`0.55*math + 0.45*metaphysics`.

These are fixed research weights. Do not tune them on the final evaluation interval. If a future version learns weights, use nested walk-forward tuning and a sealed outer holdout.

## Candidate portfolio

- Convert hybrid scores to positive sampling weights with a softmax-like transform.
- Sample six unique numbers per line.
- Reject exact duplicate lines.
- Prefer Jaccard/overlap diversity; default maximum shared numbers between two lines = 3 where feasible.
- Label odd/even, low/high, sum, and adjacency as descriptive features only. Do not claim “balanced” lines have higher exact-combination probability.

## Backtest

At prediction index `t`, use draws `[0,t)` only. Never use the target draw in frequency, gap, normalization, weight selection, or metaphysics time conversion except as the target event time.

Compare these deterministic top-6 lines:

- `math_top6`
- `metaphysics_top6`
- `hybrid_top6`

against the exact random baseline.

Report:

- mean main-number matches;
- rate of `>=3` main matches;
- distribution of 0–6 matches;
- lift over expected mean `36/49`;
- at least three chronological subwindows when enough history exists.

Do not call a model predictive merely because one metric is above baseline. Prefer persistence, calibration, and repeated holdouts.

## Randomness audit

Useful diagnostics include marginal number counts, pair co-occurrence, serial dependence, and chi-square-style goodness-of-fit tests. Multiple testing must be acknowledged; isolated small p-values among many searched patterns are not evidence of exploitable bias.

Relevant research:

- Coronel-Brizio et al., *Statistical auditing and randomness test of lotto k/N-type games*, arXiv:0806.4595, https://arxiv.org/abs/0806.4595
- Ralph Stömmer, *Tackling the 6/49 Lottery and Debunking Common Myths with Probabilistic Methods and Combinatorial Designs*, arXiv:2603.24170, https://arxiv.org/abs/2603.24170
- Wang et al., *Number preferences in lotteries*, Judgment and Decision Making (human number-selection biases), https://www.cambridge.org/core/journals/judgment-and-decision-making/article/number-preferences-in-lotteries/47BA27051627CEED421AD3AEE255521E

Human selection bias can matter for prize sharing, not for draw probability. Birthday-heavy or popular patterns may increase the chance of splitting a pari-mutuel top prize if they hit.

## GitHub math research lineage

Two public implementations were inspected before MES-v1 was designed:

- `simplicitydone/korean-lottery-analysis`: uses Beta-Binomial shrinkage, randomness batteries, walk-forward ML, calibration and leakage-free backtests, and explicitly reports that tested models do not beat random in its lottery data. Its validation discipline informed this project's nested/prequential checks. https://github.com/simplicitydone/korean-lottery-analysis
- `dbaengineerbigdata/lotto-max-ml-predictor`: exposes Markov, Bayesian, gap, entropy and ensemble modules in a lottery codebase. Its feature menu was useful for comparison, but this project does **not** copy its gap rule that makes an overdue number automatically more probable. https://github.com/dbaengineerbigdata/lotto-max-ml-predictor

MES-v1 and MES-v2 are this project's own implementations; no source code is copied from either repository.

## Chaoshan Extra Number / zodiac model

For 潮汕买码 research, change the statistical target from six main-number inclusions to the single Extra Number.

Number-level **MES-v2** uses prior Extra Numbers only. It retains MES-v1 intact as a candidate rather than deleting it during the upgrade:

1. **Legacy MES-v1 candidate:** preserve the earlier Bayesian + EWMA + transition ensemble with its own 36-step nested prequential weighting.
2. **Dirichlet-Bayesian candidate:** treat each draw as one categorical outcome in 1–49; default recent window 160 and symmetric prior strength 49, so sparse counts shrink toward 1/49.
3. **Multi-scale EWMA candidate:** blend Extra-only exponentially weighted histories with half-lives 8/21/55 and weights 50%/30%/20%, plus a uniform pseudo-count prior.
4. **Smoothed Markov candidate:** condition on the previous Extra Number's residue state `(extra-1) mod 7`, then estimate the next exact Extra distribution with a strong symmetric prior. Seven states avoid a sparse 49×49 table.
5. **Two-state HMM candidate:** fit a strongly smoothed two-hidden-state HMM to the latest at most 180 seven-residue observations with deterministic Baum-Welch updates. Forecast the next residue distribution, then allocate within each residue using a strongly shrunk exact-number posterior. Hidden states are unlabeled statistical regimes; do not interpret them as real draw-machine states.
6. **MES-v2 model arena:** on up to the last 48 already-known outcomes, compare every candidate with the uniform null using multiclass log loss and Top5 hit rate. If a candidate loses both checks, set its target-period arena weight to zero; if it wins only one, downweight it; if all candidates lose, return the uniform math model. The outer target draw never enters this decision.
7. **Regime diagnostics:** report entropy efficiency and recent-vs-prior Jensen-Shannon divergence as diagnostics. Do not treat low entropy or drift by itself as evidence of a usable edge.

Do not use an “overdue ⇒ more likely next draw” rule. In an independent fair draw, a long gap does not increase the next-draw probability.

Zodiac-level math first converts each historical Extra Number with the lunar-year mapping valid **on that historical draw date**, then uses only shrunk frequency and EWMA residuals. It does not reward an overdue zodiac. Expected zodiac frequency is not fixed at 1/12: calculate it from that draw's 4- or 5-number zodiac bucket divided by 49.

Construct Chaoshan number scores in auditable stages:

1. current-zodiac math = 60% historical zodiac score + 40% mean projected MES number score;
2. math number = 75% MES Extra Number score + 25% current-zodiac math score;
3. metaphysics number = 70% number-level metaphysics + 30% current-zodiac metaphysics score;
4. base hybrid = fixed 55% math number + 45% metaphysics number.
5. if a frozen 外应 input is supplied, final hybrid = 90% base hybrid + 10% omen score. Historical backtests exclude unrecorded omen data.

Keep direct zodiac rankings separately:

- zodiac math from historical Extra-zodiac behavior;
- zodiac metaphysics from the projected four metaphysics families;
- zodiac base hybrid = fixed 55% zodiac math + 45% zodiac metaphysics; apply the same optional 10% omen cap only when a frozen omen exists.

### Chaoshan backtest baselines

For every walk-forward target, score:

- exact Extra Top1: random baseline 1/49;
- Extra Top5: 5/49;
- Extra Top10: 10/49;
- zodiac Top1/Top3: random baseline = total numbers covered by the predicted zodiac bucket(s) / 49.

Because the year animal contains five numbers, never use a blanket 1/12 zodiac baseline when evaluating a specific predicted zodiac.

### Monte Carlo significance audit

For every scored Chaoshan walk-forward backtest, run a deterministic 50,000-trial one-sided null simulation. Simulate independent fair Extra outcomes at the exact candidate coverage probability and report `P(null hits >= observed hits)`. For zodiac metrics, use each historical target's actual 4- or 5-number coverage rather than a fixed 1/12 assumption.

Treat the Monte Carlo tail as an audit, not a model-selection oracle. A small tail in one searched metric is not proof of predictability, especially when many variants have been tried. Prefer repeated future confirmation.

### Prospective experiment database

Use the built-in SQLite ledger when testing future draws:

- `special-freeze` inserts one immutable pre-draw forecast keyed by target time, including math/metaphysics/base-hybrid/final-hybrid rankings and frozen omen input;
- `special-settle` inserts one actual Extra Number after the result is verified and refuses overwrites;
- `special-ledger` scores only settled frozen forecasts against exact random coverage and Monte Carlo null tails.

Store the database outside the skill directory. Historical backtests and prospective records are different evidence surfaces; never merge fabricated historical omen observations into the ledger.
