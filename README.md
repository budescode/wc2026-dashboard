# 🏆 FIFA World Cup 2026 Live Dashboard

A real-time World Cup 2026 dashboard built with Dash Plotly and Dash Bootstrap Components, powered by the [football-data.org](https://www.football-data.org/) API.

## Features

- **Live match tracking** — auto-refreshes every 20 seconds during active matches
- **Group standings** — all 12 groups with form, goal difference, and advancement indicators
- **Golden Boot race** — top scorers leaderboard with goal bars and assist counts
- **Match browser** — all 104 fixtures grouped by date with clickable detail modals
- **Match detail modal** — click any match card for full-time score, half-time score, head-to-head record, and referee info; live matches auto-refresh every 20 seconds
- **Knockout bracket** — displays once the group stage concludes
- **Teams** — full squad rosters organised by position with group standings
- **Fixtures** — complete schedule with kickoff times
- **Played matches** — results, stats, and W/D/L breakdown
- **Goals & Charts** — scoring charts by player and by group
- **Light / Dark theme** — toggle with preference saved across sessions
- **Social links** — GitHub and LinkedIn in the navbar and footer

## Tech Stack

- [Dash 4.2](https://dash.plotly.com/) + [Dash Bootstrap Components 2.0](https://dash-bootstrap-components.opensource.faculty.ai/)
- [Plotly 6](https://plotly.com/python/)
- [football-data.org API v4](https://www.football-data.org/documentation/quickstart)
- Python 3.11

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/budescode/wc2026-dashboard.git
   cd wc2026-dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your API key**

   Create a `.env` file in the project root:
   ```
   API_KEY=your_football_data_api_key
   ```
   Get a free key at [football-data.org](https://www.football-data.org/).

4. **Run the app**
   ```bash
   python app.py
   ```
   Open [http://localhost:8052](http://localhost:8052) in your browser.

## Project Structure

```
├── app.py              # Main app, layout, and callbacks
├── api.py              # football-data.org API client with TTL cache
├── pages/
│   ├── teams.py        # Teams & squads page
│   ├── fixtures.py     # Full fixture list
│   ├── played.py       # Completed results & stats
│   ├── goals.py        # Scoring charts & leaderboard
│   └── live.py         # Live match view
├── assets/
│   ├── custom.css      # CSS variables, light/dark theme, all custom styles
│   ├── github.svg      # GitHub icon
│   └── linkedin.svg    # LinkedIn icon
├── requirements.txt
└── .env                # API key (not committed)
```

## Live Data

Data is fetched from the football-data.org free tier and cached in memory for 3 minutes to respect rate limits. Live matches additionally refresh the modal detail view every 20 seconds.
