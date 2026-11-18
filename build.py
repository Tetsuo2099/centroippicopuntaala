#!/usr/bin/env python3
"""CIP — generatore del sito statico. Unica fonte di verità: src/.
uso:  python3 build.py            → rigenera docs/ (cartella pubblicata da GitHub Pages)
      python3 build.py --serve    → rigenera e apre un server su http://localhost:8790

src/layout.html          scheletro comune (head, header, menu, footer)
src/pagine/<slug>.html   contenuto di ogni pagina; in testa un commento JSON con i meta:
                         <!--{"title": "...", "description": "...", "og_image": "/media/..."}-->
src/css, src/js, src/fonts   copiati così come sono
src/media/               file che sostituiscono quelli originali (es. video ricompressi)

I file /media/AAAA/MM/... citati nelle pagine vengono presi da src/media/ oppure dallo scarico
del vecchio sito (../_originale/assets/wp-content/uploads/), ridimensionati se troppo grandi.
"""
import html as html_lib, json, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "src", ROOT / "docs"
ORIG = ROOT.parent / "_originale" / "assets" / "wp-content" / "uploads"
DOMINIO = "https://www.centroippicopuntaala.it"
V = str(int(time.time()))  # cache bust

MENU = [
    ("Home", "/"),
    ("Equitazione", "/equitazione-lezioni-di-polo/"),
    ("Polo Club", "/polo-club/"),
    ("Campus Estivi", "/campus-estivi/"),
    ("Pensione Cavalli", "/pensione-cavalli/"),
    ("Stage Tecnici", "/stage-tecnici/"),
    ("Caccia alla volpe", "/caccia-alla-volpe/"),
    ("Eventi", "/eventi/"),
    ("Contatti", "/contatti/"),
]
MENU_EN = [
    ("Home", "/en/"),
    ("Riding lessons", "/en/riding-lessons/"),
    ("Polo Club", "/en/polo-club/"),
    ("Summer Camps", "/en/summer-camps/"),
    ("Horse Livery", "/en/horse-livery/"),
    ("Riding Clinics", "/en/riding-clinics/"),
    ("Fox hunting", "/en/fox-hunting/"),
    ("Events", "/en/events/"),
    ("Contact", "/en/contact/"),
]
# testi fissi del layout per lingua
T = {
    "it": {"lang": "it", "og_locale": "it_IT", "og_locale_alt": "en_GB", "home": "/",
           "t_menu_principale": "Menu principale", "t_chiudi_menu": "Chiudi menu", "t_dove": "Dove siamo",
           "t_indicazioni": "Indicazioni", "t_orari": "Orari: 09-19 (tutti i giorni)", "t_contatti": "Contatti",
           "t_diritti": "Tutti i diritti riservati.", "t_affiliato": "Centro affiliato", "t_pref_cookie": "Preferenze cookie",
           "t_torna_su": "Torna su", "alt_lang": "en", "alt_nome": "English version", "alt_sigla": "EN"},
    "en": {"lang": "en", "og_locale": "en_GB", "og_locale_alt": "it_IT", "home": "/en/",
           "t_menu_principale": "Main menu", "t_chiudi_menu": "Close menu", "t_dove": "Find us",
           "t_indicazioni": "Directions", "t_orari": "Open daily: 9am–7pm", "t_contatti": "Contact",
           "t_diritti": "All rights reserved.", "t_affiliato": "Affiliated centre", "t_pref_cookie": "Cookie preferences",
           "t_torna_su": "Back to top", "alt_lang": "it", "alt_nome": "Versione italiana", "alt_sigla": "IT"},
}
REDIRECT = {  # vecchi URL WordPress → nuovi
    "/calendar/eventi/": "/eventi/",
    "/category/uncategorized/": "/blog/",
    "/author/sadmin/": "/blog/",
    "/home/": "/",
    "/feed/": "/blog/",
}
MAX_LATO = 2000  # px: immagini più grandi vengono ridotte


def url_di(slug):
    return "/" if slug == "index" else f"/{slug}/"


