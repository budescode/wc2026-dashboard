from datetime import datetime
from urllib.parse import parse_qs

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html, no_update

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
    squad  = team.get("squad", [])
    coach  = team.get("coach", {})
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


def _team_detail_card(team: dict, entry: dict) -> html.Div:
    crest  = team.get("crest", "")
    name   = team.get("name", "?")
    tla    = team.get("tla", "")
    coach  = team.get("coach", {})
    colors = team.get("clubColors", "")
    venue  = team.get("venue", "")
    founded = team.get("founded", "")
    website = team.get("website", "")

    pos    = entry.get("position", "—")
    pts    = entry.get("points", 0)
    played = entry.get("playedGames", 0)
    won    = entry.get("won", 0)
    draw   = entry.get("draw", 0)
    lost   = entry.get("lost", 0)
    gf     = entry.get("goalsFor", 0)
    ga     = entry.get("goalsAgainst", 0)
    gd     = entry.get("goalDifference", 0)
    group  = entry.get("group", "")

    gd_str = f"+{gd}" if gd > 0 else str(gd)
    gd_color = "#22c55e" if gd > 0 else "#ef4444" if gd < 0 else "var(--text-muted)"

    def stat_pill(val, lbl, color="var(--gold)"):
        return html.Div(
            [
                html.Div(str(val), className="td-stat-num", style={"color": color, "fontFamily": "Rajdhani,sans-serif", "fontSize": "1.5rem", "fontWeight": "700", "lineHeight": "1"}),
                html.Div(lbl, className="played-stat-lbl"),
            ],
            className="played-stat-card",
        )

    squad = team.get("squad", [])
    by_pos: dict = {p: [] for p in POSITION_ORDER}
    for p in squad:
        pos_key = p.get("position", "Midfield")
        if pos_key in by_pos:
            by_pos[pos_key].append(p)

    position_sections = []
    for pos_key in POSITION_ORDER:
        players = by_pos[pos_key]
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
                        POSITION_LABEL[pos_key],
                        className="pos-tag",
                        style={"background": POSITION_COLOR[pos_key] + "22", "color": POSITION_COLOR[pos_key]},
                    ),
                    html.Div(chips, className="player-chips-row"),
                ],
                className="position-section",
            )
        )

    return html.Div(
        [
            # Header row
            html.Div(
                [
                    html.Img(src=crest, className="team-detail-crest") if crest else html.Span(tla, style={"fontSize": "3rem", "fontWeight": "700", "color": "var(--gold)"}),
                    html.Div(
                        [
                            html.H3(name, className="team-detail-name"),
                            html.Div(
                                [
                                    dbc.Badge(group, color="secondary", className="me-2"),
                                    dbc.Badge(f"#{entry.get('position','?')} in group", color="warning", text_color="dark"),
                                ],
                                className="mt-1",
                            ),
                            html.Div(
                                [
                                    html.Span([html.Span("Coach  ", className="meta-label"), coach.get("name", "—")], className="team-meta-item me-3") if coach.get("name") else None,
                                    html.Span([html.Span("Founded  ", className="meta-label"), str(founded)], className="team-meta-item me-3") if founded else None,
                                    html.Span([html.Span("Venue  ", className="meta-label"), venue], className="team-meta-item me-3") if venue else None,
                                    html.Span([html.Span("Colors  ", className="meta-label"), colors], className="team-meta-item") if colors else None,
                                ],
                                className="team-meta-row mt-2",
                            ),
                        ]
                    ),
                ],
                className="team-detail-header",
            ),
            # Stats row
            html.Div(
                [
                    stat_pill(played, "Played",        "var(--text-secondary)"),
                    stat_pill(won,    "Won",            "#22c55e"),
                    stat_pill(draw,   "Drawn",          "#f59e0b"),
                    stat_pill(lost,   "Lost",           "#ef4444"),
                    stat_pill(f"{gf}:{ga}", "GF:GA",   "#60a5fa"),
                    stat_pill(gd_str, "Goal Diff",      gd_color),
                    stat_pill(pts,    "Points",         "var(--gold)"),
                ],
                className="played-stats-row mt-3",
            ),
            html.Hr(style={"borderColor": "var(--border)", "margin": "16px 0"}),
            # Squad
            html.Div("Squad", className="modal-section-label mb-2"),
            html.Div(position_sections, className="squad-sections"),
        ],
        className="team-detail-card",
    )


