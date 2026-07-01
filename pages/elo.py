import math
import random
from collections import defaultdict

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

import api

K_FACTOR = 40
BASE_ELO = 1500
N_SIMS   = 400


# ── Elo Engine ─────────────────────────────────────────────────────────────────

def _compute_elo(matches: list) -> dict:
    elo = defaultdict(lambda: BASE_ELO)
    finished = sorted(
        [m for m in matches if m.get("status") == "FINISHED"],
        key=lambda m: m.get("utcDate", ""),
    )
    for m in finished:
        h_id = m.get("homeTeam", {}).get("id")
        a_id = m.get("awayTeam", {}).get("id")
        if not h_id or not a_id:
            continue
        ft  = m.get("score", {}).get("fullTime", {})
        hg, ag = ft.get("home"), ft.get("away")
        if hg is None or ag is None:
            continue
        eh  = 1 / (1 + 10 ** ((elo[a_id] - elo[h_id]) / 400))
        sh  = 1.0 if hg > ag else 0.0 if hg < ag else 0.5
        elo[h_id] += K_FACTOR * (sh - eh)
        elo[a_id] += K_FACTOR * ((1 - sh) - (1 - eh))
    return dict(elo)


def _match_probs(elo_h: float, elo_a: float) -> tuple:
    """(p_home_win, p_draw, p_away_win)"""
    p_h    = 1 / (1 + 10 ** ((elo_a - elo_h) / 400))
    p_draw = max(0.12, min(0.30, 0.26 - 0.20 * abs(p_h - 0.5)))
    scale  = 1 - p_draw
    return p_h * scale, p_draw, (1 - p_h) * scale


def _simulate_group(table: list, remaining: list, elo: dict) -> dict:
    """Monte Carlo qualification probabilities. Returns {team_id: float}."""
    qual     = defaultdict(int)
    team_ids = [e["team"]["id"] for e in table]

    for _ in range(N_SIMS):
        pts = {e["team"]["id"]: e["points"]         for e in table}
        gd  = {e["team"]["id"]: e["goalDifference"] for e in table}
        gf  = {e["team"]["id"]: e["goalsFor"]       for e in table}

        for m in remaining:
            h_id = m.get("homeTeam", {}).get("id")
            a_id = m.get("awayTeam", {}).get("id")
            if not h_id or not a_id:
                continue
            pw, pd, _ = _match_probs(elo.get(h_id, BASE_ELO), elo.get(a_id, BASE_ELO))
            r = random.random()
            if r < pw:
                pts[h_id] = pts.get(h_id, 0) + 3
                hg, ag = random.randint(1, 3), 0
            elif r < pw + pd:
                pts[h_id] = pts.get(h_id, 0) + 1
                pts[a_id] = pts.get(a_id, 0) + 1
                hg = ag = random.randint(0, 2)
            else:
                pts[a_id] = pts.get(a_id, 0) + 3
                ag, hg = random.randint(1, 3), 0
            gd[h_id] = gd.get(h_id, 0) + hg - ag
            gd[a_id] = gd.get(a_id, 0) + ag - hg
            gf[h_id] = gf.get(h_id, 0) + hg
            gf[a_id] = gf.get(a_id, 0) + ag

        ranked = sorted(team_ids,
                        key=lambda t: (pts.get(t, 0), gd.get(t, 0), gf.get(t, 0)),
                        reverse=True)
        for tid in ranked[:2]:
            qual[tid] += 1

    return {tid: qual[tid] / N_SIMS for tid in team_ids}


def _champ_prob(elo: dict, team_ids: list) -> dict:
    """Softmax over Elo ratings → rough championship probability."""
    weights = {tid: math.exp(elo.get(tid, BASE_ELO) / 400) for tid in team_ids}
    total   = sum(weights.values())
    return {tid: w / total for tid, w in weights.items()}


# ── Chart Helpers ──────────────────────────────────────────────────────────────