def leggi_pagina(f):
    testo = f.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", testo, re.S)
    meta = json.loads(m.group(1)) if m else {}
    return meta, testo[m.end():] if m else testo


def menu_html(url, lingua="it"):
    righe = []
    for nome, href in (MENU_EN if lingua == "en" else MENU):
        cur = ' aria-current="page"' if href == url else ""
        righe.append(f'    <li><a href="{href}"{cur}>{nome}</a></li>')
    return "\n".join(righe)


def render(layout, slug, meta, contenuto, lingua="it", alt=None):
    """alt = URL della stessa pagina nell'altra lingua (None se non esiste)."""
    url = meta.get("url") or url_di(slug)
    t = T[lingua]
    if alt:
        it_u, en_u = (url, alt) if lingua == "it" else (alt, url)
        hreflang = (f'<link rel="alternate" hreflang="it" href="{DOMINIO}{it_u}">\n'
                    f'<link rel="alternate" hreflang="en" href="{DOMINIO}{en_u}">\n'
                    f'<link rel="alternate" hreflang="x-default" href="{DOMINIO}{it_u}">')
    else:
        hreflang = ""
    val = {
        **t,
        "hreflang": hreflang,
        "alt_url": alt or ("/en/" if lingua == "it" else "/"),
        "title": meta.get("title", "Centro Ippico Punta Ala"),
        "description": meta.get("description", ""),
        "canonical": DOMINIO + url,
        "og_type": meta.get("og_type", "article" if meta.get("post") else "website"),
        "og_image": DOMINIO + meta.get("og_image", "/media/2025/11/testa_bianca.png"),
        "head_extra": meta.get("head_extra", "") + (f'<link rel="stylesheet" href="/css/p-{slug}.css?v={V}">' if (SRC / "css" / f"p-{slug}.css").exists() else ""),
        "body_extra": f'<script src="/js/p-{slug}.js?v={V}" defer></script>' if (SRC / "js" / f"p-{slug}.js").exists() else "",
        "body_class": meta.get("body_class", ""),
        "menu": menu_html(url, lingua),
        "content": contenuto,
        "v": V,
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: val.get(m.group(1), m.group(0)), layout), url


def copia_media(rif):
    """rif = '/media/2024/04/foto.jpg' → docs/media/2024/04/foto.jpg"""
    rel = rif[len("/media/"):]
    dst = OUT / "media" / rel
    if dst.exists():
        return True
    src = SRC / "media" / rel
    if not src.exists():
        src = ORIG / rel
    if not src.exists():
        print(f"  ! manca {rif}")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    ext = src.suffix.lower()
    if ext in (".jpg", ".jpeg") and src.stat().st_size > 300_000:
        # JPG pesanti: max 2000px, qualità 80, progressivo, senza metadati
        subprocess.run(["magick", str(src), "-resize", f"{MAX_LATO}x{MAX_LATO}>", "-strip", "-interlace", "Plane",
                        "-sampling-factor", "4:2:0", "-quality", "80", str(dst)], check=True)
        if dst.stat().st_size >= src.stat().st_size:
            shutil.copy2(src, dst)
        return True
    if ext in (".png", ".webp"):
        w = subprocess.run(["magick", "identify", "-format", "%w %h", str(src)], capture_output=True, text=True).stdout.split()
        if w and max(int(w[0]), int(w[1])) > MAX_LATO:
            subprocess.run(["magick", str(src), "-resize", f"{MAX_LATO}x{MAX_LATO}>", "-strip", str(dst)], check=True)
            return True
    shutil.copy2(src, dst)
    return True


# ---------- Articoli (src/post/<slug>.html) ----------
# meta JSON in testa: {"title": "<title pagina>", "h1": "Titolo visibile", "date": "2026-03-24",
#   "featured": "/media/...jpg", "thumb": "/media/...-768x...jpg", "excerpt": "...", "description": "..."}
FRECCE = ('<button class="carosello__freccia carosello__freccia--prev" type="button" aria-label="Precedente"><svg viewBox="0 0 20 40"><path d="M18 2 2 20l16 18"/></svg></button>',
          '<button class="carosello__freccia carosello__freccia--next" type="button" aria-label="Successivo"><svg viewBox="0 0 20 40"><path d="M2 2l16 18L2 38"/></svg></button>')


