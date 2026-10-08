<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/garden-dark.svg">
    <img alt="Jardin solarpunk généré à partir de mes contributions GitHub" src="assets/garden-light.svg">
  </picture>
</p>

# solargraph

Mon graphe de contributions GitHub, transformé en jardin solarpunk isométrique. Une parcelle par jour, un bloc par année (5 par défaut, `GARDEN_YEARS` pour changer), une saison selon la date.

| Contributions du jour | Plante |
|---|---|
| 0 | terre nue |
| quartile 1 | pousse |
| quartile 2 | fleur (arbuste en hiver) |
| quartile 3 | arbre (sapin en hiver) |
| quartile 4 | éolienne et panneau solaire |

## Utilisation

```bash
python fetch.py   # récupère les contributions des N dernières années (GITHUB_TOKEN ou session `gh`)
python render.py  # écrit assets/garden-light.svg et assets/garden-dark.svg
```

Aucune dépendance, Python 3 suffit. `GITHUB_LOGIN` change le compte lu (par défaut `Shagshag`).

## Climats

`GARDEN_CLIMATE` choisit les saisons du jardin (`temperate-north` par défaut). `GARDEN_HEMISPHERE=north|south` reste accepté comme ancien nom des deux premiers.

| Valeur | Saisons | Pour qui |
|---|---|---|
| `temperate-north` | printemps, été, automne, hiver | Amérique du Nord, Europe, Japon, nord de la Chine |
| `temperate-south` | idem, décalées de six mois | Australie (sud), Nouvelle-Zélande, Argentine, Afrique du Sud, sud du Brésil |
| `monsoon` | saison fraîche (déc. à fév.), chaude (mars à mai), mousson (juin à sept.), après-mousson (oct. et nov.) | Inde, Bangladesh, Sri Lanka, Népal |
| `tropical-south` | pluies (nov. à avril), sèche (mai à oct.) | Brésil central, Indonésie, Afrique australe |
| `tropical-north` | pluies (mai à oct.), sèche (nov. à avril) | Sahel, Amérique centrale, Asie du Sud-Est continentale |

Les mois sont des moyennes : une région précise (côte est de l'Inde, Kerala...) peut avoir ses pluies à d'autres dates.

## Mise en ligne

Pousse ce dépôt sur `Shagshag/Shagshag` pour que le README s'affiche sur ton profil. La GitHub Action `.github/workflows/garden.yml` régénère le jardin chaque jour. Pour inclure les contributions privées, ajoute un secret `GH_STATS_TOKEN` (token avec `read:user`) et active « Private contributions » dans les réglages du profil.
