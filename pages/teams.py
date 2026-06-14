from datetime import datetime

import dash_bootstrap_components as dbc
from dash import html

import api

POSITION_ORDER = ["Goalkeeper", "Defence", "Midfield", "Offence"]
POSITION_LABEL = {"Goalkeeper": "GK", "Defence": "DEF", "Midfield": "MID", "Offence": "FWD"}
POSITION_COLOR = {"Goalkeeper": "#f59e0b", "Defence": "#22c55e", "Midfield": "#60a5fa", "Offence": "#ef4444"}


def _age(dob_str: str) -> str:
    try:
        dob = datetime.fromisoformat(dob_str)
        return str((datetime.now() - dob).days // 365)
    except Exception:
        return "?"


def _squad_body(team: dict) -> html.Div:
    squad = team.get("squad", [])
    coach = team.get("coach", {})
    colors = team.get("clubColors", "")

    by_pos: dict = {p: [] for p in POSITION_ORDER}
    for p in squad:
        pos = p.get("position", "Midfield")
        if pos in by_pos:
            by_pos[pos].append(p)

    position_sections = []
    for pos in POSITION_ORDER:
        players = by_pos[pos]
        if not players:
            continue
        chips = [
            html.Div(
                [
                    html.Span(p.get("name", "?"), className="player-name"),
                    html.Span(_age(p.get("dateOfBirth", "")), className="player-age"),
                ],
                className="player-chip",
            )
            for p in players
        ]
        position_sections.append(
            html.Div(
                [
                    html.Span(
                        POSITION_LABEL[pos],
                        className="pos-tag",
                        style={"background": POSITION_COLOR[pos] + "22", "color": POSITION_COLOR[pos]},
                    ),
                    html.Div(chips, className="player-chips-row"),
                ],
                className="position-section",
            )
        )

    meta = []
    if coach.get("name"):
        meta.append(html.Span([html.Span("Coach  ", className="meta-label"), coach["name"]], className="team-meta-item"))
    if team.get("founded"):
        meta.append(html.Span([html.Span("Founded  ", className="meta-label"), str(team["founded"])], className="team-meta-item"))
    if colors:
        meta.append(html.Span([html.Span("Colors  ", className="meta-label"), colors], className="team-meta-item"))

    return html.Div(
        [
            html.Div(meta, className="team-meta-row") if meta else html.Span(),
            html.Div(position_sections, className="squad-sections"),
        ],
        className="squad-body",
    )


def _accordion_title(entry: dict, full_team: dict) -> html.Div:
    team  = entry.get("team", {})
    crest = team.get("crest", "") or full_team.get("crest", "")
    name  = team.get("name", "?")
    pos   = entry.get("position", 0)
    pts   = entry.get("points", 0)
    played = entry.get("playedGames", 0)

    pos_cls = "acc-pos-badge" + (" acc-pos-advance" if pos <= 2 else "")

    return html.Div(
        [
            html.Span(str(pos), className=pos_cls),
            html.Img(src=crest, className="acc-crest") if crest else html.Span(team.get("tla",""), className="acc-tla"),
            html.Span(name, className="acc-team-name"),
            html.Div(
                [
                    html.Span(f"{pts} pts", className="acc-pts"),
                    html.Span(f"{played}G", className="acc-played"),
                ],
                className="acc-stats",
            ),
        ],
        className="acc-header-inner",
    )


def layout() -> html.Div:
    try:
        standings_data = api.get_standings()
        teams_data     = api.get_teams()
    except Exception as e:
        return dbc.Alert(str(e), color="warning", className="m-4")

    standings = [s for s in standings_data.get("standings", []) if s.get("type") == "TOTAL"]
    standings.sort(key=lambda s: s.get("group", ""))

    team_lookup = {t["id"]: t for t in teams_data.get("teams", [])}

    group_sections = []
    for s in standings:
        group = s.get("group", "")
        letter = group.split()[-1] if group else "?"
        table  = s.get("table", [])

        items = []
        for entry in table:
            team_id   = entry.get("team", {}).get("id")
            full_team = team_lookup.get(team_id, {})
            items.append(
                dbc.AccordionItem(
                    _squad_body(full_team),
                    title=_accordion_title(entry, full_team),
                    className="team-accordion-item",
                )
            )

        group_sections.append(
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            [html.Span(letter, className="group-letter"), html.Span(group, className="group-label-text")],
                            className="group-card-header",
                        ),
                        dbc.Accordion(items, start_collapsed=True, flush=True, className="team-accordion"),
                    ],
                    className="group-card",
                ),
                lg=6, md=12, className="mb-4",
            )
        )

    rows = []
    for i in range(0, len(group_sections), 2):
        rows.append(dbc.Row(group_sections[i : i + 2], className="g-4"))

    return html.Div(
        [
            html.Div(
                [
                    html.H2("All 48 Teams", className="page-title"),
                    html.P("Click a team to expand their squad", className="page-subtitle"),
                ],
                className="page-hero",
            ),
            html.Div(rows),
        ]
    )