def esc(t):
    return html_lib.escape(t or "", quote=True)


def carica_post():
    posts = []
    for f in (SRC / "post").glob("*.html"):
        meta, corpo = leggi_pagina(f)
        meta["slug"] = f.stem
        posts.append((meta, corpo))
    posts.sort(key=lambda p: p[0].get("date", ""), reverse=True)
    f = SRC / "post" / "_ordine.txt"
    if f.exists():
        ordine = [r.strip() for r in f.read_text().splitlines() if r.strip() and not r.startswith("#")]
        pos = {s: i for i, s in enumerate(ordine)}
        posts.sort(key=lambda p: pos.get(p[0]["slug"], len(ordine)))  # stabile: i non elencati restano per data
    return posts


def card_home(m, lingua="it"):
    u = f"/{m['slug']}/"
    return (f'    <article class="card">\n      <a class="card__img" href="{u}" tabindex="-1"><img src="{m.get("thumb") or m.get("featured")}" alt="" loading="lazy"></a>\n'
            f'      <h5><a href="{u}">{esc(m.get("h1"))}</a></h5>\n      <p>{esc(m.get("excerpt"))}</p>\n'
            f'      <a class="btn btn--sm" href="{u}"' + (' hreflang="it">Read more' if lingua == "en" else '>Leggi tutto') + '</a>\n    </article>')


def card_altri(m):
    u = f"/{m['slug']}/"
    return (f'    <article class="card card--altri">\n      <a class="card__img" href="{u}" tabindex="-1"><img src="{m.get("thumb") or m.get("featured")}" alt="" loading="lazy"></a>\n'
            f'      <h5><a href="{u}">{esc(m.get("h1"))}</a></h5>\n    </article>')


MESI = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()


def elenco_post(posts):
    righe = []
    for m, _ in posts:
        d = m.get("date", "")
        data = f"{int(d[8:10])} {MESI[int(d[5:7]) - 1]} {d[:4]}" if len(d) >= 10 else ""
        righe.append(f'    <li><a href="/{m["slug"]}/"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M7 3l7 7-7 7"/></svg>'
                     f'<span class="blog-elenco__t">{esc(m.get("h1"))}</span><time datetime="{d}">{data}</time></a></li>')
    return "\n".join(righe)


def ultimi_post(posts, n=12, lingua="it"):
    return "\n".join(card_home(m, lingua) for m, _ in posts[:n])


def pagina_post(m, corpo, posts):
    altri = "\n".join(card_altri(x) for x, _ in posts if x["slug"] != m["slug"])
    return f"""<section class="post-testa" style="background-image:url('{m.get("featured", "")}')">
  <h1 class="post-testa__titolo">{esc(m.get("h1"))}</h1>
</section>
<article class="post-corpo">
{corpo}
</article>
<section class="carosello carosello--altri" aria-label="Altri articoli">
  <h3 class="t3">Altri articoli</h3>
  {FRECCE[0]}
  <div class="carosello__traccia">
{altri}
  </div>
  {FRECCE[1]}
</section>"""


def galleria_en(slug, corpo, m):
    """<!--GALLERIA--> → la galleria della pagina italiana, con alt e etichette tradotti."""
    if "<!--GALLERIA-->" not in corpo:
        return corpo
    it = (SRC / "pagine" / f"{slug}.html").read_text(encoding="utf-8")
    i = min(x for x in (it.find('<div class="galleria"'), it.find('<div class="scroller"')) if x >= 0)
    g = it[i:]
    g = re.sub(r'alt="[^"]*— foto (\d+)"', lambda x: f'alt="{m.get("alt_galleria", "Centro Ippico Punta Ala")} — photo {x.group(1)}"', g)
    g = g.replace('aria-label="Foto precedenti"', 'aria-label="Previous photos"').replace('aria-label="Foto successive"', 'aria-label="Next photos"')
    return corpo.replace("<!--GALLERIA-->", g)


