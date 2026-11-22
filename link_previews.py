#!/usr/bin/env python3
"""link-preview-images: a share image (Open Graph) for every page of a site, and a check of the tags.

    python3 link_previews.py render previews.json [--out link-previews]   # one 1200x630 PNG per page + preview sheet
    python3 link_previews.py check <folder | page URL | sitemap.xml URL>
    python3 link_previews.py --test

Renders with headless Chrome. No Python package needed.
"""
import argparse
import concurrent.futures as cf
import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

W, H = 1200, 630
# The long dash reads as machine-written: no text this skill writes may hold one. A spaced en
# dash ("a – b") is the same dash in disguise; an unspaced one ("2020–2024") is a range and stays.
LONG_DASH = re.compile(r"—|\s–\s")
UA = {"User-Agent": "link-preview-images/1.0 (+https://github.com/Lvni7/link-preview-images)"}


# ---------- colors ----------

def luminance(hexa):
    h = hexa.lstrip("#")
    h = "".join(c * 2 for c in h) if len(h) == 3 else h[:6]
    lin = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def readable_on(background):
    """White or near-black, whichever reads best on this background."""
    return "#ffffff" if luminance(background) < 0.4 else "#0b0b12"


# ---------- render ----------

def find_chrome():
    programs = os.environ.get("PROGRAMFILES", r"C:\Program Files"), os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
    candidates = [os.environ.get("CHROME"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                  "/Applications/Chromium.app/Contents/MacOS/Chromium",
                  *(shutil.which(n) for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")),
                  *(rf"{p}\Google\Chrome\Application\chrome.exe" for p in programs),
                  *(rf"{p}\Microsoft\Edge\Application\msedge.exe" for p in programs)]
    for c in candidates:
        if c and Path(c).exists():
            return c
    sys.exit("Chrome not found. Install Google Chrome, or give its path: CHROME=/path/to/chrome python3 link_previews.py ...")


def screenshot(chrome, tmp, page_html, out, w, h):
    """Renders page_html at w×h into out (PNG); fails unless the PNG has exactly that size."""
    d = Path(tempfile.mkdtemp(dir=tmp))
    page = d / "page.html"
    page.write_text(page_html, encoding="utf-8")
    # Chrome refuses to run as root without --no-sandbox (containers, cloud agents).
    root = ["--no-sandbox"] if hasattr(os, "geteuid") and os.geteuid() == 0 else []
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    f"--user-data-dir={d / 'profile'}", *root, "--virtual-time-budget=5000",
                    f"--window-size={w},{h}", f"--screenshot={out}", page.as_uri()],
                   check=True, capture_output=True, timeout=180)
    got = struct.unpack(">II", out.read_bytes()[16:24])
    if got != (w, h):
        raise RuntimeError(f"{out.name}: {got[0]}×{got[1]} instead of {w}×{h}")


THEMES = ("gradient", "dark", "light")


def plain(title):
    """The title without its *highlight* marks, as a link card shows it."""
    return title.replace("*", "")


