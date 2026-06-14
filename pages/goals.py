import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

import api

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#64748b"),
    margin=dict(l=0, r=16, t=8, b=8),
    showlegend=False,
    xaxis=dict(showgrid=True, gridcolor="rgba(100,116,139,0.12)", zeroline=False, tickfont=dict(color="#64748b")),
    yaxis=dict(showgrid=False, tickfont=dict(color="#475569", size=12)),
)


def _scorers_chart(scorers: list) -> dcc.Graph:
    if not scorers:
        return html.Div()

    names  = [s.get("player", {}).get("name", "?") for s in scorers]
    goals  = [s.get("goals", 0) or 0 for s in scorers]
    crests = [s.get("team", {}).get("crest", "") for s in scorers]
    teams  = [s.get("team", {}).get("name", "") for s in scorers]

    # Color bars gold → amber
    max_g  = max(goals) if goals else 1
    colors = [f"rgba(240,192,48,{0.4 + 0.6 * (g / max_g)})" for g in goals]

    fig = go.Figure(
        go.Bar(
            x=goals,
            y=names,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[str(g) for g in goals],
            textposition="outside",
            textfont=dict(color="#f0c030", size=13, family="Rajdhani"),
            hovertemplate="<b>%{y}</b><br>Goals: %{x}<extra></extra>",
            customdata=teams,
        )
    )
    layout = dict(CHART_LAYOUT)
    layout["yaxis"] = dict(autorange="reversed", showgrid=False, tickfont=dict(color="#475569", size=12))
    layout["height"] = max(300, len(scorers) * 38)
    fig.update_layout(**layout)
    return dcc.Graph(figure=fig, config={"displayModeBar": False}, className="goals-chart")


def _group_goals_chart(standings: list) -> dcc.Graph:
    group_data = []
    for s in standings:
        group = s.get("group", "")
        letter = group.split()[-1] if group else "?"
        table = s.get("table", [])
        total_gf = sum(e.get("goalsFor", 0) for e in table)
        played   = sum(e.get("playedGames", 0) for e in table) // 2  # each match counted twice
        gpg = round(total_gf / played, 2) if played else 0
        group_data.append((letter, total_gf, gpg, played))

    group_data.sort(key=lambda x: x[1], reverse=True)
    labels  = [f"Group {d[0]}" for d in group_data]
    totals  = [d[1] for d in group_data]
    gpg_vals = [d[2] for d in group_data]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=totals,
        name="Total Goals",
        marker=dict(color="rgba(240,192,48,0.7)", line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Total: %{y} goals<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=gpg_vals,
        name="Goals/Match",
        mode="lines+markers",
        yaxis="y2",
        line=dict(color="#60a5fa", width=2),
        marker=dict(size=7, color="#60a5fa"),
        hovertemplate="<b>%{x}</b><br>Per match: %{y:.2f}<extra></extra>",
    ))
    layout2 = dict(CHART_LAYOUT)
    layout2.update(
        height=280,
        yaxis=dict(showgrid=True, gridcolor="rgba(100,116,139,0.12)", tickfont=dict(color="#b8880e")),
        yaxis2=dict(overlaying="y", side="right", showgrid=False, tickfont=dict(color="#3b82f6")),
        legend=dict(orientation="h", x=0, y=1.1, font=dict(color="#64748b", size=11)),
        showlegend=True,
        barmode="group",
    )
    fig.update_layout(**layout2)
    return dcc.Graph(figure=fig, config={"displayModeBar": False}, className="goals-chart")


def layout() -> html.Div:
    try:
        scorers_data   = api.get_scorers(limit=20)
        standings_data = api.get_standings()
        matches_data   = api.get_matches()
    except Exception as e:
        return dbc.Alert(str(e), color="warning", className="m-4")

    scorers   = scorers_data.get("scorers", [])
    standings = [s for s in standings_data.get("standings", []) if s.get("type") == "TOTAL"]
    matches   = matches_data.get("matches", [])

    played    = [m for m in matches if m.get("status") == "FINISHED"]
    total_goals = sum(
        (m.get("score", {}).get("fullTime", {}).get("home") or 0) +
        (m.get("score", {}).get("fullTime", {}).get("away") or 0)
        for m in played
    )
    avg_goals = round(total_goals / len(played), 2) if played else 0
    max_goals = scorers[0].get("goals", 0) if scorers else 0

    def stat(val, lbl, color="#f0c030"):
        return html.Div(
            [html.Div(str(val), className="played-stat-num", style={"color": color}),
             html.Div(lbl, className="played-stat-lbl")],
            className="played-stat-card",
        )

    stats_row = html.Div(
        [
            stat(total_goals,            "Total Goals"),
            stat(len(played),            "Matches Played",      "#8899aa"),
            stat(avg_goals,              "Goals / Match",       "#60a5fa"),
            stat(max_goals,              "Top Scorer Goals",    "#22c55e"),
        ],
        className="played-stats-row",
    )

    return html.Div(
        [
            html.Div(
                [html.H2("Goals & Scorers", className="page-title"),
                 html.P("Tournament scoring statistics", className="page-subtitle")],
                className="page-hero",
            ),
            stats_row,
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [html.H5("Top Scorers", className="chart-title"), _scorers_chart(scorers)],
                            className="chart-card",
                        ),
                        lg=7,
                    ),
                    dbc.Col(
                        html.Div(
                            [html.H5("Goals by Group", className="chart-title"), _group_goals_chart(standings)],
                            className="chart-card",
                        ),
                        lg=5,
                    ),
                ],
                className="g-4 mt-1",
            ),
            html.Div(
                [
                    html.H5("Golden Boot Leaderboard", className="chart-title mb-3"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else str(i + 1),
                                        className="scorer-rank",
                                    ),
                                    html.Img(src=s.get("team", {}).get("crest",""), className="crest-sm")
                                    if s.get("team", {}).get("crest") else html.Span(),
                                    html.Span(s.get("player", {}).get("name", "?"), className="scorer-name me-2"),
                                    html.Span(s.get("team", {}).get("name", ""), className="scorer-team-name me-3"),
                                    dbc.Badge(f"{s.get('goals',0)} G", color="warning", text_color="dark", className="me-1"),
                                    dbc.Badge(f"{s.get('assists',0) or 0} A", color="primary", className="me-1"),
                                ],
                                className="leaderboard-row" + (" lb-leader" if i == 0 else ""),
                            )
                            for i, s in enumerate(scorers[:10])
                        ],
                        className="leaderboard-list",
                    ),
                ],
                className="chart-card mt-4",
            ),
        ]
    )
