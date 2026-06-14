from datetime import datetime, timezone
from collections import defaultdict

import dash
import dash_bootstrap_components as dbc
from dash import ALL, ctx, dcc, html, callback, Input, Output, State, no_update

import api
import pages.teams as pg_teams
import pages.fixtures as pg_fixtures
import pages.played as pg_played
import pages.goals as pg_goals
import pages.live as pg_live

# ── App Setup ──────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="World Cup 2026 | Dashboard",
    update_title=None,
)
server = app.server

# ── Helpers ────────────────────────────────────────────────────────────────────

def fmt_date(utc_str: str) -> str:
    try:
        dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d  •  %H:%M UTC")
    except Exception:
        return utc_str or ""


def status_badge(status: str) -> dbc.Badge:
    MAP = {
        "LIVE":       ("danger",    "⚡ LIVE"),
        "IN_PLAY":    ("danger",    "⚡ LIVE"),
        "PAUSED":     ("warning",   "HT"),
        "FINISHED":   ("secondary", "FT"),
        "SCHEDULED":  ("primary",   "UPCOMING"),
        "TIMED":      ("primary",   "UPCOMING"),
        "POSTPONED":  ("dark",      "POSTPONED"),
    }
    color, label = MAP.get(status, ("secondary", status))
    pulse = " live-pulse" if status in ("LIVE", "IN_PLAY") else ""
    return dbc.Badge(label, color=color, className=f"status-badge{pulse}")


def form_dots(form_str: str):
    if not form_str:
        return html.Span("—", className="text-muted")
    parts = [r.strip() for r in form_str.split(",") if r.strip()]
    dots = []
    for r in parts[-5:]:
        cls = "form-dot win" if r == "W" else "form-dot draw" if r == "D" else "form-dot loss"
        dots.append(html.Span(r, className=cls))
    return html.Span(dots, className="form-dots")


def error_card(msg: str):
    return dbc.Alert(
        [
            html.H5("⚠️  Data Unavailable", className="alert-heading mb-1"),
            html.P(msg, className="mb-1 small"),
            html.P("Check your API key in .env and try refreshing.", className="mb-0 small"),
        ],
        color="warning",
        className="mt-4",
    )


# ── Header ─────────────────────────────────────────────────────────────────────

def build_header(matches_data: dict | None = None, pathname: str = "") -> html.Div:
    total_goals = matches_played = live_count = total_matches = 0

    if matches_data:
        for m in matches_data.get("matches", []):
            total_matches += 1
            status = m.get("status", "")
            if status == "FINISHED":
                matches_played += 1
                ft = m.get("score", {}).get("fullTime", {})
                total_goals += (ft.get("home") or 0) + (ft.get("away") or 0)
            elif status in ("LIVE", "IN_PLAY", "PAUSED"):
                live_count += 1

    def pill(value, label, href="/", extra_cls=""):
        is_active = pathname == href
        cls = f"stat-pill {extra_cls}" + (" stat-pill-active" if is_active else "")
        inner = html.Div(
            [
                html.Div(str(value), className="stat-pill-value"),
                html.Div(label, className="stat-pill-label"),
            ],
            className=cls,
        )
        return dcc.Link(inner, href=href, style={"textDecoration": "none"})

    return html.Div(
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("🏆", className="wc-trophy me-3"),
                                html.Div(
                                    [
                                        html.H1("FIFA World Cup 2026", className="wc-title"),
                                        html.Div(
                                            "United States  ·  Canada  ·  Mexico",
                                            className="wc-subtitle",
                                        ),
                                    ]
                                ),
                            ],
                            className="d-flex align-items-center",
                        ),
                        xs=12, lg="auto",
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                pill(48,                  "Teams",    href="/teams"),
                                pill(total_matches,       "Fixtures", href="/fixtures"),
                                pill(matches_played,      "Played",   href="/played"),
                                pill(total_goals,         "Goals",    href="/goals"),
                                pill(live_count or "—",   "Live Now", href="/live",
                                     extra_cls="live-pill" if live_count else ""),
                            ],
                            className="header-stats",
                        ),
                        xs=12, lg=True,
                        className="d-flex align-items-end justify-content-lg-end",
                    ),
                ],
                align="end", className="g-0",
            ),
            fluid=True,
        ),
        className="wc-header",
    )