def card_html(site, page, base):
    """One 1200×630 card: logo, label pill, title fitted to 3 lines, description, domain, and the
    brand symbol drawn large in the background. Three themes: gradient (built from the accent),
    dark and light."""
    accent = site.get("accent", "#6C47FF")
    theme = page.get("theme") or site.get("theme") or "gradient"
    if theme == "gradient":
        # Light at the top left, the accent in the middle, deeper at the edges.
        bg = (f"radial-gradient(ellipse 70% 80% at 22% 8%,color-mix(in srgb,{accent} 38%,white),transparent 62%),"
              f"radial-gradient(ellipse 120% 120% at 60% 45%,{accent} 30%,color-mix(in srgb,{accent} 78%,black))")
        text, ref = "#ffffff", accent
    else:
        ref = site.get("background", "#0b0b12") if theme == "dark" else site.get("light_background", "#ffffff")
        glow = "40%" if theme == "dark" else "16%"
        bg = (f"radial-gradient(ellipse 55% 75% at 100% 0,color-mix(in srgb,{accent} {glow},transparent),transparent 70%),"
              f"radial-gradient(ellipse 45% 60% at 0 100%,color-mix(in srgb,{accent} {glow},transparent),transparent 70%),{ref}")
        text = readable_on(ref)
    text = site.get("text") or text
    on_accent = theme == "gradient"
    pill_bg = "rgba(255,255,255,.18)" if on_accent else f"color-mix(in srgb,{accent} 14%,transparent)"
    pill_fg = "#ffffff" if on_accent else accent
    mark_css = {"gradient": "filter:brightness(0) invert(1);opacity:.16", "dark": "opacity:.22", "light": "opacity:.14"}[theme]
    font = site.get("font") or "system-ui"
    face = ""
    if site.get("font_file"):
        face = (f"@font-face{{font-family:'og-font';src:url('{(base / site['font_file']).resolve().as_uri()}');"
                f"font-weight:100 900}}")
        font = "og-font"
    logo = site.get("logo_on_light") if theme == "light" and site.get("logo_on_light") else site.get("logo")
    uri = lambda p: (base / p).resolve().as_uri()
    e = html.escape
    brand = f'<img class="logo" src="{uri(logo)}">' if logo else f'<b class="name">{e(site.get("name", ""))}</b>'
    mark = f'<img class="mark" src="{uri(site["symbol"])}">' if site.get("symbol") else ""
    title = re.sub(r"\*(.+?)\*", r"<em>\1</em>", e(page["title"]))
    label, desc = page.get("label", ""), page.get("description", "")
    em = (f"background:#fff;color:{accent};padding:0 .14em;border-radius:.16em;box-decoration-break:clone;"
          f"-webkit-box-decoration-break:clone" if on_accent else f"color:{accent}")
    return f"""<!doctype html><meta charset="utf-8"><style>{face}
*{{box-sizing:border-box;margin:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{position:relative;padding:68px 80px 60px;background:{bg};color:{text};
  font-family:{font},-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;display:flex;flex-direction:column}}
.mark{{position:absolute;right:-110px;top:50%;width:560px;height:560px;transform:translateY(-50%) rotate(-10deg);
  object-fit:contain;{mark_css}}}
.logo{{position:relative;height:54px;max-width:420px;object-fit:contain;object-position:left}}
.name{{position:relative;font-size:34px;font-weight:800;letter-spacing:-.02em}}
.main{{position:relative;margin-top:auto;display:flex;flex-direction:column;align-items:flex-start;gap:22px}}
.label{{background:{pill_bg};color:{pill_fg};border:1.5px solid color-mix(in srgb,{pill_fg} 35%,transparent);
  padding:9px 22px;border-radius:999px;font-size:22px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}}
.title{{font-size:92px;font-weight:800;line-height:1.04;letter-spacing:-.035em;max-width:900px;text-wrap:balance}}
.title em{{font-style:normal;{em}}}
.desc{{font-size:29px;line-height:1.35;opacity:.86;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
  overflow:hidden;max-width:860px}}
.foot{{position:relative;margin-top:36px;display:flex;align-items:center;gap:14px;font-size:24px;font-weight:600;opacity:.8}}
</style>
{mark}
{brand}
<div class="main">
  {f'<div class="label">{e(label)}</div>' if label else ''}
  <h1 class="title">{title}</h1>
  {f'<p class="desc">{e(desc)}</p>' if desc else ''}
</div>
<div class="foot">{e(site.get("domain", ""))}</div>
<script>
// Shrinks the title until it holds in 3 lines, once the fonts are in. offsetHeight counts
// line boxes only: scrollHeight would also count glyphs drawn past a tight line-height.
document.fonts.ready.then(() => {{
  const t = document.querySelector('.title');
  let s = 92;
  while (t.offsetHeight > 3.5 * 1.04 * s && s > 40) {{ s -= 2; t.style.fontSize = s + 'px'; }}
}});
</script>"""


def sheet_html(site, cards):
    """Each card as a large link preview and as a small thumbnail, to judge it at both sizes."""
    domain = html.escape(site.get("domain", ""))
    rows = "".join(f"""<section><h2>{html.escape(name)}</h2><div class="row">
<figure class="large"><img src="{png.as_uri()}"><figcaption><small>{domain}</small><b>{html.escape(plain(page['title']))}</b></figcaption></figure>
<figure class="small"><img src="{png.as_uri()}"><figcaption><b>{html.escape(plain(page['title']))}</b><small>{domain}</small></figcaption></figure>
</div></section>""" for name, page, png in cards)
    return f"""<!doctype html><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0}} body{{width:1240px;padding:40px;background:#f2f2f5;color:#1b1b22;
font:15px/1.4 -apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}}
h1{{font-size:26px;height:32px;line-height:32px;margin-bottom:24px}}
h2{{font-size:14px;height:24px;line-height:24px;color:#6b6b78;font-weight:600;margin:0 0 10px}}
section{{height:400px;margin-bottom:28px}} .row{{display:flex;gap:28px;align-items:flex-start}}
figure{{background:#fff;border:1px solid #dcdce3;border-radius:10px;overflow:hidden}}
.large{{width:560px}} .large img{{display:block;width:560px;height:294px}}
.large figcaption{{height:64px;padding:12px 14px;display:flex;flex-direction:column;gap:2px}}
.large small{{color:#6b6b78;text-transform:uppercase;font-size:12px}} .large b{{font-size:16px}}
.small{{width:520px;display:flex;align-items:center;gap:12px;padding:10px}}
.small img{{width:150px;height:79px;border-radius:6px;object-fit:cover}}
.small figcaption{{display:flex;flex-direction:column;gap:4px}} .small small{{color:#6b6b78}}
</style><h1>Share previews · {html.escape(site.get('name', ''))}</h1>{rows}"""


