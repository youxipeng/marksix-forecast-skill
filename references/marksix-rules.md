# Mark Six rules and probability baseline

Verified 2026-08-06 against Hong Kong Jockey Club material. Re-check live before future forecasts because rules and schedules can change.

## Official rules

- Mark Six is a 6-out-of-49 lottery operated by HKJC Lotteries Limited.
- A Single Entry selects six different numbers from 1–49.
- Each draw produces six Drawn Numbers plus one Extra Number from the remaining numbers.
- Unit stake: HK$10. Multiple and Banker entries accept HK$5 partial units under the stated rules.
- Prize tiers: 1st = 6 main; 2nd = 5 main + extra; 3rd = 5 main; 4th = 4 main + extra; 5th = 4 main; 6th = 3 main + extra; 7th = 3 main.
- Fixed full-unit prizes at verification: 4th HK$9,600; 5th HK$640; 6th HK$320; 7th HK$40. First/second/third are pool-dependent; HKJC states a minimum First Division Prize Fund of HK$8 million.
- Draws are normally held three times weekly, typically Tuesday, Thursday, and a non-racing Saturday or Sunday. Use the live fixtures page for the exact target draw.

## Official sources

- HKJC Mark Six: https://bet.hkjc.com/en/marksix
- HKJC results: https://bet.hkjc.com/en/marksix/results
- HKJC fixtures: https://bet.hkjc.com/en/marksix/fixtures
- HKJC prize qualification: https://special.hkjc.com/e-win/en-US/betting-info/marksix/prize-qualification/
- HKJC entry types: https://special.hkjc.com/e-win/en-US/betting-info/marksix/types-of-entry/
- Lotteries Rule 3, version surfaced 2026-03-30: https://special.hkjc.com/e-win/en-US/betting-info/marksix/lotteries-rules/-/media/Sites/JCBW/Special/betting-rules/Lotteries_Rule_3_Eng_20260330

## Exact first-prize probability

There are:

`C(49,6) = 13,983,816`

equally likely six-number main combinations under the fair-draw model. Therefore every fixed valid Single Entry has first-prize probability:

`1 / 13,983,816 ≈ 0.000007151%`.

The expected number of main-number matches for any fixed six-number ticket is:

`6 × (6/49) = 36/49 ≈ 0.734694`.

For exactly `k` main-number matches, ignoring the Extra Number:

`P(K=k) = C(6,k) C(43,6-k) / C(49,6)`.

Use this hypergeometric distribution as the baseline for backtest hit-rate comparisons.

## Important distinction

Historical hot/cold behavior, auspicious numbers, date patterns, and chart features do not alter these exact probabilities unless there is a genuine non-random physical bias in the draw mechanism. Any claimed edge must therefore survive a strict out-of-sample test and a randomness audit.
