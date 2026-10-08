"""Récupère le calendrier de contributions GitHub et l'écrit dans data/contributions.json."""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

LOGIN = os.environ.get("GITHUB_LOGIN", "Shagshag")
OUT = Path(__file__).parent / "data" / "contributions.json"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount } }
      }
    }
  }
}
"""


def get_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    # En local, on réutilise la session de la CLI gh.
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("Aucun token : définis GITHUB_TOKEN ou connecte-toi avec `gh auth login`.")


def main():
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {get_token()}", "User-Agent": "solargraph"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
        cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except Exception as exc:  # API en panne : on garde les données précédentes
        print(f"Échec de la récupération ({exc}), données précédentes conservées.")
        return

    days = [
        {"date": d["date"], "weekday": d["weekday"], "count": d["contributionCount"]}
        for week in cal["weeks"]
        for d in week["contributionDays"]
    ]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps({"login": LOGIN, "total": cal["totalContributions"], "days": days}, indent=1),
        encoding="utf-8",
    )
    print(f"{len(days)} jours, {cal['totalContributions']} contributions.")


if __name__ == "__main__":
    main()
