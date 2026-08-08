# 外应 Pro / 现场观察输入

## Purpose

Treat 外应 as an optional, prospective cultural heuristic. It is never evidence that a fair draw is causally predictable and never replaces the no-omen mathematical/玄学 baseline.

## Freeze protocol

When the user wants 外应, collect one observation **before showing the omen-adjusted ranking**. Do not let the user keep changing observations after seeing candidates.

Prefer naturally available fields rather than staged objects:

- `左物` / `left_object`: the first salient object already on the user's left;
- `左色` / `left_color`: its main color;
- `右物` / `right_object`, `右色` / `right_color`: same rule on the right;
- `方位` / `direction`: current facing direction if known;
- `数字` / `number`: a number naturally noticed before the forecast, not chosen from candidate numbers;
- `数量` / `count`: a naturally observed count such as repeated sounds; omit if none.
- `第一眼物品` / `first_sight`: the first salient object noticed without staging it;
- `第一声声音` / `first_sound`: the first naturally heard sound;
- `人动物` / `person_animal`: a naturally appearing zodiac animal cue; unknown people are not assigned arbitrary生肖;
- `运动方向` / `movement`: direction of a salient moving object when naturally observed;
- `天气` / `weather`: the actual local weather description at observation time;
- `所在方位` / `location_direction`: location/facing cue when known;
- `手机数字` / `phone_number`: the first naturally visible number on the phone, not a chosen candidate;
- `随机文字` / `random_text`: naturally appearing text; score it only if it contains an explicit five-element/color/material/zodiac cue;
- `观察时间` / `observation_time`: `HH:MM` or ISO date-time recorded when the observation is frozen.

Do not require every field. One or two frozen observations are enough. Record the observation time in the conversational report when available.

## Deterministic encoding

Use `scripts/marksix_engine.py --omen-json` rather than improvising a new mapping per forecast.

Color-to-five-element convention:

- 青/绿 → 木
- 红/紫/粉/橙 → 火
- 黄/棕/米 → 土
- 白/金/银/灰 → 金
- 黑/蓝 → 水

Object keywords use broad material/scene classes in the script: plants/wood/paper → 木; light/fire/electronics → 火; stone/ceramic/earth → 土; metal/tools/vehicles → 金; water/liquid/rain/fish → 水. If an object is ambiguous or unknown, leave it unscored instead of inventing a mapping.

Sound keywords use a small explicit table only: wind/birds/leaves → 木; explosions/alarms/electric cues → 火; footsteps/wall/stone dull impacts → 土; bells/metal/keys/coins → 金; rain/flowing water/waves → 水. Unknown sounds remain unscored.

Weather uses an equally explicit project convention: wind → 木; sun/heat → 火; dust/dryness → 土; frost/hail → 金; rain/snow/fog/cloudy/humid → 水. Treat this as a deterministic experiment encoding, not a classical doctrine.

Position adds only a small conventional prior: left/青龙 → 木 and right/白虎 → 金. Direction uses 东/东南木、南火、西南/东北/中土、西/西北金、北水.

A naturally observed number can contribute exact-number, 洛书九宫 and mod-12 resonances. A count contributes only a small digital-root/九宫 feature. These translations are explicit project conventions, not classical claims.

A recognized zodiac animal can add a direct current-year zodiac-bucket resonance. Observation time contributes a small digital-root palace plus double-hour branch cue. Arbitrary text is never hashed to a lucky number; if it lacks an explicit known cue, leave it unscored and disclose that choice.

## Fusion and evaluation

- Compute the ordinary base hybrid first: `55% math + 45% metaphysics`.
- Project the omen score to numbers and zodiac buckets independently.
- Cap the omen influence at `10%`: final = `90% base hybrid + 10% omen`.
- Always expose both base and omen-adjusted scores when omen is enabled.
- Historical backtests must run with omen disabled unless authentic pre-draw observations were logged at the time. Never manufacture historical “left-side objects” from the known result.
- To evaluate 外应, start a prospective log: observation → frozen forecast → actual Extra Number/生肖. Compare after enough future draws; do not cherry-pick successful cases.
- Prefer `special-freeze` to persist the frozen prediction, then `special-settle` and `special-ledger`; the SQLite ledger refuses forecast/result overwrites.
