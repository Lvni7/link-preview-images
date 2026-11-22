# link-preview-images

**Une image de partage pour chaque page de ton site, l'image que les gens voient quand ton lien est partagé, puis la vérification que chaque aperçu fonctionne.**
Un [Agent Skill](https://agentskills.io) pour Claude Code, Codex, Cursor et tout agent IA qui lit les `SKILL.md`, et un script Python que tu peux aussi lancer toi-même.

🇬🇧 [Read in English](README.md)

![Quatre images de partage générées par link-preview-images pour un site d'exemple : deux en thème dégradé, une sombre, une claire](assets/cards.png)

Quand quelqu'un partage un lien sur LinkedIn, X, WhatsApp, Slack ou iMessage, l'app affiche une carte d'aperçu : une image, un titre, une description. L'image vient de la balise `og:image` de la page (Open Graph). La plupart des sites n'en ont pas, donc le lien s'affiche nu, ou ils réutilisent le même logo sur toutes les pages.

**Ce skill règle ça d'un coup.** Ton agent lit le site (pages, titres, couleurs, logo, police), et le script dessine une image 1200×630 par page, aux couleurs de ta marque. L'agent branche ensuite les images dans le site et vérifie les balises de chaque page.

- **Fait pour se démarquer :** trois thèmes (un dégradé vif construit à partir de ta couleur, sombre, clair), ton symbole en grand en arrière-plan, et un mot clé surligné dans chaque titre.
- **À tes couleurs :** ta couleur, ton logo, ta police. La couleur du texte est choisie pour le contraste, et les titres longs rétrécissent pour tenir en 3 lignes.
- **Vérifié à l'œil :** une planche montre chaque image en grande carte de lien et en petite vignette, pour repérer une carte illisible avant que quelqu'un la partage.
- **Vérifié par le script :** balises manquantes, image en adresse relative, image inaccessible, mauvaise taille, image trop lourde, sur un site construit ou en ligne.
- **Branchement natif :** sur Next.js, les images deviennent des fichiers `opengraph-image.png` et le framework écrit les balises lui-même. Ailleurs, l'agent ajoute les balises.

![La planche d'aperçu : chaque page en grande carte de lien et en petite vignette](assets/preview-sheet.png)

## Installation

### Le plus simple : demande à ton agent

Colle ceci dans Claude Code, Codex, Cursor ou n'importe quel agent :

```text
Installe le skill https://github.com/Lvni7/link-preview-images
```

### Avec la CLI skills (plus de 40 agents)

```bash
npx skills add Lvni7/link-preview-images -g
```

### À la main

```bash
# Claude Code
git clone https://github.com/Lvni7/link-preview-images ~/.claude/skills/link-preview-images
# Codex
git clone https://github.com/Lvni7/link-preview-images ~/.codex/skills/link-preview-images
```

Puis vérifie que tout marche : `python3 ~/.claude/skills/link-preview-images/link_previews.py --test` affiche `ok`.

## Utilisation

Demande à ton agent, avec tes mots :

> Mes liens n'ont pas d'image quand je les partage. Fais les images de partage de toutes les pages du site.

Ou utilise le script toi-même. Décris le site et ses pages dans un petit fichier JSON :

```json
{
  "site": { "name": "lvni7", "domain": "lvni7.dev", "accent": "#FB1E58", "theme": "gradient",
            "logo": "logo-white.svg", "logo_on_light": "logo.svg", "symbol": "symbol.svg" },
  "pages": [
    { "file": "home", "label": "Fullstack developer", "title": "Web and mobile apps, *built to ship*",
      "description": "From the first sketch to the App Store and Google Play." },
    { "file": "blog/first-app", "label": "Blog", "title": "What I learned shipping my *first app*", "theme": "dark" }
  ]
}
```

```bash
python3 link_previews.py render previews.json --out link-previews   # un PNG par page + preview.png
```

| Clé | Rôle | Obligatoire |
|---|---|---|
| `site.accent` | Couleur de marque : le dégradé, les halos, l'étiquette, le surlignage | |
| `site.theme`, `pages[].theme` | `gradient` (par défaut), `dark` ou `light` | |
| `site.logo` | Logo pour les thèmes dégradé et sombre (une version claire), SVG ou PNG | |
| `site.logo_on_light` | Logo pour le thème clair | |
| `site.symbol` | Symbole dessiné en grand en arrière-plan | |
| `site.background`, `site.light_background` | Couleurs de base des thèmes sombre et clair | |
| `site.name`, `site.domain` | Écrit quand il n'y a pas de logo ; affiché en bas | |
| `site.text` | Couleur du texte (par défaut : blanc ou noir, le plus lisible) | |
| `site.font` / `site.font_file` | Une police installée sur la machine, ou un fichier `.woff2` / `.ttf` | |
| `pages[].file` | Chemin du PNG, sans `.png` | ✓ |
| `pages[].title` | Le grand titre ; les `*mots*` sont surlignés | ✓ |
| `pages[].label`, `pages[].description` | Petite étiquette au-dessus du titre, une ou deux lignes en dessous | |

Les chemins sont relatifs au fichier JSON. Essaie-le sur le site d'exemple du dépôt :

```bash
python3 link_previews.py render examples/lvni7/previews.json --out link-previews
```

### Vérifier un site

```bash
python3 link_previews.py check out/                               # un site statique construit
python3 link_previews.py check https://exemple.fr/sitemap.xml     # toutes les pages d'un site en ligne
python3 link_previews.py check https://exemple.fr/tarifs          # une page
```

La commande se termine avec le code 1 s'il y a une erreur : elle peut aussi tourner en CI.

## Prérequis

- **Python 3.9+**, aucun paquet à installer.
- **Google Chrome**, Chromium ou Microsoft Edge. S'il est installé ailleurs que d'habitude : `CHROME=/chemin/vers/chrome python3 link_previews.py …`

## Comment ça marche

Chaque image est une page HTML rendue par Chrome sans interface à exactement 1200×630, 8 à la fois. Un petit script dans la page réduit le titre jusqu'à ce qu'il tienne en 3 lignes, une fois les polices chargées.
La planche d'aperçu est rendue de la même façon.
`check` lit le `<head>` de chaque page, récupère son `og:image` (dans le dossier pour un site construit, sur le web sinon), et lit la taille de l'image dans son en-tête : PNG, JPEG, GIF ou WebP.

Va bien avec [logo-kit](https://github.com/Lvni7/logo-kit), qui fait les versions claire et en couleur d'un logo et de son symbole.

## Licence

[MIT](LICENSE) © Lvni7
