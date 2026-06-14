import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
BASE_URL = "https://api.football-data.org/v4"
WC = "WC"

_cache: dict = {}
CACHE_TTL = 180  # 3 minutes


def _get(endpoint: str, params: dict = None) -> dict:
    key = f"{endpoint}|{params}"
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < CACHE_TTL:
        return _cache[key]["data"]

    r = requests.get(
        f"{BASE_URL}{endpoint}",
        headers={"X-Auth-Token": API_KEY},
        params=params or {},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    _cache[key] = {"data": data, "ts": now}
    return data


def get_competition() -> dict:
    return _get(f"/competitions/{WC}")


def get_standings() -> dict:
    return _get(f"/competitions/{WC}/standings")


def get_matches(status: str = None, stage: str = None) -> dict:
    params = {}
    if status:
        params["status"] = status
    if stage:
        params["stage"] = stage
    return _get(f"/competitions/{WC}/matches", params or None)


def get_scorers(limit: int = 30) -> dict:
    return _get(f"/competitions/{WC}/scorers", {"limit": limit})


def get_teams() -> dict:
    return _get(f"/competitions/{WC}/teams")


def get_match(match_id: int) -> dict:
    return _get(f"/matches/{match_id}")


def get_head2head(match_id: int, limit: int = 10) -> dict:
    return _get(f"/matches/{match_id}/head2head", {"limit": limit})