# ── Groups Tab ─────────────────────────────────────────────────────────────────

def group_card(group_name: str, table: list) -> html.Div:
    # group_name arrives as "Group A" from standings API
    letter = group_name.split()[-1] if group_name else "?"

    rows = []
    for entry in table:
        pos   = entry.get("position", 0)
        team  = entry.get("team", {})
        crest = team.get("crest", "")
        name  = team.get("name", "?")
        p, w, d, l = (entry.get(k, 0) for k in ("playedGames", "won", "draw", "lost"))
        gf    = entry.get("goalsFor", 0)
        ga    = entry.get("goalsAgainst", 0)
        gd    = entry.get("goalDifference", 0)
        pts   = entry.get("points", 0)

        gd_str = f"+{gd}" if gd > 0 else str(gd)
        gd_cls = "text-success" if gd > 0 else "text-danger" if gd < 0 else "text-secondary"
        pos_cls = f"pos-badge pos-{pos}"
        row_cls = "group-row advance" if pos <= 2 else "group-row eliminated"

        crest_el = (
            html.Img(src=crest, className="crest-sm")
            if crest else
            html.Span(team.get("tla", "")[:3], className="tla-xs")
        )

        rows.append(
            html.Tr(
                [
                    html.Td(html.Span(str(pos), className=pos_cls), className="td-pos"),
                    html.Td([crest_el, html.Span(name, className="td-team-name")], className="td-team"),
                    html.Td(str(p), className="td-stat"),
                    html.Td(str(w), className="td-stat fw-600 text-success"),
                    html.Td(str(d), className="td-stat text-warning"),
                    html.Td(str(l), className="td-stat text-danger"),
                    html.Td(f"{gf}:{ga}", className="td-stat text-secondary"),
                    html.Td(html.Span(gd_str, className=gd_cls), className="td-stat"),
                    html.Td(html.Strong(str(pts), className="pts-badge"), className="td-pts"),
                    html.Td(form_dots(entry.get("form", "")), className="td-form"),
                ],
                className=row_cls,
            )
        )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(letter, className="group-letter"),
                    html.Span(group_name, className="group-label-text"),
                ],
                className="group-card-header",
            ),
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("",      className="td-pos"),
                                html.Th("Team",  className="td-team"),
                                html.Th("P",     className="td-stat"),
                                html.Th("W",     className="td-stat"),
                                html.Th("D",     className="td-stat"),
                                html.Th("L",     className="td-stat"),
                                html.Th("GF:GA", className="td-stat"),
                                html.Th("GD",    className="td-stat"),
                                html.Th("Pts",   className="td-pts"),
                                html.Th("Form",  className="td-form"),
                            ],
                            className="group-thead",
                        )
                    ),
                    html.Tbody(rows),
                ],
                className="group-table",
            ),
        ],
        className="group-card",
    )


def render_groups() -> html.Div:
    try:
        data = api.get_standings()
    except Exception as e:
        return error_card(str(e))

    standings = [s for s in data.get("standings", []) if s.get("type") == "TOTAL"]
    standings.sort(key=lambda s: s.get("group", ""))

    if not standings:
        return dbc.Alert("No standings data available yet.", color="secondary", className="mt-4")

    cards = [group_card(s.get("group", f"Group {i+1}"), s.get("table", [])) for i, s in enumerate(standings)]

    rows = []
    for i in range(0, len(cards), 3):
        chunk = cards[i : i + 3]
        cols  = [dbc.Col(c, lg=4, md=6, className="mb-3") for c in chunk]
        rows.append(dbc.Row(cols, className="g-3"))

    return html.Div(
        [
            html.Div(
                [
                    html.Span("🟢 Top 2 advance", className="legend-item advance-legend me-3"),
                    html.Span("⚪ Eliminated", className="legend-item elim-legend"),
                ],
                className="group-legend mb-3",
            ),
            html.Div(rows),
        ]
    )


