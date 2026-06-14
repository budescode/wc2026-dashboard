from datetime import datetime, timezone

import dash_bootstrap_components as dbc
from dash import html

import api


def _fmt_kickoff(utc: str) -> str:
    try:
        dt = datetime.fromisoformat(utc.replace("Z", "+00:00"))
        return dt.strftime("%b %-d  ·  %H:%M UTC")
    except Exception:
        return utc or ""


def _live_match_card(match: dict) -> html.Div:
    home   = match.get("homeTeam", {})
    away   = match.get("awayTeam", {})
    score  = match.get("score", {})
    status = match.get("status", "")
    group  = match.get("group", "")
    stage  = match.get("stage", "").replace("_", " ").title()
    label  = group.replace("GROUP_", "Group ") if group else stage

    ft  = score.get("fullTime", {})
    ht  = score.get("halfTime", {})
    hs, as_ = ft.get("home"), ft.get("away")
    hht, aht = ht.get("home"), ht.get("away")

    status_label = "HALF TIME" if status == "PAUSED" else "LIVE"

    def team_col(team, score_val, is_home=True):
        crest = team.get("crest", "")
        name  = team.get("shortName") or team.get("name", "?")
        return html.Div(
            [
                html.Img(src=crest, className="live-crest") if crest else html.Span(team.get("tla",""), className="live-tla"),
                html.Div(name, className="live-team-name"),
                html.Div(str(score_val) if score_val is not None else "—", className="live-score-num"),
            ],
            className="live-team-col" + ("" if is_home else " live-away-col"),
        )

    return html.Div(
        [
            html.Div(
                [
                    html.Span(label, className="live-label"),
                    html.Span(
                        [html.Span("⚡ "), status_label],
                        className="live-status-badge",
                    ),
                ],
                className="live-card-header",
            ),
            html.Div(
                [
                    team_col(home, hs, is_home=True),
                    html.Div("VS", className="live-vs-sep"),
                    team_col(away, as_, is_home=False),
                ],
                className="live-teams-row",
            ),
            html.Div(
                f"HT  {hht} – {aht}" if hht is not None and status != "PAUSED" else "",
                className="live-ht-score",
            ) if hht is not None else html.Span(),
            html.Div("🔄 Auto-refreshes every 20 seconds", className="live-refresh-note"),
        ],
        className="live-match-card",
    )


def _upcoming_card(match: dict) -> html.Div:
    home  = match.get("homeTeam", {})
    away  = match.get("awayTeam", {})
    group = match.get("group", "")
    label = group.replace("GROUP_", "Group ") if group else match.get("stage", "").replace("_", " ").title()

    def crest(t):
        return html.Img(src=t.get("crest",""), className="crest-sm") if t.get("crest") else html.Span(t.get("tla",""), className="tla-xs")

    return html.Div(
        [
            html.Span(label, className="fix-label"),
            html.Div(
                [
                    html.Div([crest(home), html.Span(home.get("shortName") or home.get("name","?"), className="fix-name")], className="fix-team fix-home"),
                    html.Span(_fmt_kickoff(match.get("utcDate","")), className="fix-time"),
                    html.Div([html.Span(away.get("shortName") or away.get("name","?"), className="fix-name"), crest(away)], className="fix-team fix-away"),
                ],
                className="fix-teams",
            ),
            dbc.Badge("UPCOMING", color="primary", className="status-badge"),
        ],
        className="fix-row",
    )


def layout() -> html.Div:
    try:
        data = api.get_matches()
    except Exception as e:
        return dbc.Alert(str(e), color="warning", className="m-4")

    matches  = data.get("matches", [])
    live     = [m for m in matches if m.get("status") in ("IN_PLAY", "LIVE", "PAUSED")]
    upcoming = [m for m in matches if m.get("status") in ("SCHEDULED", "TIMED")]

    now = datetime.now(timezone.utc)
    upcoming_sorted = sorted(
        upcoming,
        key=lambda m: m.get("utcDate", ""),
    )[:6]

    if live:
        content = html.Div(
            [
                html.Div(
                    [html.H2("Live Now", className="page-title"),
                     html.P(f"{len(live)} match{'es' if len(live) > 1 else ''} in progress", className="page-subtitle")],
                    className="page-hero",
                ),
                html.Div([_live_match_card(m) for m in live], className="live-cards-grid"),
                html.Hr(className="modal-divider mt-4"),
                html.H5("Up Next", className="chart-title mt-2"),
                html.Div([_upcoming_card(m) for m in upcoming_sorted], className="fix-day-list mt-2"),
            ]
        )
    else:
        content = html.Div(
            [
                html.Div(
                    [html.H2("Live", className="page-title"),
                     html.P("No matches in progress right now", className="page-subtitle")],
                    className="page-hero",
                ),
                html.Div(
                    [
                        html.Div("📡", style={"fontSize": "3rem"}),
                        html.H4("Nothing Live Right Now", className="mt-3 text-secondary"),
                        html.P("Check back when the next match kicks off.", className="text-secondary small"),
                    ],
                    className="text-center py-4",
                ),
                html.H5("Upcoming Fixtures", className="chart-title mt-2"),
                html.Div([_upcoming_card(m) for m in upcoming_sorted], className="fix-day-list mt-2"),
            ]
        )

    return content