def _power_rankings_chart(ranked_teams: list, elo: dict) -> dcc.Graph:
    top20  = ranked_teams[:20]
    names  = [t.get("shortName") or t.get("name", "?") for t in top20]
    ratings = [round(elo.get(t["id"], BASE_ELO)) for t in top20]
    max_r  = max(ratings) if ratings else BASE_ELO
    colors = [f"rgba(240,192,48,{0.35 + 0.65 * (r - BASE_ELO + 200) / 400})" for r in ratings]

    fig = go.Figure(go.Bar(
        x=ratings, y=names,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[str(r) for r in ratings],
        textposition="outside",
        textfont=dict(color="#f0c030", size=12, family="Rajdhani"),
        hovertemplate="<b>%{y}</b><br>Elo: %{x}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#64748b"),
        margin=dict(l=0, r=60, t=8, b=8),
        height=max(300, len(top20) * 30),
        xaxis=dict(showgrid=True, gridcolor="rgba(100,116,139,0.12)",
                   zeroline=False, range=[BASE_ELO - 50, max_r + 60]),
        yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(color="#475569", size=11)),
        showlegend=False,
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False}, className="goals-chart")


def _winner_prob_chart(champ: dict, team_lookup: dict, top_n: int = 12) -> dcc.Graph:
    sorted_teams = sorted(champ.items(), key=lambda x: x[1], reverse=True)[:top_n]
    names  = [team_lookup.get(tid, {}).get("shortName") or team_lookup.get(tid, {}).get("name", str(tid)) for tid, _ in sorted_teams]
    probs  = [round(p * 100, 1) for _, p in sorted_teams]
    colors = ["rgba(240,192,48,0.85)" if i == 0 else "rgba(240,192,48,0.55)" if i < 3 else "rgba(100,116,139,0.45)"
              for i in range(len(probs))]

    fig = go.Figure(go.Bar(
        x=probs, y=names,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{p}%" for p in probs],
        textposition="outside",
        textfont=dict(color="#64748b", size=11, family="Inter"),
        hovertemplate="<b>%{y}</b><br>Championship: %{x}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#64748b"),
        margin=dict(l=0, r=60, t=8, b=8),
        height=max(280, len(sorted_teams) * 32),
        xaxis=dict(showgrid=True, gridcolor="rgba(100,116,139,0.12)",
                   zeroline=False, ticksuffix="%"),
        yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(color="#475569", size=11)),
        showlegend=False,
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False}, className="goals-chart")


# ── UI Helpers ─────────────────────────────────────────────────────────────────

def _prob_bar(pw: float, pd: float, pl: float) -> html.Div:
    return html.Div(
        [
            html.Div(f"{pw:.0%}", className="prob-label prob-home"),
            html.Div(
                [
                    html.Div(style={"flex": str(pw), "background": "#22c55e", "borderRadius": "3px 0 0 3px", "minWidth": "2px"}),
                    html.Div(style={"flex": str(pd), "background": "#6b7280", "minWidth": "2px"}),
                    html.Div(style={"flex": str(pl), "background": "#3b82f6", "borderRadius": "0 3px 3px 0", "minWidth": "2px"}),
                ],
                className="prob-bar-track",
            ),
            html.Div(f"{pl:.0%}", className="prob-label prob-away"),
        ],
        className="prob-bar-row",
    )


