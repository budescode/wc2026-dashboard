import dash_bootstrap_components as dbc
from dash import dcc, html

PAGES = [
    {
        "href": "/groups",
        "icon": "⚽",
        "title": "Group Standings",
        "desc": (
            "Live standings for all 12 groups. Tracks games played, wins, draws, losses, "
            "goals for/against, goal difference, points, and 5-match form. "
            "Top 2 from each group advance to the knockout rounds."
        ),
        "badge": "Live data",
        "badge_color": "success",
    },
    {
        "href": "/scorers",
        "icon": "👟",
        "title": "Golden Boot Race",
        "desc": (
            "Top scorers ranked by goals, with assist counts, goal involvements (GI), "
            "penalties scored, and matches played. Includes an interactive bar chart "
            "and a full leaderboard with group-by-group scoring stats."
        ),
        "badge": "Stats",
        "badge_color": "warning",
    },
    {
        "href": "/matches",
        "icon": "📅",
        "title": "Match Browser",
        "desc": (
            "All 104 fixtures organised by date. Click any match card to open a detail "
            "modal with full-time and half-time scores, head-to-head history chart, "
            "and referee info. Live matches auto-refresh every 20 seconds inside the modal."
        ),
        "badge": "Interactive",
        "badge_color": "primary",
    },
    {
        "href": "/bracket",
        "icon": "🏆",
        "title": "Knockout Bracket",
        "desc": (
            "Round-by-round knockout bracket that appears once the Group Stage concludes. "
            "Each stage (Round of 32, Last 16, Quarters, Semis, Final) is collapsible. "
            "Completed stages fold automatically; in-progress stages stay open."
        ),
        "badge": "Knockout",
        "badge_color": "secondary",
    },
    {
        "href": "/predictions",
        "icon": "🔮",
        "title": "Predictions & Power Rankings",
        "desc": (
            "Elo-based power rankings computed from all World Cup match results. "
            "Monte Carlo simulation (400 runs per group) gives each team a group-stage "
            "qualification probability. Championship probabilities and upcoming-match "
            "win/draw/lose predictions are shown for every scheduled fixture."
        ),
        "badge": "AI / Elo",
        "badge_color": "info",
    },
    {
        "href": "/teams",
        "icon": "🌍",
        "title": "Teams & Squads",
        "desc": (
            "Explore all 48 competing nations. Search by team name to see the full squad "
            "organised by position (GK / DEF / MID / FWD), coach, venue, club colours, "
            "and group-stage stats. Use the nav player search to jump directly to a "
            "specific player and see their tournament stats card."
        ),
        "badge": "Player search",
        "badge_color": "warning",
    },
    {
        "href": "/fixtures",
        "icon": "🗓️",
        "title": "Full Fixture List",
        "desc": (
            "Complete schedule of all 104 matches with kickoff times (UTC), venue, "
            "group or stage label, and current status. Filter by date or browse the "
            "full tournament calendar from the Group Stage through to the Final."
        ),
        "badge": "Schedule",
        "badge_color": "secondary",
    },
    {
        "href": "/played",
        "icon": "✅",
        "title": "Results & Played Stats",
        "desc": (
            "All finished matches with full-time scores, win/draw/loss indicators, "
            "and a tournament-wide summary: total matches played, goals scored, "
            "clean sheets, and average goals per game."
        ),
        "badge": "Results",
        "badge_color": "secondary",
    },
    {
        "href": "/goals",
        "icon": "📊",
        "title": "Goals & Charts",
        "desc": (
            "Interactive scoring charts: a horizontal bar chart of the top scorers, "
            "a dual-axis group goals chart (total goals vs. goals-per-match), "
            "and the Golden Boot leaderboard with Goals, Assists, GI, and Penalties."
        ),
        "badge": "Charts",
        "badge_color": "primary",
    },
    {
        "href": "/live",
        "icon": "⚡",
        "title": "Live Match View",
        "desc": (
            "Dedicated live view that auto-refreshes every 20 seconds. Shows all "
            "currently active matches with real-time scores. When no matches are live "
            "it displays the next upcoming fixtures."
        ),
        "badge": "Live",
        "badge_color": "danger",
    },
]

TECH = [
    ("Dash 4.2", "https://dash.plotly.com/", "Python web framework for data apps"),
    ("Dash Bootstrap Components 2", "https://dash-bootstrap-components.opensource.faculty.ai/", "Bootstrap UI components for Dash"),
    ("Plotly 6", "https://plotly.com/python/", "Interactive chart library"),
    ("football-data.org API v4", "https://www.football-data.org/", "Live World Cup match and squad data"),
    ("Python 3.11", "https://www.python.org/", "Backend language"),
]


