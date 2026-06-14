from collections import defaultdict
from datetime import datetime, timezone

import dash_bootstrap_components as dbc
from dash import html

import api


def layout() -> html.Div:
    try:
        data = api.get_matches()
    except Exception as e:
        return dbc.Alert(str(e), color="warning", className="m-4")

    all_matches = data.get("matches", [])
    matches     = [m for m in all_matches if m.get("status") == "FINISHED"]

    if not matches:
        return html.Div(
            [
                html.Div("🏟️", style={"fontSize": "3rem"}),
                html.H4("No matches played yet", className="text-secondary mt-3"),
            ],
            className="text-center py-5",
        )

    # Summary stats
    total_goals = 0
    clean_sheets = 0
    high_score = 0
    high_match = None

    for m in matches:
        ft = m.get("score", {}).get("fullTime", {})
        hg = ft.get("home") or 0
        ag = ft.get("away") or 0
        total_goals += hg + ag
        if hg == 0 or ag == 0:
            clean_sheets += 1
        goals = hg + ag
        if goals > high_score:
            high_score = goals
            high_match = m

    avg_goals = round(total_goals / len(matches), 2) if matches else 0

    home_hn  = sum(1 for m in matches if m.get("score", {}).get("winner") == "HOME_TEAM")
    draws_n  = sum(1 for m in matches if m.get("score", {}).get("winner") == "DRAW")
    away_wn  = sum(1 for m in matches if m.get("score", {}).get("winner") == "AWAY_TEAM")

    def stat_card(value, label, color="#f0c030"):
        return html.Div(
            [html.Div(str(value), className="played-stat-num", style={"color": color}),
             html.Div(label, className="played-stat-lbl")],
            className="played-stat-card",
        )

    stats_row = html.Div(
        [
            stat_card(len(matches),  "Matches Played"),
            stat_card(total_goals,   "Goals Scored",      "#22c55e"),
            stat_card(avg_goals,     "Goals / Match",     "#60a5fa"),
            stat_card(clean_sheets,  "Clean Sheets",      "#a78bfa"),
            stat_card(home_hn,       "Home Wins",         "#f0c030"),
            stat_card(draws_n,       "Draws",             "#6b7280"),
            stat_card(away_wn,       "Away Wins",         "#f59e0b"),
        ],
        className="played-stats-row",
    )

    # Highest-scoring match highlight
    highlight = html.Span()
    if high_match:
        hm_home  = high_match.get("homeTeam", {})
        hm_away  = high_match.get("awayTeam", {})
        hm_ft    = high_match.get("score", {}).get("fullTime", {})
        hm_crest_h = html.Img(src=hm_home.get("crest",""), className="crest-sm") if hm_home.get("crest") else html.Span()
        hm_crest_a = html.Img(src=hm_away.get("crest",""), className="crest-sm") if hm_away.get("crest") else html.Span()
        highlight = html.Div(
            [
                html.Div("🔥 Highest Scoring", className="highlight-label"),
                html.Div(
                    [
                        hm_crest_h, html.Span(hm_home.get("shortName","?"), className="hl-name"),
                        html.Span(f" {hm_ft.get('home')}–{hm_ft.get('away')} ", className="hl-score"),
                        html.Span(hm_away.get("shortName","?"), className="hl-name"), hm_crest_a,
                    ],
                    className="hl-match",
                ),
            ],
            className="highlight-card",
        )

    # W/D/L bar
    total_n = len(matches)
    wdl_bar = html.Div(
        [
            html.Div(
                [
                    html.Div(className="wdl-seg wdl-home", style={"flex": str(home_hn / max(total_n, 1))}),
                    html.Div(className="wdl-seg wdl-draw", style={"flex": str(draws_n / max(total_n, 1))}),
                    html.Div(className="wdl-seg wdl-away", style={"flex": str(away_wn / max(total_n, 1))}),
                ],
                className="wdl-bar",
            ),
            html.Div(
                [
                    html.Span([html.Span("■ ", style={"color":"#f0c030"}), f"Home wins ({home_hn})"]),
                    html.Span([html.Span("■ ", style={"color":"#374151"}), f"Draws ({draws_n})"]),
                    html.Span([html.Span("■ ", style={"color":"#60a5fa"}), f"Away wins ({away_wn})"]),
                ],
                className="wdl-legend",
            ),
        ],
        className="wdl-section",
    )

    # Matches grouped by date
    by_date: dict = defaultdict(list)
    for m in matches:
        try:
            key = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).date()
        except Exception:
            key = None
        by_date[key].append(m)

    def result_row(match):
        home   = match.get("homeTeam", {})
        away   = match.get("awayTeam", {})
        ft     = match.get("score", {}).get("fullTime", {})
        hs, as_ = ft.get("home", 0), ft.get("away", 0)
        winner = match.get("score", {}).get("winner", "")
        group  = match.get("group", "")
        label  = group.replace("GROUP_", "Group ") if group else ""

        def crest(t):
            return html.Img(src=t.get("crest",""), className="fix-crest") if t.get("crest") else html.Span(t.get("tla",""), className="fix-tla")

        hw_cls = "fix-team fix-home" + (" fix-winner" if winner == "HOME_TEAM" else "")
        aw_cls = "fix-team fix-away" + (" fix-winner" if winner == "AWAY_TEAM" else "")

        return html.Div(
            [
                html.Span(label, className="fix-label"),
                html.Div(
                    [
                        html.Div([crest(home), html.Span(home.get("shortName") or home.get("name","?"), className="fix-name")], className=hw_cls),
                        html.Span(f"{hs}–{as_}", className="fix-score"),
                        html.Div([html.Span(away.get("shortName") or away.get("name","?"), className="fix-name"), crest(away)], className=aw_cls),
                    ],
                    className="fix-teams",
                ),
                dbc.Badge("FT", color="secondary", className="status-badge"),
            ],
            className="fix-row",
        )

    sections = []
    for date in sorted(d for d in by_date if d):
        day = by_date[date]
        sections.append(
            html.Div(
                [
                    html.Div(date.strftime("%A, %B %-d"), className="fix-date-label"),
                    html.Div([result_row(m) for m in day], className="fix-day-list"),
                ],
                className="fix-date-section",
            )
        )

    return html.Div(
        [
            html.Div(
                [html.H2("Played Matches", className="page-title"),
                 html.P(f"{len(matches)} matches completed", className="page-subtitle")],
                className="page-hero",
            ),
            stats_row,
            html.Div([highlight, wdl_bar], className="played-highlights"),
            html.Div(sections, className="fixtures-list mt-4"),
        ]
    )