def _accordion_title(entry: dict, full_team: dict) -> html.Div:
    team   = entry.get("team", {})
    crest  = team.get("crest", "") or full_team.get("crest", "")
    name   = team.get("name", "?")
    pos    = entry.get("position", 0)
    pts    = entry.get("points", 0)
    played = entry.get("playedGames", 0)

    pos_cls = "acc-pos-badge" + (" acc-pos-advance" if pos <= 2 else "")

    return html.Div(
        [
            html.Span(str(pos), className=pos_cls),
            html.Img(src=crest, className="acc-crest") if crest else html.Span(team.get("tla", ""), className="acc-tla"),
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


# ── Callback ───────────────────────────────────────────────────────────────────

@callback(
    Output("team-detail-panel", "children"),
    Input("team-search-dropdown", "value"),
    prevent_initial_call=True,
)
def show_team_detail(team_id):
    if not team_id:
        return html.Span()
    try:
        standings_data = api.get_standings()
        teams_data     = api.get_teams()
    except Exception as e:
        return dbc.Alert(str(e), color="warning")

    team_lookup = {t["id"]: t for t in teams_data.get("teams", [])}
    full_team   = team_lookup.get(int(team_id), {})
    if not full_team:
        return dbc.Alert("Team not found.", color="secondary")

    standings = [s for s in standings_data.get("standings", []) if s.get("type") == "TOTAL"]
    entry = {}
    for s in standings:
        for row in s.get("table", []):
            if row.get("team", {}).get("id") == int(team_id):
                entry = {**row, "group": s.get("group", "")}
                break

    return _team_detail_card(full_team, entry)


# ── Layout ─────────────────────────────────────────────────────────────────────

def _get_entry(team_id: int, standings: list) -> dict:
    for s in standings:
        for row in s.get("table", []):
            if row.get("team", {}).get("id") == team_id:
                return {**row, "group": s.get("group", "")}
    return {}


def layout(search: str = "") -> html.Div:
    try:
        standings_data = api.get_standings()
        teams_data     = api.get_teams()
    except Exception as e:
        return dbc.Alert(str(e), color="warning", className="m-4")

    standings  = [s for s in standings_data.get("standings", []) if s.get("type") == "TOTAL"]
    standings.sort(key=lambda s: s.get("group", ""))
    team_lookup = {t["id"]: t for t in teams_data.get("teams", [])}

    # Parse ?team=<id> query param
    preselect_id = None
    try:
        params = parse_qs(search.lstrip("?"))
        preselect_id = int(params.get("team", [None])[0])
    except (TypeError, ValueError, IndexError):
        pass

    # Pre-render detail card if arriving via URL
    initial_detail = html.Span()
    if preselect_id and preselect_id in team_lookup:
        initial_detail = _team_detail_card(
            team_lookup[preselect_id],
            _get_entry(preselect_id, standings),
        )

    # Build dropdown options sorted alphabetically — text only to keep rendering fast
    all_teams = sorted(teams_data.get("teams", []), key=lambda t: t.get("name", ""))
    dropdown_options = [
        {"label": t.get("name", "?"), "value": t["id"]}
        for t in all_teams
    ]

    # Group sections — lightweight rows only, no squad pre-rendering
    group_sections = []
    for s in standings:
        group  = s.get("group", "")
        letter = group.split()[-1] if group else "?"
        table  = s.get("table", [])

        rows = []
        for entry in table:
            team      = entry.get("team", {})
            team_id   = team.get("id")
            full_team = team_lookup.get(team_id, {})
            crest     = full_team.get("crest", "") or team.get("crest", "")
            name      = team.get("name", "?")
            pos       = entry.get("position", 0)
            pts       = entry.get("points", 0)
            played    = entry.get("playedGames", 0)
            won       = entry.get("won", 0)
            draw      = entry.get("draw", 0)
            lost      = entry.get("lost", 0)
            gd        = entry.get("goalDifference", 0)
            gd_str    = f"+{gd}" if gd > 0 else str(gd)
            gd_color  = "#22c55e" if gd > 0 else "#ef4444" if gd < 0 else "var(--text-muted)"
            advance   = pos <= 2

            rows.append(
                html.Div(
                    [
                        html.Span(str(pos), className="acc-pos-badge" + (" acc-pos-advance" if advance else "")),
                        html.Img(src=crest, className="acc-crest") if crest else html.Span(team.get("tla", ""), className="acc-tla"),
                        html.Span(name, className="acc-team-name"),
                        html.Div(
                            [
                                html.Span(f"{won}W {draw}D {lost}L", style={"fontSize": "0.72rem", "color": "var(--text-muted)", "marginRight": "10px"}),
                                html.Span(gd_str, style={"fontSize": "0.72rem", "color": gd_color, "marginRight": "10px", "fontWeight": "600"}),
                                html.Span(f"{pts} pts", className="acc-pts"),
                                html.Span(f"{played}G", className="acc-played"),
                            ],
                            className="acc-stats",
                        ),
                    ],
                    className="acc-header-inner group-team-row",
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
                        html.Div(rows, className="group-team-list"),
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
                    html.P("Search for a team or browse by group below", className="page-subtitle"),
                ],
                className="page-hero",
            ),

            # ── Team search dropdown ──────────────────────────────────────────
            html.Div(
                [
                    dcc.Dropdown(
                        id="team-search-dropdown",
                        options=dropdown_options,
                        value=preselect_id,
                        placeholder="🔍  Search for a team...",
                        clearable=True,
                        searchable=True,
                        className="team-dropdown",
                    ),
                    dcc.Loading(
                        html.Div(initial_detail, id="team-detail-panel", className="mt-3"),
                        type="circle",
                        color="#f0c030",
                    ),
                ],
                className="team-search-section mb-4",
            ),

            # ── Browse by group ───────────────────────────────────────────────
            html.Div("Browse by group", className="modal-section-label mb-3"),
            html.Div(rows),
        ]
    )
