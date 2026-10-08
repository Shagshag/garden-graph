"""Fetch the GitHub contribution calendar and write it to data/contributions.json."""
import json
import os
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

LOGIN = os.environ.get("GITHUB_LOGIN", "Shagshag")
OUT = Path(__file__).parent / "data" / "contributions.json"

YEARS = int(os.environ.get("GARDEN_YEARS", "5"))  # number of calendar years to fetch, the current one included


def build_query(years):
    """One query with one aliased field per year: contributionsCollection is limited to 12 months."""
    fields = "".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") {{'
        "contributionCalendar { weeks { contributionDays { date contributionCount } } } } "
        for y in years
    )
    return "query($login: String!) { user(login: $login) { " + fields + "} }"


def get_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    # Locally, reuse the gh CLI session.
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("No token: set GITHUB_TOKEN or sign in with `gh auth login`.")


def main():
    years = list(range(date.today().year - YEARS + 1, date.today().year + 1))
    body = json.dumps({"query": build_query(years), "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {get_token()}", "User-Agent": "solargraph"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.load(resp)
        user = payload["data"]["user"]
    except Exception as exc:  # API down: keep the previous data
        print(f"Fetch failed ({exc}), keeping the previous data.")
        return

    counts = {}  # dedupe: a week spanning two years appears in both
    for y in years:
        for week in user[f"y{y}"]["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                if d["date"].startswith(str(y)) and d["date"] <= date.today().isoformat():
                    counts[d["date"]] = d["contributionCount"]
    days = [{"date": k, "count": v} for k, v in sorted(counts.items())]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps({"login": LOGIN, "years": years, "total": sum(counts.values()), "days": days}, indent=1),
        encoding="utf-8",
    )
    print(f"{len(days)} days, {sum(counts.values())} contributions over {len(years)} years.")


if __name__ == "__main__":
    main()