def render(spec_path, out):
    spec_path = Path(spec_path)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    site, pages = spec.get("site", {}), spec.get("pages", [])
    if not pages:
        sys.exit(f"{spec_path}: no pages")
    base = spec_path.resolve().parent
    for key in ("logo", "logo_on_light", "symbol", "font_file"):
        if site.get(key) and not (base / site[key]).is_file():
            sys.exit(f"{spec_path}: site.{key} not found: {site[key]} (paths are relative to the JSON file)")
    for p in [site, *pages]:
        if p.get("theme") and p["theme"] not in THEMES:
            sys.exit(f"{spec_path}: theme must be one of {', '.join(THEMES)}: {p['theme']}")
    for p in pages:
        if not p.get("title") or not p.get("file"):
            sys.exit(f"{spec_path}: every page needs a 'file' and a 'title': {p}")
    dashed = [f"{p['file']}.{k}" for p in pages for k in ("label", "title", "description") if LONG_DASH.search(p.get(k, ""))]
    if dashed:
        sys.exit(f"{spec_path}: no long dash (—) in a card's text; rewrite with a colon, a comma or two sentences: "
                 + ", ".join(dashed))
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    jobs = [(p["file"], p, out / f"{p['file']}.png") for p in pages]
    with tempfile.TemporaryDirectory() as tmp, cf.ThreadPoolExecutor(8) as pool:
        for _, _, png in jobs:
            png.parent.mkdir(parents=True, exist_ok=True)
        waits = [pool.submit(screenshot, chrome, tmp, card_html(site, p, base), png, W, H) for _, p, png in jobs]
        for w in waits:
            w.result()  # raises the first error
        sheet = sheet_html(site, jobs)
        (out / "preview.html").write_text(sheet, encoding="utf-8")
        height = 40 + 56 + len(jobs) * 428 - 28 + 40  # the sheet's fixed heights
        screenshot(chrome, tmp, sheet, out / "preview.png", 1240, height)
    for _, _, png in jobs:
        kb = png.stat().st_size // 1024
        print(f"{png.relative_to(out)}  {W}×{H}  {kb} KB" + ("  ⚠ over 1 MB" if kb > 1024 else ""))
    print(f"Check: {out / 'preview.png'}")


