from collections import defaultdict
from datetime import datetime, timezone

import dash_bootstrap_components as dbc
from dash import html

import api

STAGE_LABELS = {
    "GROUP_STAGE":    "Group Stage",
    "LAST_32":        "Round of 32",
    "LAST_16":        "Round of 16",
    "QUARTER_FINALS": "Quarter Finals",
    "SEMI_FINALS":    "Semi Finals",
    "THIRD_PLACE":    "Third Place",
    "FINAL":          "Final",
}

STATUS_MAP = {
    "LIVE":      ("danger",    "⚡ LIVE"),
    "IN_PLAY":   ("danger",    "⚡ LIVE"),
    "PAUSED":    ("warning",   "HT"),
    "FINISHED":  ("secondary", "FT"),
    "SCHEDULED": ("primary",   "UPCOMING"),
    "TIMED":     ("primary",   "UPCOMING"),
}


def _status_badge(status: str) -> dbc.Badge:
    color, label = STATUS_MAP.get(status, ("secondary", status))
    return dbc.Badge(label, color=color, className="status-badge")


def _fmt(utc: str) -> str:
    try:
        dt = datetime.fromisoformat(utc.replace("Z", "+00:00"))
        return dt.strftime("%H:%M UTC")
    except Exception:
        return ""


def _fixture_row(match: dict) -> html.Div:
    home   = match.get("homeTeam", {})
    away   = match.get("awayTeam", {})
    score  = match.get("score", {})
    status = match.get("status", "")
    group  = match.get("group", "")
    stage  = match.get("stage", "")
    label  = group.replace("GROUP_", "Group ") if group else STAGE_LABELS.get(stage, stage)

    ft = score.get("fullTime", {})
    hs, as_ = ft.get("home"), ft.get("away")
    has_score = status in ("FINISHED", "IN_PLAY", "LIVE", "PAUSED")

    def team_img(t):
        crest = t.get("crest", "")
        return html.Img(src=crest, className="fix-crest") if crest else html.Span(t.get("tla","?"), className="fix-tla")

    winner = score.get("winner", "")
    home_cls = "fix-team fix-home" + (" fix-winner" if winner == "HOME_TEAM" else "")
    away_cls = "fix-team fix-away" + (" fix-winner" if winner == "AWAY_TEAM" else "")

    score_el = (
        html.Span(f"{hs}–{as_}", className="fix-score")
        if has_score and hs is not None
        else html.Span(_fmt(match.get("utcDate", "")), className="fix-time")
    )

    return html.Div(
        [
            html.Span(label, className="fix-label"),
            html.Div(
                [
                    html.Div([team_img(home), html.Span(home.get("shortName") or home.get("name","?"), className="fix-name")], className=home_cls),
                    html.Div(score_el, className="fix-score-col"),
                    html.Div([html.Span(away.get("shortName") or away.get("name","?"), className="fix-name"), team_img(away)], className=away_cls),
                ],
                className="fix-teams",
            ),
            _status_badge(status),
        ],
        className="fix-row" + (" fix-row-live" if status in ("IN_PLAY","LIVE") else ""),
    )


def layout() -> html.Div:
    try:
        data = api.get_matches()
    except Exception as e:
        return dbc.Alert(str(e), color="warning", className="m-4")

    matches = data.get("matches", [])
    today   = datetime.now(timezone.utc).date()

    by_date: dict = defaultdict(list)
    for m in matches:
        try:
            key = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).date()
        except Exception:
            key = None
        by_date[key].append(m)

    total     = len(matches)
    played    = sum(1 for m in matches if m.get("status") == "FINISHED")
    remaining = total - played

    sections = []
    for date in sorted(d for d in by_date if d):
        day      = by_date[date]
        is_today = date == today
        label    = "TODAY" if is_today else date.strftime("%A, %B %-d")

        sections.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(label, className="fix-date-label" + (" fix-date-today" if is_today else "")),
                            dbc.Badge(f"{len(day)}", color="secondary", className="ms-2"),
                        ],
                        className="fix-date-header",
                    ),
                    html.Div([_fixture_row(m) for m in day], className="fix-day-list"),
                ],
                className="fix-date-section",
            )
        )

    return html.Div(
        [
            html.Div(
                [
                    html.H2("All Fixtures", className="page-title"),
                    html.Div(
                        [
                            html.Div([html.Div(str(total), className="summary-num"), html.Div("Total", className="summary-lbl")], className="summary-pill"),
                            html.Div([html.Div(str(played), className="summary-num text-success"), html.Div("Played", className="summary-lbl")], className="summary-pill"),
                            html.Div([html.Div(str(remaining), className="summary-num text-primary"), html.Div("Remaining", className="summary-lbl")], className="summary-pill"),
                        ],
                        className="summary-row",
                    ),
                ],
                className="page-hero",
            ),
            html.Div(sections, className="fixtures-list"),
        ]
    )
