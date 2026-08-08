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