# ── Scorers Tab ────────────────────────────────────────────────────────────────

def render_scorers() -> html.Div:
    try:
        data = api.get_scorers(limit=25)
    except Exception as e:
        return error_card(str(e))

    scorers = data.get("scorers", [])
    if not scorers:
        return dbc.Alert("No scorer data available yet.", color="secondary", className="mt-4")

    max_goals = scorers[0].get("goals", 1) or 1

    rows = []
    for i, scorer in enumerate(scorers):
        rank    = i + 1
        player  = scorer.get("player", {})
        team    = scorer.get("team", {})
        goals   = scorer.get("goals", 0) or 0
        assists = scorer.get("assists", 0) or 0
        played  = scorer.get("playedMatches", 0) or 0
        pens    = scorer.get("penalties", 0) or 0
        crest   = team.get("crest", "")
        bar_pct = round(goals / max_goals * 100)

        if rank == 1:
            rank_el = html.Span("🥇", className="rank-gold")
        elif rank == 2:
            rank_el = html.Span("🥈", className="rank-silver")
        elif rank == 3:
            rank_el = html.Span("🥉", className="rank-bronze")
        else:
            rank_el = html.Span(str(rank), className="rank-normal")

        crest_el = html.Img(src=crest, className="crest-sm") if crest else html.Span()

        row_cls = "scorer-row scorer-leader" if rank == 1 else "scorer-row"

        rows.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(rank_el, className="scorer-rank"),
                            html.Div(
                                [
                                    html.Div(player.get("name", "?"), className="scorer-name"),
                                    html.Div(
                                        [crest_el, html.Span(team.get("name", ""), className="scorer-team-name")],
                                        className="scorer-team",
                                    ),
                                ],
                                className="scorer-info",
                            ),
                        ],
                        className="scorer-left",
                    ),
                    html.Div(
                        [
                            html.Div(
                                html.Div(className="goal-bar-fill", style={"width": f"{bar_pct}%"}),
                                className="goal-bar",
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        [html.Strong(str(goals)), f" goal{'s' if goals != 1 else ''}"],
                                        className="goals-count",
                                    ),
                                    html.Span(f"{assists} ast", className="assists-count"),
                                    html.Span(f"{pens} pen", className="text-secondary small") if pens else None,
                                    html.Span(f"{played} games", className="games-count"),
                                ],
                                className="scorer-stats",
                            ),
                        ],
                        className="scorer-right",
                    ),
                ],
                className=row_cls,
            )
        )

    return html.Div(
        [
            html.H4("⚽  Golden Boot Race", className="tab-section-title"),
            html.Div(rows, className="scorers-list"),
        ]
    )


# ── Matches Tab ────────────────────────────────────────────────────────────────

def match_card(match: dict) -> html.Div:
    home   = match.get("homeTeam", {})
    away   = match.get("awayTeam", {})
    score  = match.get("score", {})
    status = match.get("status", "")
    group  = match.get("group", "")
    stage  = match.get("stage", "").replace("_", " ").title()
    label  = group.replace("GROUP_", "Group ") if group else STAGE_LABELS.get(match.get("stage", ""), stage)

    ft = score.get("fullTime", {})
    hs, as_ = ft.get("home"), ft.get("away")

    has_score = status in ("FINISHED", "LIVE", "IN_PLAY", "PAUSED")
    score_el  = (
        html.Div(
            [
                html.Span(str(hs) if hs is not None else "—", className="score-num"),
                html.Span(" : ", className="score-sep"),
                html.Span(str(as_) if as_ is not None else "—", className="score-num"),
            ],
            className="score-display",
        )
        if has_score
        else html.Span("vs", className="vs-text")
    )

    winner  = score.get("winner", "")

    def team_block(t: dict, is_home: bool) -> html.Div:
        crest = t.get("crest", "")
        name  = t.get("shortName") or t.get("name") or "TBD"
        tla   = t.get("tla") or name[:3].upper()
        side  = "HOME_TEAM" if is_home else "AWAY_TEAM"
        won   = winner == side

        crest_el = (
            html.Img(src=crest, className="match-crest")
            if crest
            else html.Span(tla, className="match-tla")
        )
        cls = "match-team" + (" winner" if won else "") + ("" if is_home else " away-team")
        return html.Div(
            [crest_el, html.Span(name, className="match-team-name")],
            className=cls,
        )

    card_cls = "match-card" + (" match-live" if status in ("LIVE", "IN_PLAY") else "")
    match_id = match.get("id", 0)

    return html.Div(
        [
            html.Div(
                [html.Span(label, className="match-group-label"), status_badge(status)],
                className="match-card-header",
            ),
            html.Div(
                [team_block(home, True), html.Div(score_el, className="score-center"), team_block(away, False)],
                className="match-body",
            ),
            html.Div(fmt_date(match.get("utcDate", "")), className="match-date"),
        ],
        id={"type": "match-click", "index": match_id},
        n_clicks=0,
        className=card_cls,
        style={"cursor": "pointer"},
    )


