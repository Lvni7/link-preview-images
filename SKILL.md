---
name: link-preview-images
description: Use when a website needs its link previews (Open Graph images, og:image, social share images, Twitter/X cards, the picture shown when a link is shared on LinkedIn, X, WhatsApp, Slack or iMessage) made, fixed or checked, for one page or every page. Also when the user says "OG images", "share images", "link previews", "aperçu des liens", "images de partage", "image OG", "quand je partage le lien il n'y a pas d'image". Not for the site's favicon or logo files (that is a logo kit).
---

# Link preview images

Every page of a site gets its own 1200×630 share image in the brand's style, made by
`link_previews.py`, which sits next to this file (`<skill-dir>` below). It renders with headless
Chrome and needs no Python package. **Never draw these images by hand: write the spec, run the
script, look at the preview.**

## Steps

1. **List the pages** worth sharing, with the title and description each one really shows:
   - Next.js App Router: every `app/**/page.tsx` and its `metadata` or `generateMetadata`;
   - Astro: `src/pages`; Nuxt: `pages/`; static site: the `.html` files; anything else: the router.
   - Pages made from data (blog posts, products): one image per entry when there are fewer than
     about 50. Past that, or for pages users create, static images don't keep up: tell the user,
     and offer a route that draws the image on request (Next.js `opengraph-image.tsx` with
     `ImageResponse`) using the same design.
2. **Read the brand**: the accent color (CSS variables, Tailwind config, logo), the logo in a
   light version for colored and dark backgrounds and in its normal colors for light ones (a logo
   kit has both), the symbol alone if there is one, and the font file if the site ships one.
3. **Write the spec** `previews.json` at the project root (paths are relative to it):
   ```json
   {
     "site": {
       "name": "lvni7", "domain": "lvni7.dev", "accent": "#FB1E58", "theme": "gradient",
       "logo": "public/logo-white.svg", "logo_on_light": "public/logo.svg",
       "symbol": "public/symbol.svg", "font_file": "public/fonts/Inter.woff2"
     },
     "pages": [
       { "file": "home", "label": "Fullstack developer", "title": "Web and mobile apps, *built to ship*",
         "description": "From the first sketch to the App Store and Google Play." },
       { "file": "blog/first-app", "label": "Blog", "title": "What I learned shipping my *first app*", "theme": "dark" }
     ]
   }
   ```
   - `file` is the PNG's path without `.png`. Only `file` and `title` are required.
   - `theme`, for the site or one page: `gradient` (built from the accent, the boldest), `dark`
     (`background`, near-black by default) or `light` (`light_background`, white by default).
     Mixing themes across sections (blog in dark, case studies in light) reads well.
   - `*words*` in a title are highlighted. One highlight per title at most, on the words that matter.
   - `symbol` is drawn large in the background. `text` (the text color) is picked for contrast
     unless given; without `logo`, `name` is written instead.
   - Use each page's real title, shortened if it is over about 70 characters. The `*` marks are
     for the image only: never put them in the page's `og:title`.
   - **Never a long dash (—)**, nor a dash between spaces (" – "), in anything you write: card
     texts, `og:title`, `og:description`, alt texts. It reads as machine-written. Use a colon, a
     comma or two sentences. The script refuses a card that holds one, and `check` flags it in
     the tags.
4. **Run**:
   ```bash
   python3 <skill-dir>/link_previews.py render previews.json --out link-previews
   ```
   On Windows use `python` instead of `python3`.
5. **Look at `link-previews/preview.png`** with your image-viewing tool. Each page is shown as a
   large link card and as a small thumbnail. Fix and run again when you see:
   - a logo hard to see on its background → `logo` or `logo_on_light` in the right version;
   - a title shrunk very small, or a label longer than the title → a shorter title or label;
   - text unreadable in the small thumbnail → fewer words; drop the description.
6. **Wire the images in**:
   - **Next.js App Router**: copy each PNG to the matching route as `opengraph-image.png`, and
     again as `twitter-image.png` (`link-previews/home.png` → `app/opengraph-image.png`,
     `link-previews/blog/x.png` → `app/blog/x/opengraph-image.png`). Next.js then writes
     `og:image`, its size and type, `twitter:image` and `twitter:card` itself. Set `metadataBase`
     in the root layout so the URLs are absolute, and give each page
     `openGraph: { title, description, url }` in its metadata.
   - **Any other site**: put the PNGs in the public folder under `og/` and add to each page's
     `<head>`, with absolute URLs:
     ```html
     <meta property="og:title" content="…">
     <meta property="og:description" content="…">
     <meta property="og:url" content="https://domain/page">
     <meta property="og:image" content="https://domain/og/page.png">
     <meta property="og:image:width" content="1200">
     <meta property="og:image:height" content="630">
     <meta property="og:image:alt" content="…">
     <meta name="twitter:card" content="summary_large_image">
     ```
7. **Check**, then tell the user what you found:
   ```bash
   python3 <skill-dir>/link_previews.py check out/                         # a built static site
   python3 <skill-dir>/link_previews.py check https://domain/sitemap.xml   # a live site
   ```
   Every error must be fixed. A site served by a server (Next.js without static export) is
   checked once deployed: before that, its absolute image URLs point to a domain that doesn't
   serve them yet.

## Common mistakes

- A long dash (—) in a title or description, copied from the page or written by habit.
- A relative `og:image` (`/og/home.png`): apps ignore it. Always the full URL.
- Saying "done" without looking at `preview.png`. The script checks sizes, not readability.
- Forgetting caches: LinkedIn and Facebook keep an old preview for days. After deploying, tell
  the user to refresh it with LinkedIn's Post Inspector and Facebook's Sharing Debugger.
- Committing `link-previews/`: only the copies wired into the site belong in the repository.

The script checks itself with `python3 <skill-dir>/link_previews.py --test`.