def _page_card(page: dict) -> dbc.Col:
    return dbc.Col(
        dcc.Link(
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(page["icon"], className="about-page-icon"),
                            dbc.Badge(
                                page["badge"],
                                color=page["badge_color"],
                                className="about-page-badge ms-2",
                            ),
                        ],
                        className="about-page-card-top",
                    ),
                    html.H5(page["title"], className="about-page-title"),
                    html.P(page["desc"], className="about-page-desc"),
                    html.Span(
                        [html.Span("Go to page"), html.Span(" →", className="about-arrow")],
                        className="about-page-link-label",
                    ),
                ],
                className="about-page-card",
            ),
            href=page["href"],
            style={"textDecoration": "none"},
        ),
        lg=6, md=12, className="mb-4",
    )


def layout() -> html.Div:
    page_cols = [_page_card(p) for p in PAGES]
    rows = []
    for i in range(0, len(page_cols), 2):
        rows.append(dbc.Row(page_cols[i : i + 2], className="g-4"))

    tech_items = [
        html.Div(
            [
                html.A(name, href=url, target="_blank", className="about-tech-name"),
                html.Span(f" — {desc}", className="about-tech-desc"),
            ],
            className="about-tech-item",
        )
        for name, url, desc in TECH
    ]

    return html.Div(
        [
            # ── Hero ─────────────────────────────────────────────────────────────
            html.Div(
                [
                    html.H2("About This Dashboard", className="page-title"),
                    html.P(
                        "A real-time FIFA World Cup 2026 companion, built for fans and analysts.",
                        className="page-subtitle",
                    ),
                ],
                className="page-hero",
            ),

            # ── What is it ────────────────────────────────────────────────────────
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("What is this?", className="about-section-title"),
                            html.P(
                                [
                                    "The ",
                                    html.Strong("FIFA World Cup 2026 Dashboard"),
                                    " is a live data app built with Dash Plotly that tracks every "
                                    "match, team, and player across the 2026 tournament — hosted across "
                                    "the United States, Canada, and Mexico.",
                                ],
                                className="about-body-text",
                            ),
                            html.P(
                                "Match data, standings, squads, and scorer stats are pulled from the "
                                "football-data.org API and cached for 3 minutes so the app stays "
                                "responsive without hammering rate limits. Live matches refresh every "
                                "20 seconds automatically.",
                                className="about-body-text",
                            ),
                            html.P(
                                [
                                    "Built as an entry for the ",
                                    html.Strong("Plotly Dash App Challenge"),
                                    " by ",
                                    html.A(
                                        "budescode",
                                        href="https://www.linkedin.com/in/budescode",
                                        target="_blank",
                                        className="about-inline-link",
                                    ),
                                    ".",
                                ],
                                className="about-body-text mb-0",
                            ),
                        ],
                        className="about-what-card",
                    ),
                ],
                className="mb-4",
            ),

            # ── Pages ─────────────────────────────────────────────────────────────
            html.Div("Explore the Dashboard", className="modal-section-label mb-3"),
            html.Div(rows, className="mb-5"),

            # ── Tech Stack ────────────────────────────────────────────────────────
            html.Div(
                [
                    html.H4("Tech Stack", className="about-section-title"),
                    html.Div(tech_items, className="about-tech-list"),
                ],
                className="about-what-card mb-4",
            ),

            # ── Source & Data ─────────────────────────────────────────────────────
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("📦 ", style={"fontSize": "1.1rem"}),
                            html.Span("Source code — ", className="about-tech-desc"),
                            html.A(
                                "github.com/budescode/wc2026-dashboard",
                                href="https://github.com/budescode/wc2026-dashboard",
                                target="_blank",
                                className="about-inline-link",
                            ),
                        ],
                        className="about-source-row",
                    ),
                    html.Div(
                        [
                            html.Span("📡 ", style={"fontSize": "1.1rem"}),
                            html.Span("Live data — ", className="about-tech-desc"),
                            html.A(
                                "football-data.org",
                                href="https://www.football-data.org/",
                                target="_blank",
                                className="about-inline-link",
                            ),
                            html.Span(
                                "  (free tier API key required to self-host)",
                                className="about-tech-desc",
                            ),
                        ],
                        className="about-source-row",
                    ),
                ],
                className="about-what-card",
            ),
        ]
    )