def render_matches() -> html.Div:
    try:
        data = api.get_matches()
    except Exception as e:
        return error_card(str(e))

    matches = data.get("matches", [])
    if not matches:
        return dbc.Alert("No match data available yet.", color="secondary", className="mt-4")

    today = datetime.now(timezone.utc).date()
    by_date: dict = defaultdict(list)
    for m in matches:
        try:
            dt  = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
            key = dt.date()
        except Exception:
            key = None
        by_date[key].append(m)

    sections = []
    for date in sorted(d for d in by_date if d):
        day     = by_date[date]
        is_today = date == today
        label   = "TODAY" if is_today else date.strftime("%A, %B %-d")

        sections.append(
            html.Div(
                [
                    html.H5(
                        [
                            html.Span("• ", className="text-warning me-1" if is_today else "text-secondary me-1"),
                            label,
                            dbc.Badge(
                                f"{len(day)} matches",
                                color="secondary",
                                className="ms-2 fw-normal",
                                style={"fontSize": "0.65rem"},
                            ),
                        ],
                        className="date-section-header",
                    ),
                    html.Div([match_card(m) for m in day], className="matches-grid"),
                ],
                className="date-section",
            )
        )

    return html.Div(sections)


# ── Bracket Tab ────────────────────────────────────────────────────────────────

STAGE_ORDER  = ["LAST_32", "LAST_16", "QUARTER_FINALS", "SEMI_FINALS", "THIRD_PLACE", "FINAL"]
STAGE_LABELS = {
    "LAST_32":        "Round of 32",
    "LAST_16":        "Round of 16",
    "QUARTER_FINALS": "Quarter Finals",
    "SEMI_FINALS":    "Semi Finals",
    "THIRD_PLACE":    "Third Place",
    "FINAL":          "Final",
}


def render_bracket() -> html.Div:
    try:
        data    = api.get_matches()
        matches = data.get("matches", [])
    except Exception as e:
        return error_card(str(e))

    ko = [m for m in matches if m.get("stage") in STAGE_ORDER]

    if not ko:
        return html.Div(
            html.Div(
                [
                    html.Div("🏆", className="bracket-trophy"),
                    html.H4("Knockout Bracket", className="bracket-title"),
                    html.P("Will appear here once the Group Stage concludes.", className="text-secondary mt-2"),
                    html.Hr(className="bracket-divider"),
                    dbc.Badge("Group Stage  •  In Progress", color="warning", className="bracket-stage-info px-3 py-2"),
                ],
                className="bracket-placeholder",
            ),
            className="text-center py-5",
        )

    by_stage: dict = defaultdict(list)
    for m in ko:
        by_stage[m.get("stage")].append(m)

    sections = []
    for stage in STAGE_ORDER:
        if stage not in by_stage:
            continue
        sections.append(
            html.Div(
                [
                    html.Div(STAGE_LABELS[stage], className="ko-stage-label"),
                    html.Div([match_card(m) for m in by_stage[stage]], className="matches-grid"),
                ],
                className="ko-stage-section",
            )
        )

    return html.Div(sections)


