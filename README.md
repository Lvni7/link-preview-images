# link-preview-images

**Give every page of your website its own share image, the picture people see when your link is shared, then check that every preview works.**
An [Agent Skill](https://agentskills.io) for Claude Code, Codex, Cursor and any AI agent that reads `SKILL.md`, plus a plain Python script you can run yourself.

[![License: MIT](https://img.shields.io/badge/license-MIT-FB1E58.svg)](LICENSE)
![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-FB1E58)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-FB1E58)
![No dependencies](https://img.shields.io/badge/dependencies-none-FB1E58)

🇫🇷 [Lire en français](README.fr.md)

![Four share images made by link-preview-images for a sample website: two in the bold gradient theme, one dark, one light](assets/cards.png)

When someone shares a link on LinkedIn, X, WhatsApp, Slack or iMessage, the app shows a preview card: a picture, a title, a description. The picture comes from the page's `og:image` tag (Open Graph). Most sites have none, so the link shows up bare, or they reuse one logo for every page.

**This skill fixes that in one go.** Your agent reads the site (pages, titles, colors, logo, font), and the script draws one 1200×630 image per page in your brand's style. The agent then wires the images into the site and checks the tags of every page.

- **Made to stand out:** three themes (a bold gradient built from your brand color, dark, light), your symbol drawn large in the background, and a highlighted keyword in each title.
- **On brand:** your color, your logo, your font. The text color is picked for contrast, and long titles shrink to fit in 3 lines.
- **Checked by eye:** a preview sheet shows each image as a large link card and as a small thumbnail, so an unreadable card is caught before anyone shares it.
- **Checked by the script:** missing tags, relative image URLs, unreachable images, wrong sizes and images that are too heavy, on a built site or a live one.
- **No machine-written tells:** the script refuses a long dash (—) in a card's text, and `check` flags one in your tags.
- **Native wiring:** on Next.js the images become `opengraph-image.png` files, and the framework writes the tags. Anywhere else, the agent adds the meta tags.

![The preview sheet: each page as a large link card and as a small thumbnail](assets/preview-sheet.png)

## Install

### The easy way: ask your agent

Paste this to Claude Code, Codex, Cursor or any coding agent:

```text
Install the agent skill from https://github.com/Lvni7/link-preview-images
```

### With the skills CLI (40+ agents)

```bash
npx skills add Lvni7/link-preview-images -g
```

### By hand

```bash
# Claude Code
git clone https://github.com/Lvni7/link-preview-images ~/.claude/skills/link-preview-images
# Codex
git clone https://github.com/Lvni7/link-preview-images ~/.codex/skills/link-preview-images
```

Then check that it works: `python3 ~/.claude/skills/link-preview-images/link_previews.py --test` prints `ok`.

## Use it

Ask your agent, in your own words:

> My links have no preview image when I share them. Make share images for every page of the site.

Or use the script yourself. Describe the site and its pages in a small JSON file:

```json
{
  "site": { "name": "Lvni7", "domain": "lvni7.dev", "accent": "#FB1E58", "theme": "gradient",
            "logo": "logo-white.svg", "logo_on_light": "logo.svg", "symbol": "symbol.svg" },
  "pages": [
    { "file": "home", "label": "Fullstack developer", "title": "Web and mobile apps, *built to ship*",
      "description": "From the first sketch to the App Store and Google Play." },
    { "file": "blog/first-app", "label": "Blog", "title": "What I learned shipping my *first app*", "theme": "dark" }
  ]
}
```

```bash
python3 link_previews.py render previews.json --out link-previews   # one PNG per page + preview.png
```

| Key | What it does | Required |
|---|---|---|
| `site.accent` | Brand color: the gradient, the glows, the label, the highlight | |
| `site.theme`, `pages[].theme` | `gradient` (default), `dark` or `light` | |
| `site.logo` | Logo for the gradient and dark themes (a light version), SVG or PNG | |
| `site.logo_on_light` | Logo for the light theme | |
| `site.logo_on_dark` | Logo for the dark theme (default: `logo`) | |
| `site.symbol` | Symbol drawn large in the background | |
| `site.background`, `site.light_background` | Base colors of the dark and light themes | |
| `site.name`, `site.domain` | Written when there is no logo; shown at the bottom | |
| `site.text` | Text color (default: white or black, whichever reads best) | |
| `site.font` / `site.font_file` | A font installed on the machine, or a `.woff2` / `.ttf` file | |
| `pages[].file` | Path of the PNG, without `.png` | ✓ |
| `pages[].title` | The big title; `*words*` are highlighted | ✓ |
| `pages[].label`, `pages[].description` | Small label above the title, one or two lines under it | |

Paths are relative to the JSON file. Try it on the sample site in this repository:

```bash
python3 link_previews.py render examples/lvni7/previews.json --out link-previews
```

### Check a site

```bash
python3 link_previews.py check out/                               # a built static site
python3 link_previews.py check https://example.com/sitemap.xml    # every page of a live site
python3 link_previews.py check https://example.com/pricing        # one page
```

```text
✗ blog/post.html
    warn: missing og:url
    warn: twitter:card is not summary_large_image: X shows a small card
    error: og:image must be an absolute URL: /og/post.png
✓ index.html
✗ services.html
    error: missing og:title
    error: missing og:description
    error: missing og:image
    warn: missing og:url
    warn: twitter:card is not summary_large_image: X shows a small card

3 page(s), 4 error(s)
```

It exits with code 1 when there is an error, so it can run in CI too.

## Requirements

- **Python 3.9+**, no package to install.
- **Google Chrome**, Chromium or Microsoft Edge. If it is installed somewhere unusual: `CHROME=/path/to/chrome python3 link_previews.py …`

## How it works

Each image is an HTML page rendered by headless Chrome at exactly 1200×630, 8 at a time. A small script in the page shrinks the title until it holds in 3 lines once the fonts are loaded.
The preview sheet is rendered the same way.
`check` reads each page's `<head>`, fetches its `og:image` (from the folder for a built site, from the web otherwise), and reads the image's size from its header: PNG, JPEG, GIF or WebP.

Pairs well with [logo-kit](https://github.com/Lvni7/logo-kit), which makes the light and colored versions of a logo and its symbol.

## For AI agents

If a user gives you this repository's link and asks you to install it:

1. Find your skills folder: `~/.claude/skills` for Claude Code, `~/.codex/skills` for Codex, otherwise the folder where your agent loads `SKILL.md` skills from (`~/.agents/skills` for many).
2. Run `git clone https://github.com/Lvni7/link-preview-images <skills folder>/link-preview-images`, or `npx skills add Lvni7/link-preview-images -g -y`.
3. Run `python3 <skills folder>/link-preview-images/link_previews.py --test` and check that it prints `ok`.
4. Check that Chrome, Chromium or Edge is installed.
5. Tell the user the skill is ready, and that they can ask for "share images for every page of my site".

To use the skill, read [`SKILL.md`](SKILL.md): it holds the steps, the spec format, the wiring for Next.js and other sites, and the checks.

## License

[MIT](LICENSE) © Lvni7
