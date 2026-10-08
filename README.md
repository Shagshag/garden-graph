<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/garden-dark.svg">
    <img alt="Solarpunk garden generated from a GitHub contribution graph" src="assets/garden-light.svg">
  </picture>
</p>

# solargraph

[English](#english) · [Français](#français)

## English

Your GitHub contribution graph, turned into an isometric solarpunk garden. One tile per day, one block per year (5 by default, `GARDEN_YEARS` to change it), and the season follows the date. A small gardener strolls around today's tile.

| Contributions that day | Plant |
|---|---|
| 0 | bare soil |
| quartile 1 | sprout |
| quartile 2 | flower (shrub in winter) |
| quartile 3 | tree (fir in winter) |
| quartile 4 | wind turbine and solar panel |

Days that have not happened yet are packed earth. The output is plain SVG with CSS and SMIL animations, so it works in a GitHub profile README: a light and a dark version, picked with `<picture>`. No dependencies, Python 3 is enough.

### Quick start

1. Copy this repository (fork it, or create `<your-login>/<your-login>` to get a profile README) and enable GitHub Actions.
2. In [`.github/workflows/garden.yml`](.github/workflows/garden.yml), set `GITHUB_LOGIN` to your username and pick your climate and language (see below).
3. Run the **Update garden** workflow once from the Actions tab. It then refreshes the garden every day and commits only when something changed.

To run it locally:

```bash
GITHUB_LOGIN=your-login python fetch.py   # fetch contributions (GITHUB_TOKEN, or your `gh` session)
GITHUB_LOGIN=your-login python render.py  # write assets/garden-light.svg and assets/garden-dark.svg
```

`GITHUB_LOGIN` defaults to `Shagshag`, so set it. To also count private contributions, add a secret `GH_STATS_TOKEN` (a token with `read:user`) and enable "Private contributions" in your profile settings.

### Settings

All settings are environment variables.

| Variable | Default | Meaning |
|---|---|---|
| `GITHUB_LOGIN` | `Shagshag` | whose contributions to read |
| `GARDEN_YEARS` | `5` | number of calendar years, the current one included |
| `GARDEN_CLIMATE` | `temperate-north` | which seasons the garden follows |
| `GARDEN_LANG` | `fr` | language of the texts: `fr`, `en`, `ja`, `hi` |

### Climates

`GARDEN_HEMISPHERE=north|south` is still accepted as the old name of the first two.

| Value | Seasons | For |
|---|---|---|
| `temperate-north` | spring, summer, autumn, winter | North America, Europe, Japan, northern China |
| `temperate-south` | same, shifted by six months | southern Australia, New Zealand, Argentina, South Africa, southern Brazil |
| `monsoon` | cool (Dec-Feb), hot (Mar-May), monsoon (Jun-Sep), post-monsoon (Oct-Nov) | India, Bangladesh, Sri Lanka, Nepal |
| `tropical-south` | wet (Nov-Apr), dry (May-Oct) | central Brazil, Indonesia, southern Africa |
| `tropical-north` | wet (May-Oct), dry (Nov-Apr) | the Sahel, Central America, mainland Southeast Asia |
| `china-southeast` | mild winter (Dec-Feb), spring rains (Mar-May), humid summer and typhoons (Jun-Sep), clear autumn (Oct-Nov) | Guangdong, Fujian, Hong Kong, Shenzhen |
| `japan` | sakura (Mar-Apr), spring (May), tsuyu (Jun to mid-Jul), summer, autumn (from mid-Sep), winter | Honshu: Tokyo, Kyoto, Osaka |

Months are averages (in Japan, July and September are split at the 15th). A specific region (the east coast of India, Kerala...) can have its rains at other dates. Adding a climate means one entry in `CLIMATES` and one per new season in `PALETTE`, both in [render.py](render.py).

### Languages

`GARDEN_LANG` picks the language of the title, subtitle, legend and date label. Sentences are full templates with placeholders (`{login}`, `{total}`, `{first}`, `{last}`...), not words glued together, in [i18n.py](i18n.py). Numbers follow local usage ("3 677", "3,677", and the Indian grouping "12,34,567" in Hindi). To add a language, copy an entry of `STRINGS` and translate it. Japanese and Hindi texts have not been reviewed by a native speaker, corrections are welcome.

Fonts are not embedded in the SVG, so Japanese and Hindi need a matching font on the viewer's machine.

## Français

Votre graphe de contributions GitHub, transformé en jardin solarpunk isométrique. Une parcelle par jour, un bloc par année (5 par défaut, `GARDEN_YEARS` pour changer), une saison selon la date. Un petit jardinier se promène autour de la parcelle du jour.

| Contributions du jour | Plante |
|---|---|
| 0 | terre nue |
| quartile 1 | pousse |
| quartile 2 | fleur (arbuste en hiver) |
| quartile 3 | arbre (sapin en hiver) |
| quartile 4 | éolienne et panneau solaire |

Les jours à venir sont en terre battue. Le résultat est un SVG avec animations CSS et SMIL, qui s'affiche dans le README d'un profil GitHub, en version claire et sombre via `<picture>`. Aucune dépendance, Python 3 suffit.

### Démarrage rapide

1. Copiez ce dépôt (fork, ou création de `<votre-login>/<votre-login>` pour avoir un README de profil) et activez GitHub Actions.
2. Dans [`.github/workflows/garden.yml`](.github/workflows/garden.yml), mettez votre nom d'utilisateur dans `GITHUB_LOGIN` et choisissez votre climat et votre langue (voir plus bas).
3. Lancez une fois le workflow **Update garden** depuis l'onglet Actions. Il met ensuite le jardin à jour chaque jour et ne committe que si quelque chose a changé.

En local :

```bash
GITHUB_LOGIN=votre-login python fetch.py   # récupère les contributions (GITHUB_TOKEN, ou la session `gh`)
GITHUB_LOGIN=votre-login python render.py  # écrit assets/garden-light.svg et assets/garden-dark.svg
```

`GITHUB_LOGIN` vaut `Shagshag` par défaut : pensez à le régler. Pour compter aussi les contributions privées, ajoutez un secret `GH_STATS_TOKEN` (token avec `read:user`) et activez « Private contributions » dans les réglages du profil.

### Réglages

Tous les réglages sont des variables d'environnement.

| Variable | Défaut | Rôle |
|---|---|---|
| `GITHUB_LOGIN` | `Shagshag` | le compte dont on lit les contributions |
| `GARDEN_YEARS` | `5` | nombre d'années calendaires, l'année en cours incluse |
| `GARDEN_CLIMATE` | `temperate-north` | les saisons que suit le jardin |
| `GARDEN_LANG` | `fr` | langue des textes : `fr`, `en`, `ja`, `hi` |

### Climats

`GARDEN_HEMISPHERE=north|south` reste accepté comme ancien nom des deux premiers.

| Valeur | Saisons | Pour qui |
|---|---|---|
| `temperate-north` | printemps, été, automne, hiver | Amérique du Nord, Europe, Japon, nord de la Chine |
| `temperate-south` | idem, décalées de six mois | Australie (sud), Nouvelle-Zélande, Argentine, Afrique du Sud, sud du Brésil |
| `monsoon` | saison fraîche (déc. à fév.), chaude (mars à mai), mousson (juin à sept.), après-mousson (oct. et nov.) | Inde, Bangladesh, Sri Lanka, Népal |
| `tropical-south` | pluies (nov. à avril), sèche (mai à oct.) | Brésil central, Indonésie, Afrique australe |
| `tropical-north` | pluies (mai à oct.), sèche (nov. à avril) | Sahel, Amérique centrale, Asie du Sud-Est continentale |
| `china-southeast` | hiver doux (déc. à fév.), pluies de printemps (mars à mai), été humide et typhons (juin à sept.), automne clair (oct. et nov.) | Guangdong, Fujian, Hong Kong, Shenzhen |
| `japan` | sakura (mars et avril), printemps (mai), tsuyu (juin à mi-juillet), été, automne (dès la mi-septembre), hiver | Honshu : Tokyo, Kyoto, Osaka |

Les mois sont des moyennes (au Japon, juillet et septembre sont coupés au 15) : une région précise (côte est de l'Inde, Kerala...) peut avoir ses pluies à d'autres dates. Ajouter un climat, c'est une entrée dans `CLIMATES` et une par nouvelle saison dans `PALETTE`, toutes deux dans [render.py](render.py).

### Langues

`GARDEN_LANG` choisit la langue du titre, du sous-titre, de la légende et de la date. Les phrases sont des modèles complets avec des zones de remplacement (`{login}`, `{total}`, `{first}`, `{last}`...), pas des mots assemblés, dans [i18n.py](i18n.py). Les nombres suivent l'usage local (« 3 677 », « 3,677 », et le groupement indien « 12,34,567 » en hindi). Pour ajouter une langue, copiez une entrée de `STRINGS` et traduisez-la. Les textes japonais et hindi n'ont pas été relus par un locuteur natif, les corrections sont les bienvenues.

Les polices ne sont pas embarquées dans le SVG : le japonais et l'hindi demandent une police adaptée sur la machine du visiteur.