# ── Match Detail Modal ─────────────────────────────────────────────────────────

def build_modal_content(detail: dict, h2h: dict) -> list:
    home   = detail.get("homeTeam", {})
    away   = detail.get("awayTeam", {})
    score  = detail.get("score", {})
    status = detail.get("status", "")
    group  = detail.get("group", "")
    stage  = detail.get("stage", "").replace("_", " ").title()
    group_label = group.replace("GROUP_", "Group ") if group else STAGE_LABELS.get(detail.get("stage", ""), stage)
    matchday = detail.get("matchday")
    referees = detail.get("referees", [])
    is_live  = status in ("IN_PLAY", "LIVE", "PAUSED")

    ft  = score.get("fullTime", {})
    ht  = score.get("halfTime", {})
    hs, as_ = ft.get("home"), ft.get("away")
    hht, aht = ht.get("home"), ht.get("away")
    winner = score.get("winner", "")

    def crest_name(team, reverse=False):
        crest = team.get("crest", "")
        name  = team.get("name", "?")
        img   = html.Img(src=crest, className="modal-crest") if crest else html.Span(team.get("tla",""), className="modal-tla")
        els   = [img, html.Div(name, className="modal-team-name")]
        return html.Div(list(reversed(els)) if reverse else els,
                        className="modal-team-block" + (" modal-team-right" if reverse else ""))

    # Score or kickoff time
    has_score = status in ("FINISHED", "IN_PLAY", "LIVE", "PAUSED")
    if has_score:
        home_won = winner == "HOME_TEAM"
        away_won = winner == "AWAY_TEAM"
        score_block = html.Div([
            html.Div([
                html.Span(str(hs) if hs is not None else "—",
                          className="modal-score-num" + (" modal-winner-num" if home_won else "")),
                html.Span("–", className="modal-score-sep"),
                html.Span(str(as_) if as_ is not None else "—",
                          className="modal-score-num" + (" modal-winner-num" if away_won else "")),
            ], className="modal-score-main"),
            html.Div(
                f"HT  {hht} – {aht}" if hht is not None else "",
                className="modal-score-ht",
            ),
            html.Div(
                [html.Span("⚡", className="me-1"), "LIVE"],
                className="modal-live-label",
            ) if is_live else html.Span(),
        ], className="modal-score-block")
    else:
        score_block = html.Div([
            html.Div("vs", className="modal-vs"),
            html.Div(fmt_date(detail.get("utcDate", "")), className="modal-kickoff-time"),
        ], className="modal-score-block")

    # H2H aggregates
    agg      = h2h.get("aggregates", {})
    n_played = agg.get("numberOfMatches", 0)
    h2h_section = html.Span()
    if n_played:
        hw = agg.get("homeTeam", {}).get("wins", 0)
        dr = agg.get("homeTeam", {}).get("draws", 0)
        aw = agg.get("awayTeam", {}).get("wins", 0)
        total_goals = agg.get("totalGoals", 0)
        denom = max(hw + dr + aw, 1)

        h2h_section = html.Div([
            html.Div("Head-to-Head", className="modal-section-label"),
            html.Div([
                html.Div([html.Div(str(hw), className="h2h-num home"), html.Div(home.get("shortName","Home")[:10], className="h2h-team-name")], className="h2h-col"),
                html.Div([html.Div(str(dr), className="h2h-num draw"), html.Div("Draws", className="h2h-team-name")], className="h2h-col"),
                html.Div([html.Div(str(aw), className="h2h-num away"), html.Div(away.get("shortName","Away")[:10], className="h2h-team-name")], className="h2h-col"),
            ], className="h2h-row"),
            html.Div([
                html.Div(className="h2h-seg h2h-home", style={"flex": str(hw / denom)}),
                html.Div(className="h2h-seg h2h-draw", style={"flex": str(dr / denom)}),
                html.Div(className="h2h-seg h2h-away", style={"flex": str(aw / denom)}),
            ], className="h2h-bar"),
            html.Div(f"{n_played} meetings  ·  {total_goals} total goals", className="h2h-meta"),
        ], className="modal-h2h")

    # Referee
    ref_section = html.Span()
    if referees:
        ref = referees[0]
        ref_section = html.Div([
            html.Div("Referee", className="modal-section-label"),
            html.Div([
                html.Span("🟡 "),
                html.Span(ref.get("name", ""), className="ref-name"),
                html.Span(f"  ·  {ref.get('nationality', '')}", className="ref-nat"),
            ], className="ref-row"),
        ], className="modal-ref")

    header = dbc.ModalHeader(
        html.Div([
            dbc.Badge(group_label, color="secondary", className="me-2"),
            dbc.Badge(f"MD {matchday}", color="dark", className="me-2") if matchday else html.Span(),
            status_badge(status),
            html.Span(
                [html.Span("⚡", className="me-1"), "Auto-refreshing"],
                className="modal-live-refresh ms-2",
            ) if is_live else html.Span(),
        ]),
        close_button=True,
        className="modal-header-custom",
    )

    body = dbc.ModalBody(
        html.Div([
            # Teams + score
            html.Div([
                crest_name(home),
                score_block,
                crest_name(away, reverse=True),
            ], className="modal-score-row"),
            html.Hr(className="modal-divider"),
            # Stats
            html.Div([h2h_section, ref_section], className="modal-stats-area"),
        ]),
        className="modal-body-custom",
    )

    return [header, body]