def _upcoming_row(match: dict, elo: dict) -> html.Div:
    home   = match.get("homeTeam", {})
    away   = match.get("awayTeam", {})
    h_id   = home.get("id", 0)
    a_id   = away.get("id", 0)
    h_name = home.get("shortName") or home.get("name", "?")
    a_name = away.get("shortName") or away.get("name", "?")
    h_crest = home.get("crest", "")
    a_crest = away.get("crest", "")

    try:
        from datetime import datetime
        dt = datetime.fromisoformat(match.get("utcDate", "").replace("Z", "+00:00"))
        date_str = dt.strftime("%b %-d  ·  %H:%M UTC")
    except Exception:
        date_str = match.get("utcDate", "")[:10]

    pw, pd, pl = _match_probs(elo.get(h_id, BASE_ELO), elo.get(a_id, BASE_ELO))

    def crest_name(team_name, crest):
        return html.Div(
            [
                html.Img(src=crest, style={"height": "20px", "width": "20px", "objectFit": "contain"}) if crest else html.Span(),
                html.Span(team_name, className="pred-team-name"),
            ],
            className="pred-team",
        )

    return html.Div(
        [
            html.Div(
                [
                    crest_name(h_name, h_crest),
                    html.Span("vs", className="pred-vs"),
                    crest_name(a_name, a_crest),
                ],
                className="pred-teams-row",
            ),
            _prob_bar(pw, pd, pl),
            html.Div(date_str, className="pred-date"),
        ],
        className="pred-match-card",
    )


def _qual_row(entry: dict, prob: float, team_lookup: dict) -> html.Div:
    team  = entry.get("team", {})
    tid   = team.get("id")
    full  = team_lookup.get(tid, {})
    crest = full.get("crest") or team.get("crest", "")
    name  = team.get("shortName") or team.get("name", "?")
    pts   = entry.get("points", 0)
    pos   = entry.get("position", 0)
    pct   = prob * 100

    bar_color = "#22c55e" if pct >= 70 else "#f0c030" if pct >= 40 else "#ef4444" if pct < 20 else "#6b7280"

    return html.Div(
        [
            html.Span(str(pos), className="acc-pos-badge" + (" acc-pos-advance" if pos <= 2 else ""), style={"flexShrink": "0"}),
            html.Img(src=crest, style={"height": "18px", "width": "18px", "objectFit": "contain", "flexShrink": "0"}) if crest else html.Span(),
            html.Span(name, className="pred-team-name", style={"flex": "1"}),
            html.Span(f"{pts}pts", style={"fontSize": "0.72rem", "color": "var(--text-muted)", "marginRight": "8px"}),
            html.Div(
                html.Div(style={"width": f"{pct:.0f}%", "background": bar_color, "height": "100%", "borderRadius": "3px", "transition": "width 0.4s"}),
                style={"flex": "1", "background": "var(--border)", "borderRadius": "3px", "height": "6px", "maxWidth": "80px"},
            ),
            html.Span(f"{pct:.0f}%", style={"fontSize": "0.78rem", "fontWeight": "700", "color": bar_color, "minWidth": "36px", "textAlign": "right"}),
        ],
        style={"display": "flex", "alignItems": "center", "gap": "8px", "padding": "7px 12px",
               "borderBottom": "1px solid var(--border)"},
    )


# ── Layout ─────────────────────────────────────────────────────────────────────

