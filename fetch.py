"""Récupère le calendrier de contributions GitHub et l'écrit dans data/contributions.json."""
import json
import os
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

LOGIN = os.environ.get("GITHUB_LOGIN", "Shagshag")
OUT = Path(__file__).parent / "data" / "contributions.json"

YEARS = int(os.environ.get("GARDEN_YEARS", "5"))  # nombre d'années calendaires, l'année en cours incluse


def build_query(years):
    """Une requête avec un champ aliasé par année : contributionsCollection est limité à 12 mois."""
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
    # En local, on réutilise la session de la CLI gh.
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("Aucun token : définis GITHUB_TOKEN ou connecte-toi avec `gh auth login`.")


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
    except Exception as exc:  # API en panne : on garde les données précédentes
        print(f"Échec de la récupération ({exc}), données précédentes conservées.")
        return

    counts = {}  # dédoublonnage : une semaine à cheval sur deux années apparaît dans les deux
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
    print(f"{len(days)} jours, {sum(counts.values())} contributions sur {len(years)} ans.")


if __name__ == "__main__":
    main()