# ── Layout ─────────────────────────────────────────────────────────────────────

app.layout = html.Div(
    [
        dcc.Location(id="url"),
        dcc.Interval(id="refresh", interval=3 * 60 * 1000, n_intervals=0),
        dcc.Interval(id="live-interval", interval=20_000, n_intervals=0),
        dcc.Store(id="selected-match-id"),
        dcc.Store(id="theme-store", storage_type="local", data="dark"),
        html.Div(
            [
                html.Div(id="header-area"),
                html.Button(
                    "☀️",
                    id="theme-toggle-btn",
                    className="theme-toggle-btn",
                    n_clicks=0,
                    title="Toggle light / dark theme",
                ),
            ],
            style={"position": "relative"},
        ),
        dbc.Container(
            [
                html.Div(
                    [
                        dbc.Nav(
                            [
                                dbc.NavLink("⚽  Groups",      href="/groups",  active="exact"),
                                dbc.NavLink("👟  Golden Boot", href="/scorers", active="exact"),
                                dbc.NavLink("📅  Matches",     href="/matches", active="exact"),
                                dbc.NavLink("🏆  Bracket",     href="/bracket", active="exact"),
                            ],
                            className="main-tabs",
                        ),
                        html.Div(
                            [
                                html.A(
                                    html.Img(src="/assets/github.svg", style={"height": "18px", "width": "18px"}),
                                    href="https://github.com/budescode/wc2026-dashboard",
                                    target="_blank",
                                    className="social-link",
                                    title="GitHub",
                                ),
                                html.A(
                                    html.Img(src="/assets/linkedin.svg", style={"height": "18px", "width": "18px"}),
                                    href="https://www.linkedin.com/in/budescode",
                                    target="_blank",
                                    className="social-link",
                                    title="LinkedIn",
                                ),
                            ],
                            className="social-links",
                        ),
                    ],
                    className="tabs-bar",
                ),
                html.Div(id="tab-content", className="py-4"),
            ],
            fluid=True,
            className="main-content",
        ),
        dbc.Modal(
            id="match-modal",
            is_open=False,
            size="lg",
            centered=True,
            className="match-detail-modal",
        ),
        html.Footer(
            dbc.Container(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("🏆", className="footer-trophy"),
                                    html.Span("FIFA World Cup 2026", className="footer-brand"),
                                ],
                                className="footer-left",
                            ),
                            html.Div(
                                [
                                    html.Span("Built by ", className="footer-by"),
                                    html.A("budescode", href="https://www.linkedin.com/in/budescode", target="_blank", className="footer-author"),
                                    html.Span(" · ", className="footer-sep"),
                                    html.Span("Powered by ", className="footer-by"),
                                    html.A("football-data.org", href="https://www.football-data.org", target="_blank", className="footer-link"),
                                    html.Span(" · ", className="footer-sep"),
                                    html.A("Dash Plotly", href="https://dash.plotly.com", target="_blank", className="footer-link"),
                                ],
                                className="footer-center",
                            ),
                            html.Div(
                                [
                                    html.A(
                                        html.Img(src="/assets/github.svg", style={"height": "16px", "width": "16px"}),
                                        href="https://github.com/budescode/wc2026-dashboard",
                                        target="_blank",
                                        className="footer-icon-link",
                                        title="GitHub",
                                    ),
                                    html.A(
                                        html.Img(src="/assets/linkedin.svg", style={"height": "16px", "width": "16px"}),
                                        href="https://www.linkedin.com/in/budescode",
                                        target="_blank",
                                        className="footer-icon-link",
                                        title="LinkedIn",
                                    ),
                                ],
                                className="footer-right",
                            ),
                        ],
                        className="footer-inner",
                    ),
                ],
                fluid=True,
            ),
            className="wc-footer",
        ),
    ]
)