def build():
    # svuota docs/ tranne media/ (le immagini già ottimizzate restano) e CNAME
    OUT.mkdir(exist_ok=True)
    for p in OUT.iterdir():
        if p.name in ("media",):
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    for d in ("css", "js", "fonts"):
        shutil.copytree(SRC / d, OUT / d)

    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    posts = carica_post()
    sorgenti = [(f.stem, *leggi_pagina(f)) for f in sorted((SRC / "pagine").glob("*.html"))]
    for m, corpo in posts:
        m.setdefault("post", True)
        m["body_class"] = (m.get("body_class", "") + " post").strip()
        m.setdefault("og_image", m.get("featured"))
        sorgenti.append((m["slug"], m, pagina_post(m, corpo, posts)))
    # versione inglese: src/en/<slug-italiano>.html, meta con "url": "/en/..."
    alt = {}
    for f in sorted((SRC / "en").glob("*.html")):
        m, corpo = leggi_pagina(f)
        it_url = url_di(f.stem)
        alt[it_url], alt[m["url"]] = m["url"], it_url
        m["lingua"] = "en"
        sorgenti.append((f.stem, m, galleria_en(f.stem, corpo, m)))
    pagine = []
    for slug, meta, contenuto in sorgenti:
        lingua = meta.get("lingua", "it")
        contenuto = contenuto.replace("<!--ULTIMI_POST-->", ultimi_post(posts, lingua=lingua)).replace("<!--ELENCO_POST-->", elenco_post(posts))
        u = meta.get("url") or url_di(slug)
        html, url = render(layout, slug, meta, contenuto, lingua, alt.get(u))
        if meta.get("file"):
            dest = OUT / meta["file"]
        else:
            dest = OUT / url.strip("/") / "index.html" if url != "/" else OUT / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        pagine.append((url, meta))

    # redirect dai vecchi indirizzi WordPress
    for vecchio, nuovo in REDIRECT.items():
        d = OUT / vecchio.strip("/") / "index.html"
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(f'<!doctype html><meta charset="utf-8"><title>Reindirizzamento</title><link rel="canonical" href="{DOMINIO}{nuovo}">'
                     f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={nuovo}"><a href="{nuovo}">{DOMINIO}{nuovo}</a>', encoding="utf-8")

    # sitemap.xml + robots.txt + CNAME
    date_post = {f"/{m['slug']}/": m.get("date", "") for m, _ in posts}
    righe = [f"  <url><loc>{DOMINIO}{u}</loc>" + (f"<lastmod>{date_post[u]}</lastmod>" if date_post.get(u) else "") + "</url>"
             for u, m in pagine if not m.get("noindex") and not m.get("file")]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "\n".join(righe) + "\n</urlset>\n", encoding="utf-8")
    shutil.copy2(OUT / "sitemap.xml", OUT / "sitemap_index.xml")  # vecchio URL Yoast
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {DOMINIO}/sitemap.xml\n", encoding="utf-8")
    (OUT / "CNAME").write_text(DOMINIO.split("//")[1] + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    # media citati in html/css
    rif = set()
    for f in list(OUT.rglob("*.html")) + list(OUT.rglob("*.css")):
        rif |= set(re.findall(r"/media/[^\"')\s?#]+", f.read_text(encoding="utf-8")))
    mancanti = [r for r in sorted(rif) if not copia_media(r)]

    print(f"OK: {len(pagine)} pagine ({len(posts)} articoli), {len(rif)} file media" + (f", {len(mancanti)} mancanti" if mancanti else ""))


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import http.server, functools
        class NoCache(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                self.send_header("Cache-Control", "no-store, must-revalidate")
                super().end_headers()
        h = functools.partial(NoCache, directory=str(OUT))
        print("http://localhost:8790")
        http.server.ThreadingHTTPServer(("", 8790), h).serve_forever()
