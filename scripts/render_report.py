#!/usr/bin/env python3
"""Render marksix_engine JSON as a self-contained, responsive HTML report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def esc(v) -> str:
    return html.escape(str(v))


def fmt(v, digits=3) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def score_cell(v) -> str:
    if v is None:
        return '<td class="muted">—</td>'
    val = max(0.0, min(100.0, float(v)))
    return f'<td><div class="score"><span style="width:{val:.1f}%"></span><b>{val:.1f}</b></div></td>'


def render_special(data: dict) -> str:
    bt = data.get("backtest", {})
    z_rows = data.get("top_zodiacs", [])
    n_rows = data.get("top_special_numbers", [])
    data_info = data.get("data", {})
    warnings = data.get("warnings", [])
    z_html = []
    for row in z_rows:
        nums = " ".join(f"{int(n):02d}" for n in row.get("numbers", []))
        z_html.append(
            "<tr>"
            f'<td><b class="zodiac">{esc(row.get("zodiac", ""))}</b></td>'
            f'<td>{esc(nums)}</td><td>{esc(row.get("element", ""))}</td>'
            + score_cell(row.get("math"))
            + score_cell(row.get("干支"))
            + score_cell(row.get("河洛"))
            + score_cell(row.get("梅花"))
            + score_cell(row.get("奇门"))
            + score_cell(row.get("base_hybrid"))
            + score_cell(row.get("omen"))
            + score_cell(row.get("hybrid"))
            + "</tr>"
        )
    n_html = []
    for row in n_rows:
        n_html.append(
            "<tr>"
            f'<td><span class="ball">{int(row.get("number", 0)):02d}</span></td>'
            f'<td>{esc(row.get("zodiac", ""))}</td><td>{esc(row.get("element", ""))}</td>'
            + score_cell(row.get("math"))
            + score_cell(row.get("干支"))
            + score_cell(row.get("河洛"))
            + score_cell(row.get("梅花"))
            + score_cell(row.get("奇门"))
            + score_cell(row.get("base_hybrid"))
            + score_cell(row.get("omen"))
            + score_cell(row.get("hybrid"))
            + "</tr>"
        )
    bt_html = []
    if bt.get("status") == "ok":
        for key, label in (("math", "MES-v2数学"), ("metaphysics", "玄学"), ("hybrid", "融合")):
            m = bt.get(key, {})
            z = m.get("zodiac", {})
            n = m.get("number", {})
            mc = m.get("monte_carlo", {}).get("number_top5", {})
            bt_html.append(
                f"<tr><td>{label}</td><td>{fmt(z.get('top1_rate'),3)}</td>"
                f"<td>{fmt(z.get('random_top1_rate'),3)}</td><td>{fmt(z.get('top3_rate'),3)}</td>"
                f"<td>{fmt(n.get('top5_rate'),3)}</td><td>{fmt(n.get('top10_rate'),3)}</td>"
                f"<td>{fmt(mc.get('p_ge_observed'),4)}</td></tr>"
            )
    warning_html = "".join(f"<li>{esc(x)}</li>" for x in warnings)
    context = data.get("metaphysics_context", {})
    mes = context.get("数学MES", {})
    arena = mes.get("arena", {})
    arena_weights = mes.get("arena_weights", {})
    arena_bt = bt.get("arena_components", {})
    arena_rows = []
    labels = {"mes_v1": "旧MES-v1整体", "bayes": "Dirichlet贝叶斯", "ewma": "多尺度EWMA", "transition": "Markov转移", "hmm": "两状态HMM"}
    for key in ("mes_v1", "bayes", "ewma", "transition", "hmm"):
        outer = arena_bt.get(key, {}).get("number", {})
        mc = arena_bt.get(key, {}).get("monte_carlo", {}).get("number_top5", {})
        arena_rows.append(
            f"<tr><td>{esc(labels[key])}</td><td>{esc(arena.get('component_status',{}).get(key,'—'))}</td>"
            f"<td>{fmt(arena_weights.get(key),3)}</td><td>{fmt(arena.get('component_log_loss',{}).get(key),3)}</td>"
            f"<td>{fmt(arena.get('component_top5_rate',{}).get(key),3)}</td><td>{fmt(outer.get('top5_rate'),3)}</td>"
            f"<td>{fmt(outer.get('top10_rate'),3)}</td><td>{fmt(mc.get('p_ge_observed'),4)}</td></tr>"
        )
    arena_html = "".join(arena_rows)
    diagnostic_html = "".join(
        f'<article class="diag"><h3>{esc(key)}</h3><pre>{esc(json.dumps(context[key], ensure_ascii=False, indent=2))}</pre></article>'
        for key in ("数学MES", "外应") if key in context
    )
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>六合彩 · 潮汕特码生肖研究</title>
<style>
:root{{--ink:#201b17;--muted:#746b61;--paper:#f5f0e5;--panel:#fffaf0;--line:#d8ccb9;--red:#9f2e24;--gold:#b88936}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC","SimSun",serif}}
main{{max-width:1180px;margin:auto;padding:32px 20px 56px}}header{{border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:22px}}
.eyebrow{{color:var(--red);font-weight:700;letter-spacing:.16em}}h1{{font-size:clamp(30px,5vw,54px);margin:9px 0}}h2{{font-size:22px}}
.sub,.muted{{color:var(--muted)}}.panel{{background:var(--panel);border:1px solid var(--line);padding:18px;margin:14px 0 24px;overflow:auto}}
table{{width:100%;border-collapse:collapse;min-width:780px}}th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line);white-space:nowrap}}th{{font-size:12px;color:var(--muted)}}
.score{{position:relative;height:25px;min-width:76px;background:#eadfce}}.score span{{display:block;height:100%;background:linear-gradient(90deg,var(--gold),var(--red));opacity:.72}}.score b{{position:absolute;right:5px;top:4px;font:600 12px system-ui}}
.ball{{display:inline-grid;place-items:center;width:36px;height:36px;border-radius:50%;background:var(--red);color:white;font:700 13px system-ui}}.zodiac{{font-size:20px;color:var(--red)}}
.notice{{border-left:4px solid var(--red);padding:11px 14px;background:#eee2d2}}.diag{{border-top:1px solid var(--line);padding:10px 0}}pre{{white-space:pre-wrap;font:12px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}}footer{{margin-top:24px;color:var(--muted);font-size:13px}}
</style></head><body><main>
<header><div class="eyebrow">潮汕买码 · 特码 / 生肖研究</div><h1>特别号 × 十二生肖 × 玄数融合</h1>
<p class="sub">目标：{esc(data.get("target",""))} · 农历年生肖：{esc(data.get("target_lunar_zodiac",""))} · 历史 {esc(data_info.get("draws_used",0))} 期 · 截至 {esc(data_info.get("through",""))}</p></header>
<section class="panel"><h2>先看走步回测 · {esc(bt.get('range',{}).get('steps','—'))}期</h2><table><thead><tr><th>模型</th><th>生肖Top1</th><th>随机Top1基线</th><th>生肖Top3</th><th>特码Top5</th><th>特码Top10</th><th>Top5 MC p值</th></tr></thead><tbody>{''.join(bt_html)}</tbody></table><p class="muted">MC p值 = 在公平随机开奖假设下，随机模拟至少达到当前命中数的比例；越小才越值得继续研究，不能把一次低值直接当作可预测证据。</p></section>
<section class="panel"><h2>MES-v2 模型竞技场</h2><table><thead><tr><th>候选数学模型</th><th>当前状态</th><th>当前权重</th><th>内层LogLoss</th><th>内层Top5</th><th>外层Top5</th><th>外层Top10</th><th>Top5 MC p值</th></tr></thead><tbody>{arena_html}</tbody></table><p class="muted">竞技场只用目标期之前的内层走步数据调权；同时落后均匀随机的候选可被归零。</p></section>
<section class="panel"><h2>候选生肖</h2><table><thead><tr><th>生肖</th><th>本年号码</th><th>五行</th><th>MES数学</th><th>干支</th><th>河洛</th><th>梅花</th><th>奇门</th><th>外应前融合</th><th>外应</th><th>最终融合</th></tr></thead><tbody>{''.join(z_html)}</tbody></table></section>
<section class="panel"><h2>候选特码号码</h2><table><thead><tr><th>号码</th><th>生肖</th><th>河图五行</th><th>MES数学</th><th>干支</th><th>河洛</th><th>梅花</th><th>奇门</th><th>外应前融合</th><th>外应</th><th>最终融合</th></tr></thead><tbody>{''.join(n_html)}</tbody></table></section>
{f'<section class="panel"><h2>数学 / 外应 Pro 诊断</h2>{diagnostic_html}</section>' if diagnostic_html else ''}
{f'<section class="panel"><h2>提示</h2><ul>{warning_html}</ul></section>' if warning_html else ''}
<p class="notice">{esc(data.get("interpretation",""))}</p>
<footer>民俗与算法研究用途。生肖、热冷与玄学评分不改变公平开奖的随机概率；不提供追损、借贷或加码建议。</footer>
</main></body></html>'''


def render(data: dict) -> str:
    if data.get("mode") == "chaoshan-special":
        return render_special(data)
    prob = data.get("probability", {})
    bt = data.get("backtest", {})
    weights = data.get("weights", {})
    context = data.get("metaphysics_context", {})
    rows = data.get("top_numbers", [])
    portfolio = data.get("portfolio", [])
    warnings = data.get("warnings", [])
    top_rows = []
    for r in rows:
        top_rows.append(
            "<tr>"
            f'<td><span class="ball">{int(r["number"]):02d}</span></td>'
            f'<td>{esc(r.get("element", ""))} · {esc(r.get("palace", ""))}宫</td>'
            + score_cell(r.get("math"))
            + score_cell(r.get("干支"))
            + score_cell(r.get("河洛"))
            + score_cell(r.get("梅花"))
            + score_cell(r.get("奇门"))
            + score_cell(r.get("hybrid"))
            + "</tr>"
        )
    ticket_cards = []
    for i, t in enumerate(portfolio, 1):
        balls = "".join(f'<span class="ball big">{int(n):02d}</span>' for n in t.get("numbers", []))
        ticket_cards.append(
            f'<article class="ticket"><div class="ticket-head"><b>{i:02d} · {esc(t.get("label", ""))}</b>'
            f'<span>融合均分 {fmt(t.get("avg_hybrid"), 1)}</span></div><div class="balls">{balls}</div>'
            f'<p>和值 {esc(t.get("sum"))} · 奇数 {esc(t.get("odd"))} · 1–24 {esc(t.get("low_1_24"))} · 连号对 {esc(t.get("adjacent_pairs"))}</p></article>'
        )
    bt_rows = []
    if bt.get("status") == "insufficient_history":
        bt_rows.append(f'<tr><td colspan="4">历史不足：需要至少 {esc(bt.get("needed_prior_draws", 100))} 期，当前 {esc(bt.get("available", 0))} 期。</td></tr>')
    else:
        rb = bt.get("random_baseline", {})
        bt_rows.append(f'<tr><td>均匀随机基线</td><td>{fmt(rb.get("expected_mean_hits"), 3)}</td><td>{fmt(rb.get("rate_ge3"), 3)}</td><td>0</td></tr>')
        for key, label in (("math", "数学"), ("metaphysics", "玄学"), ("hybrid", "融合")):
            m = bt.get(key, {})
            lift = m.get("mean_lift_vs_random")
            cls = "pos" if isinstance(lift, (int, float)) and lift > 0 else "neg"
            bt_rows.append(f'<tr><td>{label}</td><td>{fmt(m.get("mean_hits"), 3)}</td><td>{fmt(m.get("rate_ge3"), 3)}</td><td class="{cls}">{fmt(lift, 3)}</td></tr>')
    ctx_items = []
    for key in ("干支", "河洛", "梅花", "奇门"):
        if key in context:
            ctx_items.append(f'<article class="ctx"><h3>{key}</h3><pre>{esc(json.dumps(context[key], ensure_ascii=False, indent=2))}</pre></article>')
    warning_html = "".join(f'<li>{esc(x)}</li>' for x in warnings)
    data_info = data.get("data", {})
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>六合彩 · 数学 × 玄数融合研究</title>
<style>
:root{{--ink:#201b17;--muted:#746b61;--paper:#f5f0e5;--panel:#fffaf0;--line:#d8ccb9;--red:#9f2e24;--gold:#b88936;--green:#2f7459;--blue:#3c6080}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC","SimSun",serif}}
main{{max-width:1180px;margin:auto;padding:34px 22px 60px}} header{{border-bottom:1px solid var(--line);padding-bottom:22px;margin-bottom:24px}}
.eyebrow{{color:var(--red);font-weight:700;letter-spacing:.18em}} h1{{font-size:clamp(30px,5vw,58px);margin:10px 0 8px;line-height:1.05}} h2{{font-size:22px;margin:0 0 16px}} h3{{margin:0 0 8px}}
.sub{{color:var(--muted);max-width:900px}} .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 28px}}
.stat,.panel,.ticket,.ctx{{background:var(--panel);border:1px solid var(--line)}} .stat{{padding:16px}} .stat small{{display:block;color:var(--muted);margin-bottom:7px}} .stat b{{font-size:24px}}
.panel{{padding:20px;margin:14px 0 24px;overflow:hidden}} .table-wrap{{overflow-x:auto}} table{{width:100%;border-collapse:collapse;min-width:780px}} th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line);white-space:nowrap}} th{{font-size:12px;color:var(--muted);font-weight:600}}
.score{{position:relative;height:25px;min-width:82px;background:#eadfce}} .score span{{display:block;height:100%;background:linear-gradient(90deg,var(--gold),var(--red));opacity:.72}} .score b{{position:absolute;right:6px;top:4px;font:600 12px/1.4 system-ui;color:var(--ink)}}
.ball{{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--red);color:white;font:700 13px/1 system-ui;box-shadow:inset 0 0 0 2px rgba(255,255,255,.22)}} .ball.big{{width:44px;height:44px;font-size:15px;margin:2px 4px}}
.tickets{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}} .ticket{{padding:14px}} .ticket-head{{display:flex;justify-content:space-between;gap:12px;color:var(--red)}} .ticket-head span{{color:var(--muted);font-size:12px}} .balls{{margin:12px 0}} .ticket p{{margin:6px 0 0;color:var(--muted);font-size:13px}}
.contexts{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}} .ctx{{padding:15px}} pre{{margin:0;white-space:pre-wrap;font:12px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}}
.pos{{color:var(--green);font-weight:700}} .neg{{color:var(--red);font-weight:700}} .muted{{color:var(--muted)}} .notice{{border-left:4px solid var(--red);padding:10px 14px;background:#eee2d2;color:#4f4036}}
footer{{margin-top:26px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}}
@media(max-width:760px){{.grid{{grid-template-columns:repeat(2,1fr)}}.tickets,.contexts{{grid-template-columns:1fr}}main{{padding:24px 14px 44px}}}}
</style>
</head>
<body><main>
<header><div class="eyebrow">MARK SIX · RESEARCH FORECAST</div><h1>六合彩 · 数学 × 玄数融合</h1>
<p class="sub">目标：{esc(data.get("target", ""))}（香港本地时刻） · 历史样本 {esc(data_info.get("draws_used", 0))} 期 · 数据截至 {esc(data_info.get("through", ""))}</p></header>
<section class="grid">
<div class="stat"><small>头奖单注精确概率</small><b>{esc(prob.get("first_prize_odds", ""))}</b></div>
<div class="stat"><small>随机每注期望命中主号</small><b>{fmt(prob.get("expected_main_matches"), 3)}</b></div>
<div class="stat"><small>融合权重</small><b>{int(100*weights.get("math",.55))}:{int(100*weights.get("metaphysics",.45))}</b></div>
<div class="stat"><small>玄学引擎</small><b>{esc(len(weights.get("metaphysics_components", [])))}/4</b></div>
</section>
<section class="panel"><h2>走步回测 · 必须先看这个</h2><div class="table-wrap"><table><thead><tr><th>模型</th><th>平均命中主号</th><th>≥3 主号比例</th><th>均值相对随机</th></tr></thead><tbody>{''.join(bt_rows)}</tbody></table></div></section>
<section class="panel"><h2>融合排名 · 分数不是概率</h2><div class="table-wrap"><table><thead><tr><th>号码</th><th>河图五行 · 九宫</th><th>数学</th><th>干支</th><th>河洛</th><th>梅花</th><th>奇门</th><th>融合</th></tr></thead><tbody>{''.join(top_rows)}</tbody></table></div></section>
<section><h2>候选组合 · 实验性选号</h2><div class="tickets">{''.join(ticket_cards)}</div></section>
<section class="panel"><h2>目标时刻玄学上下文</h2><div class="contexts">{''.join(ctx_items) or '<p class="muted">未取得精确历法上下文。</p>'}</div>{f'<ul>{warning_html}</ul>' if warning_html else ''}</section>
<p class="notice">{esc(data.get("interpretation", "任何固定6码在公平开奖下头奖概率相同。"))}</p>
<footer>本报告用于概率教育、算法回测与传统文化研究。历史热冷、干支、河洛、梅花、奇门均不能被当作确定性中奖依据；不要追损、借贷或加码投注。</footer>
</main></body></html>'''


def main() -> None:
    ap = argparse.ArgumentParser(description="Render Mark Six research JSON to HTML")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    Path(args.output).write_text(render(data), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