# ── Theme Callbacks ────────────────────────────────────────────────────────────

# Apply theme to <html> element and update button icon
app.clientside_callback(
    """
    function(theme) {
        var t = theme || 'light';
        document.documentElement.setAttribute('data-theme', t);
        return t === 'dark' ? '🌙' : '☀️';
    }
    """,
    Output("theme-toggle-btn", "children"),
    Input("theme-store", "data"),
)


@callback(
    Output("theme-store", "data"),
    Input("theme-toggle-btn", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def toggle_theme(_, current_theme):
    return "dark" if (current_theme or "light") == "light" else "light"


# ── Callbacks ──────────────────────────────────────────────────────────────────

@callback(
    Output("header-area", "children"),
    Input("refresh", "n_intervals"),
    Input("url", "pathname"),
)
def update_header(_, pathname):
    try:
        md = api.get_matches()
    except Exception:
        md = None
    return build_header(md, pathname or "")


@callback(
    Output("tab-content", "children"),
    Input("url", "pathname"),
    Input("refresh", "n_intervals"),
    Input("live-interval", "n_intervals"),
)
def render_tab(pathname, _, __):
    route = (pathname or "/groups").strip("/") or "groups"

    # Only re-render on live-interval when actually on /live
    if ctx.triggered_id == "live-interval" and route != "live":
        return no_update

    if route == "groups":
        return render_groups()
    if route == "scorers":
        return render_scorers()
    if route == "matches":
        return render_matches()
    if route == "bracket":
        return render_bracket()
    if route == "teams":
        return pg_teams.layout()
    if route == "fixtures":
        return pg_fixtures.layout()
    if route == "played":
        return pg_played.layout()
    if route == "goals":
        return pg_goals.layout()
    if route == "live":
        return pg_live.layout()
    return render_groups()


# Open modal + store match id when any card is clicked
@callback(
    Output("selected-match-id", "data"),
    Output("match-modal", "is_open"),
    Input({"type": "match-click", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_match_modal(n_clicks_list):
    if not ctx.triggered_id or not any(n for n in n_clicks_list if n):
        return no_update, no_update
    return ctx.triggered_id["index"], True


# Populate modal content — refreshes every 20s when a live match is selected
@callback(
    Output("match-modal", "children"),
    Input("selected-match-id", "data"),
    Input("live-interval", "n_intervals"),
    State("match-modal", "is_open"),
    prevent_initial_call=True,
)
def update_modal(match_id, _, is_open):
    if not match_id or not is_open:
        return no_update
    try:
        detail = api.get_match(match_id)
        h2h    = api.get_head2head(match_id)
    except Exception as e:
        return [dbc.ModalHeader(close_button=True), dbc.ModalBody(error_card(str(e)))]
    return build_modal_content(detail, h2h)


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=8052)
