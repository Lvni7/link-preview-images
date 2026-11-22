---
name: og-kit
description: Use when a website needs its link previews — Open Graph images, og:image, social share images, Twitter/X cards, the picture shown when a link is shared on LinkedIn, X, WhatsApp, Slack or iMessage — made, fixed or checked, for one page or every page. Also when the user says "OG images", "share images", "link previews", "aperçu des liens", "images de partage", "image OG", "quand je partage le lien il n'y a pas d'image". Not for the site's favicon or logo files (that is a logo kit).
---

# OG kit

Every page of a site gets its own 1200×630 share image, in the brand's style, made by `og_kit.py`,
which sits next to this file (`<skill-dir>` below). It renders with headless Chrome and needs no
Python package. **Never draw these images by hand: write the spec, run the script, look at the
preview.**

## Steps

1. **List the pages** worth sharing, with the title and description each one really shows:
   - Next.js App Router: every `app/**/page.tsx` and its `metadata` or `generateMetadata`;
   - Astro: `src/pages`; Nuxt: `pages/`; static site: the `.html` files; anything else: the router.
   - Pages made from data (blog posts, products): one image per entry when there are fewer than
     about 50. Past that, or for pages users create, static images don't keep up: tell the user,
     and offer a route that draws the image on request (Next.js `opengraph-image.tsx` with
     `ImageResponse`) using the same design.
2. **Read the brand**: background and accent colors (CSS variables, Tailwind config, logo), the
   logo file (SVG or PNG; on a dark background use a light version, which a logo kit has), and
   the font file if the site ships one (`.woff2`, `.ttf`).
3. **Write the spec** `og.json` at the project root (paths are relative to it):
   ```json
   {
     "site": {
       "name": "Nova", "domain": "nova.studio", "logo": "public/logo-white.svg",
       "background": "#0b0b12", "accent": "#6C47FF", "font_file": "public/fonts/Inter.woff2"
     },
     "pages": [
       { "file": "home", "label": "Design studio", "title": "Brand identities people remember",
         "description": "Logos, brand kits and websites for ambitious small companies." },
       { "file": "blog/logo-in-five-days", "label": "Blog", "title": "How we design a logo in five days" }
     ]
   }
   ```
   `file` is the PNG's path without `.png`. Only `file` and `title` are required. `text` (the
   text color) is picked from the background unless given; without `logo`, `name` is written
   instead. Use each page's real title, shortened if it is over about 70 characters.
4. **Run**:
   ```bash
   python3 <skill-dir>/og_kit.py render og.json --out og-images
   ```
   On Windows use `python` instead of `python3`.
5. **Look at `og-images/preview.png`** with your image-viewing tool. Each page is shown as a large
   link card and as a small thumbnail. Fix and run again when you see:
   - a logo hard to see on the background → a light or dark version of the logo;
   - a title shrunk very small, or a label longer than the title → a shorter title or label;
   - text unreadable in the small thumbnail → fewer words; drop the description.
6. **Wire the images in**:
   - **Next.js App Router**: copy each PNG to the matching route as `opengraph-image.png`, and
     again as `twitter-image.png` (`og-images/home.png` → `app/opengraph-image.png`,
     `og-images/blog/x.png` → `app/blog/x/opengraph-image.png`). Next.js then writes `og:image`,
     its size and type, `twitter:image` and `twitter:card` itself. Set `metadataBase` in the root
     layout so the URLs are absolute, and give each page `openGraph: { title, description, url }`
     in its metadata.
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
   python3 <skill-dir>/og_kit.py check out/                                  # a built static site
   python3 <skill-dir>/og_kit.py check https://domain/sitemap.xml            # a live site
   ```
   Every error must be fixed. A site served by a server (Next.js without static export) is
   checked once deployed: before that, its absolute image URLs point to a domain that doesn't
   serve them yet.

## Common mistakes

- A relative `og:image` (`/og/home.png`): apps ignore it. Always the full URL.
- Saying "done" without looking at `preview.png`. The script checks sizes, not readability.
- Forgetting caches: LinkedIn and Facebook keep an old preview for days. After deploying,
  tell the user to refresh it with LinkedIn's Post Inspector and Facebook's Sharing Debugger.
- Committing `og-images/`: only the copies wired into the site belong in the repository.

The script checks itself with `python3 <skill-dir>/og_kit.py --test`.