def layout() -> html.Div:
    try:
        matches_data   = api.get_matches()
        standings_data = api.get_standings()
        teams_data     = api.get_teams()
    except Exception as e:
        return dbc.Alert(str(e), color="warning", className="m-4")

    matches    = matches_data.get("matches", [])
    standings  = [s for s in standings_data.get("standings", []) if s.get("type") == "TOTAL"]
    team_list  = teams_data.get("teams", [])
    team_lookup = {t["id"]: t for t in team_list}

    elo = _compute_elo(matches)

    all_team_ids = list({m.get("homeTeam", {}).get("id") for m in matches} |
                        {m.get("awayTeam", {}).get("id")  for m in matches})
    all_team_ids = [tid for tid in all_team_ids if tid]

    champ = _champ_prob(elo, all_team_ids)

    ranked_teams = sorted(
        [team_lookup.get(tid, {"id": tid, "name": str(tid)}) for tid in all_team_ids],
        key=lambda t: elo.get(t.get("id", 0), BASE_ELO),
        reverse=True,
    )

    # ── Power Rankings chart ──────────────────────────────────────────────────
    rankings_chart = _power_rankings_chart(ranked_teams, elo)

    # ── Winner prediction chart ───────────────────────────────────────────────
    winner_chart = _winner_prob_chart(champ, team_lookup)

    # ── Upcoming match predictions ────────────────────────────────────────────
    upcoming = sorted(
        [m for m in matches if m.get("status") in ("SCHEDULED", "TIMED")],
        key=lambda m: m.get("utcDate", ""),
    )[:12]
    pred_cards = [_upcoming_row(m, elo) for m in upcoming]

    # ── Group qualification probabilities ─────────────────────────────────────
    group_qual_sections = []
    for s in sorted(standings, key=lambda x: x.get("group", "")):
        group  = s.get("group", "")
        letter = group.split()[-1] if group else "?"
        table  = s.get("table", [])

        # Remaining group matches (SCHEDULED/TIMED only)
        group_matches_remaining = [
            m for m in matches
            if m.get("group") == f"GROUP_{letter}" and m.get("status") in ("SCHEDULED", "TIMED")
        ]

        qual_probs = _simulate_group(table, group_matches_remaining, elo)

        qual_rows = [_qual_row(entry, qual_probs.get(entry["team"]["id"], 0), team_lookup)
                     for entry in table]

        group_qual_sections.append(
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            [html.Span(letter, className="group-letter"), html.Span(group, className="group-label-text")],
                            className="group-card-header",
                        ),
                        html.Div(qual_rows),
                    ],
                    className="group-card",
                ),
                lg=4, md=6, className="mb-3",
            )
        )

    group_rows = []
    for i in range(0, len(group_qual_sections), 3):
        group_rows.append(dbc.Row(group_qual_sections[i:i+3], className="g-3"))

    # ── Methodology note ──────────────────────────────────────────────────────
    n_finished = sum(1 for m in matches if m.get("status") == "FINISHED")
    method_note = html.Div(
        [
            html.Span("⚙️  ", style={"marginRight": "4px"}),
            f"Elo ratings start at {BASE_ELO} for all teams and update after each result (K={K_FACTOR}). "
            f"Based on {n_finished} completed matches. "
            f"Qualification probabilities from {N_SIMS} Monte Carlo simulations. "
            "Championship probability uses Elo softmax — not a full bracket simulation.",
        ],
        className="elo-method-note",
    )

    return html.Div(
        [
            html.Div(
                [
                    html.H2("Predictions & Power Rankings", className="page-title"),
                    html.P("Elo-driven forecasts updated after every result", className="page-subtitle"),
                ],
                className="page-hero",
            ),
            method_note,

            # ── Charts row ────────────────────────────────────────────────────
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [html.H5("Power Rankings  (Top 20)", className="chart-title"), rankings_chart],
                            className="chart-card",
                        ),
                        lg=7,
                    ),
                    dbc.Col(
                        html.Div(
                            [html.H5("🏆  Championship Probability", className="chart-title"), winner_chart],
                            className="chart-card",
                        ),
                        lg=5,
                    ),
                ],
                className="g-4 mt-1",
            ),

            # ── Upcoming predictions ──────────────────────────────────────────
            html.Div(
                [
                    html.H5("Upcoming Match Predictions", className="chart-title mb-3"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("■", style={"color": "#22c55e", "marginRight": "4px"}), "Home win  ",
                                    html.Span("■", style={"color": "#6b7280", "margin": "0 4px 0 12px"}), "Draw  ",
                                    html.Span("■", style={"color": "#3b82f6", "margin": "0 4px 0 12px"}), "Away win",
                                ],
                                className="pred-legend mb-3",
                            ),
                            html.Div(pred_cards, className="pred-grid") if pred_cards
                            else html.P("No upcoming matches.", className="text-secondary"),
                        ]
                    ),
                ],
                className="chart-card mt-4",
            ),

            # ── Group qualification ───────────────────────────────────────────
            html.Div(
                [html.H5("Group Qualification Probability", className="chart-title mb-3"),
                 html.P("Probability of finishing top 2 in group based on remaining fixtures.", className="page-subtitle mb-3"),
                 html.Div(group_rows)],
                className="chart-card mt-4",
            ),
        ]
    )