# ---------- check ----------

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.title, self._in_title = {}, "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = a.get("property") or a.get("name")
            if key and key.lower() not in self.tags:
                self.tags[key.lower()] = (a.get("content") or "").strip()
        self._in_title = tag == "title"

    def handle_endtag(self, tag):
        self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def image_size(data):
    """(width, height) of a PNG, JPEG, GIF or WebP, else None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X":
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        if data[12:16] == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if data[12:16] == b"VP8L":
            b = int.from_bytes(data[21:25], "little")
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + length
    return None


def fetch(url, limit=10_000_000):
    """The bytes at url. curl first: it uses the system's certificates, which python.org's
    Python on macOS lacks until "Install Certificates.command" is run."""
    if shutil.which("curl"):
        r = subprocess.run(["curl", "-sSfL", "--max-time", "20", "--max-filesize", str(limit), "-A", UA["User-Agent"], url],
                           capture_output=True)
        if r.returncode:
            raise OSError(r.stderr.decode("utf-8", "replace").strip() or f"curl exit {r.returncode}")
        return r.stdout
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return r.read(limit)


def audit(tags, title, load_image):
    """Problems of one page: (level, message), level 'error' or 'warn'."""
    issues = []
    for key in ("og:title", "og:description", "og:image"):
        if not tags.get(key):
            issues.append(("error", f"missing {key}"))
    if not tags.get("og:url"):
        issues.append(("warn", "missing og:url"))
    if tags.get("twitter:card") != "summary_large_image":
        issues.append(("warn", "twitter:card is not summary_large_image: X shows a small card"))
    image = tags.get("og:image")
    if image:
        if not image.startswith(("http://", "https://")):
            issues.append(("error", f"og:image must be an absolute URL: {image}"))
        else:
            try:
                data = load_image(image)
            except Exception as err:  # unreachable image: the card shows none
                issues.append(("error", f"og:image unreachable: {image} ({err})"))
            else:
                if data is None:
                    issues.append(("warn", f"og:image not found locally, not checked: {image}"))
                else:
                    size = image_size(data)
                    if not size:
                        issues.append(("warn", "og:image format not recognized"))
                    elif size[0] < 600 or abs(size[0] / size[1] - 1.91) > 0.06:
                        issues.append(("warn", f"og:image is {size[0]}×{size[1]}: share cards are 1.91:1, use 1200×630"))
                    if len(data) > 1_048_576:
                        issues.append(("warn", f"og:image weighs {len(data) // 1024} KB: compress it under 1 MB"))
    if not tags.get("og:title") and not title.strip():
        issues.append(("error", "no title at all"))
    for key in ("og:title", "og:description"):
        if LONG_DASH.search(tags.get(key, "")):
            issues.append(("warn", f"{key} holds a long dash (—): rewrite it with a colon or a comma"))
    return issues


def check(target):
    pages = []  # (name, html text, image loader)
    unreachable = 0
    if Path(target).is_dir():
        root = Path(target).resolve()

        def local(url):  # https://site.com/og/a.png -> <root>/og/a.png
            f = root / urllib.parse.unquote(urllib.parse.urlparse(url).path).lstrip("/")
            return f.read_bytes() if f.is_file() else None
        for f in sorted(root.rglob("*.html")):
            pages.append((f.relative_to(root).as_posix(), f.read_text(encoding="utf-8", errors="replace"), local))
    else:
        urls = [target]
        if target.endswith(".xml"):
            urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", fetch(target).decode("utf-8", "replace"))[:200]
        for u in urls:
            try:
                pages.append((u, fetch(u).decode("utf-8", "replace"), fetch))
            except Exception as err:
                unreachable += 1
                print(f"✗ {u}\n    error: page unreachable ({err})")
    if not pages and not unreachable:
        sys.exit(f"No page found in {target}")
    errors = unreachable
    for name, text, loader in pages:
        m = Meta()
        m.feed(text)
        issues = audit(m.tags, m.title, loader)
        errors += sum(level == "error" for level, _ in issues)
        print(("✗ " if any(level == "error" for level, _ in issues) else "⚠ " if issues else "✓ ") + name)
        for level, msg in issues:
            print(f"    {level}: {msg}")
    print(f"\n{len(pages) + unreachable} page(s), {errors} error(s)")
    return 1 if errors else 0


# ---------- self-test ----------

def test():
    assert readable_on("#0b0b12") == "#ffffff" and readable_on("#f5f5f5") == "#0b0b12"
    assert plain("Ship *fast*") == "Ship fast"
    assert LONG_DASH.search("Apps — fast") and LONG_DASH.search("Apps – fast") and not LONG_DASH.search("2020–2024")
    m = Meta()
    m.feed('<title>T</title><meta property="og:title" content="A"><meta name="twitter:card" content="summary">')
    assert m.tags == {"og:title": "A", "twitter:card": "summary"} and m.title == "T"
    png = b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + struct.pack(">II", 1200, 630)
    assert image_size(png) == (1200, 630)
    jpeg = b"\xff\xd8\xff\xe0\x00\x10" + b"\0" * 14 + b"\xff\xc0\x00\x11\x08" + struct.pack(">HH", 630, 1200) + b"\0" * 8
    assert image_size(jpeg) == (1200, 630)
    good = {"og:title": "A", "og:description": "B", "og:image": "https://x.com/a.png", "og:url": "https://x.com/",
            "twitter:card": "summary_large_image"}
    assert audit(good, "", lambda u: png) == []
    assert any("long dash" in m for _, m in audit({**good, "og:title": "A — B"}, "", lambda u: png))
    assert ("error", "og:image must be an absolute URL: /a.png") in audit({**good, "og:image": "/a.png"}, "", None)
    assert any("1200×630" in m for _, m in audit(good, "", lambda u: png[:16] + struct.pack(">II", 800, 800)))
    print("ok")


def main():
    if sys.argv[1:] == ["--test"]:
        return test()
    p = argparse.ArgumentParser(description="Open Graph share images for every page, and a check of the tags.")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="one 1200×630 PNG per page of the JSON spec, plus preview.png")
    r.add_argument("spec", help="the JSON spec (see SKILL.md)")
    r.add_argument("--out", default="link-previews", help="output folder (default: %(default)s)")
    c = sub.add_parser("check", help="check the Open Graph tags of a built site folder, a page URL or a sitemap.xml URL")
    c.add_argument("target")
    a = p.parse_args()
    if a.cmd == "render":
        render(a.spec, a.out)
    else:
        sys.exit(check(a.target))


if __name__ == "__main__":
    main()
