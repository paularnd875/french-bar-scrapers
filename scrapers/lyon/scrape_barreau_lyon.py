#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper de l'annuaire du Barreau de Lyon -> CSV complet.

Recupere pour chaque avocat :
  nom_complet, nom, prenom, email, telephone, telephone_structure,
  site_web, structure, adresse, code_postal, ville, case,
  date_serment, annee_serment, specialisations, domaines_activite,
  langues, url_fiche

Source : https://www.barreaulyon.com/annuaire/  (~4160 avocats)

------------------------------------------------------------------------
POURQUOI LA PLUPART DES SCRAPERS NE TROUVENT QUE ~2600/4160
------------------------------------------------------------------------
L'annuaire affiche les avocats en ORDRE ALEATOIRE a chaque chargement.
Paginer ?paged=1..347 revient a tirer au hasard : statistiquement on ne
collecte ainsi que ~60-65% des fiches (probleme du collectionneur de
coupons). D'ou le plafond a ~2600.

Ce script regle ca : il enumere d'abord via le SITEMAP (liste complete
et deterministe). Si le sitemap echoue, il bascule sur une pagination
MULTI-PASSES qui boucle jusqu'a saturation. Un rapport de couverture
s'affiche a la fin.

Usage :
  pip3 install requests beautifulsoup4
  python3 scrape_barreau_lyon.py

Caracteristiques :
  - reprise auto (relance => reprend ou il s'est arrete)
  - ecriture incrementale (rien perdu si interruption)
  - rate-limit poli + retries
  - dedup par slug

Note RGPD : donnees publiques mais nominatives. Prospection B2B =>
base legale (interet legitime), information des personnes, droit
d'opposition (CNIL). A cadrer avant exploitation.
"""

import csv
import os
import re
import sys
import time
import random

import requests
from bs4 import BeautifulSoup

BASE = "https://www.barreaulyon.com"
LIST_URL = BASE + "/annuaire/?paged={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36"
}

OUT_CSV = "avocats_barreau_lyon.csv"
SLUGS_FILE = "slugs.txt"        # cache de la liste des fiches
DELAY = 0.6                     # secondes entre requetes (politesse)
MAX_PAGES = 400                 # garde-fou pagination
PAGINATION_PASSES = 6           # nb max de passes completes (fallback)
EXPECTED_MIN = 3800             # si moins, on complete par pagination

FIELDS = [
    "nom_complet", "nom", "prenom", "email", "telephone",
    "telephone_structure", "site_web", "structure", "adresse",
    "code_postal", "ville", "case", "date_serment", "annee_serment",
    "specialisations", "domaines_activite", "langues", "url_fiche",
]

SLUG_RE = re.compile(r"/annuaire/avocat/([a-z0-9\-]+)/?", re.I)
LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)
DISCLAIMER_BITS = (
    "certificat professionnel", "par l'ordre des avocats",
    "mention declarative", "sans controle", "specialisation",
    "domaines d'activite", "domaine d'activite",
)

# candidats de sitemap (WP core, Yoast, RankMath, generique)
SITEMAP_CANDIDATES = [
    "/wp-sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap.xml",
    "/sitemap-index.xml",
]


def get(url, tries=4, timeout=30):
    """GET avec retries + backoff."""
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                r.encoding = r.apparent_encoding or "utf-8"
                return r.text
            if r.status_code == 404:
                return None
        except requests.RequestException as e:
            print("  ! erreur %s: %s" % (url, e), file=sys.stderr)
        time.sleep(1.5 * (i + 1))
    return None


# ----------------------------------------------------------------------------
# Phase 1a : enumeration via sitemap (methode fiable)
# ----------------------------------------------------------------------------
def slugs_from_sitemaps():
    """Parcourt les sitemaps et renvoie les slugs d'avocats trouves."""
    seen_sitemaps = set()
    avocat_slugs = set()
    queue = []

    # trouver le(s) sitemap(s) racine
    for cand in SITEMAP_CANDIDATES:
        url = BASE + cand
        xml = get(url, timeout=30)
        if xml and "<loc>" in xml.lower():
            print("[sitemap] racine trouvee : %s" % url)
            queue.append(url)
            break

    if not queue:
        print("[sitemap] aucun sitemap racine accessible")
        return avocat_slugs

    while queue:
        sm = queue.pop()
        if sm in seen_sitemaps:
            continue
        seen_sitemaps.add(sm)
        xml = get(sm, timeout=30)
        if not xml:
            continue
        locs = LOC_RE.findall(xml)
        for loc in locs:
            low = loc.lower()
            # sous-sitemap a explorer
            if low.endswith(".xml") and "sitemap" in low:
                if loc not in seen_sitemaps:
                    queue.append(loc)
                continue
            # fiche avocat ?
            m = SLUG_RE.search(loc)
            if m:
                avocat_slugs.add(m.group(1))
        # petit indice de progression
        if locs:
            print("  %s -> %d <loc> (avocats cumules: %d)"
                  % (sm.split("/")[-1], len(locs), len(avocat_slugs)))
        time.sleep(0.3)

    print("[sitemap] %d slugs d'avocats trouves" % len(avocat_slugs))
    return avocat_slugs


# ----------------------------------------------------------------------------
# Phase 1b : pagination multi-passes (fallback anti-aleatoire)
# ----------------------------------------------------------------------------
def slugs_from_pagination(existing=None):
    slugs = set(existing or [])
    no_gain_passes = 0
    for p in range(1, PAGINATION_PASSES + 1):
        before = len(slugs)
        print("[pagination] passe %d/%d ..." % (p, PAGINATION_PASSES))
        for page in range(1, MAX_PAGES + 1):
            html = get(LIST_URL.format(page))
            if html is None:
                break
            found = set(SLUG_RE.findall(html))
            if not found:
                break
            slugs |= found
            time.sleep(DELAY)
        gained = len(slugs) - before
        print("  passe %d : +%d (total %d)" % (p, gained, len(slugs)))
        if gained == 0:
            no_gain_passes += 1
            if no_gain_passes >= 2:
                print("  2 passes sans gain -> saturation")
                break
        else:
            no_gain_passes = 0
    return slugs


def collect_slugs():
    if os.path.exists(SLUGS_FILE):
        with open(SLUGS_FILE, encoding="utf-8") as f:
            slugs = [l.strip() for l in f if l.strip()]
        if slugs:
            print("[slugs] %d slugs charges depuis %s" % (len(slugs), SLUGS_FILE))
            return slugs

    # 1) sitemap d'abord
    slugs = slugs_from_sitemaps()

    # 2) si couverture insuffisante, completer par pagination
    if len(slugs) < EXPECTED_MIN:
        print("[slugs] couverture sitemap faible (%d < %d) -> "
              "complement par pagination multi-passes"
              % (len(slugs), EXPECTED_MIN))
        slugs = slugs_from_pagination(existing=slugs)

    slugs = sorted(slugs)
    with open(SLUGS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(slugs))
    print("[slugs] TOTAL %d slugs uniques -> %s" % (len(slugs), SLUGS_FILE))
    return slugs


# ----------------------------------------------------------------------------
# Phase 2 : parser une fiche
# ----------------------------------------------------------------------------
def text_after_label(soup, label):
    """Renvoie la valeur qui suit un <strong>/<b> egal a `label`.

    Sur ce site la valeur est generalement dans le bloc *suivant* le label
    (ex: <p><strong>Structure</strong></p><p>R-AVOCAT</p>), parfois dans le
    meme bloc. On gere les deux cas.
    """
    lab_low = label.lower()
    for tag in soup.find_all(["strong", "b"]):
        if tag.get_text(strip=True).lower().rstrip(":") != lab_low:
            continue
        # cas 1 : valeur dans le meme parent, apres le label
        parent = tag.find_parent(["p", "div", "li", "td"]) or tag.parent
        full = parent.get_text(" ", strip=True)
        val = full.replace(tag.get_text(" ", strip=True), "", 1).strip(" : ")
        if val:
            return val
        # cas 2 : valeur dans un bloc suivant (en ordre document)
        node = parent
        for _ in range(12):
            node = node.find_next(["p", "div", "span", "li", "td"])
            if node is None:
                break
            t = node.get_text(" ", strip=True)
            if t and t.lower().rstrip(":") != lab_low:
                return t
    return ""


DISC_LINES = (
    "certificat professionnel", "par l'ordre des avocats",
    "mention declarative", "mention déclarative", "de l'ordre des avocats",
    "sans controle", "sans contrôle",
)


def _content_lines(soup):
    """Lignes de texte visibles, nettoyees, en ordre document."""
    out = []
    for l in soup.get_text("\n").split("\n"):
        l = re.sub(r"\s+", " ", l).strip()
        if l:
            out.append(l)
    return out


def extract_sections(soup):
    """Renvoie (specialisations, domaines_activite).

    Les valeurs de ces 2 sections sont des paragraphes (pas des <li>).
    On les delimite par leurs entetes ("Specialisation", "Domaines
    d'activite") et le pied de page ("Ordre des avocats"), en retirant
    les lignes d'avertissement (Certificat..., Mention declarative...).
    """
    lines = _content_lines(soup)
    low = [l.lower() for l in lines]

    def find(pred):
        for i, l in enumerate(low):
            if pred(l):
                return i
        return None

    i_spec = find(lambda l: l == "specialisation" or l == "spécialisation")
    i_dom = find(lambda l: l.startswith("domaines d'activ"))
    i_end = find(lambda l: l.startswith("ordre des avocats"))
    if i_end is None:
        i_end = len(lines)

    def collect(start, end):
        vals = []
        for i in range(start + 1, end):
            l, ll = lines[i], low[i]
            if any(d in ll for d in DISC_LINES):
                continue
            if l.startswith(".") or "fill:" in ll or l.startswith("http"):
                continue
            if ll in ("specialisation", "spécialisation"):
                continue
            if ll.startswith("domaines d'activ"):
                break
            vals.append(l)
        seen = []
        for v in vals:
            if v not in seen:
                seen.append(v)
        return ";".join(seen)

    spec = ""
    if i_spec is not None:
        spec_end = i_dom if (i_dom is not None and i_dom > i_spec) else i_end
        spec = collect(i_spec, spec_end)
    dom = collect(i_dom, i_end) if i_dom is not None else ""
    return spec, dom


def parse_fiche(html, url):
    soup = BeautifulSoup(html, "html.parser")
    rec = {k: "" for k in FIELDS}
    rec["url_fiche"] = url

    # Nom (h1)
    h1 = soup.find("h1")
    nom_complet = h1.get_text(" ", strip=True) if h1 else ""
    rec["nom_complet"] = nom_complet
    parts = nom_complet.split()
    nom = " ".join(p for p in parts if p.isupper() and len(p) > 1)
    prenom = " ".join(p for p in parts if not (p.isupper() and len(p) > 1))
    rec["nom"], rec["prenom"] = nom.strip(), prenom.strip()

    # Specialite annoncee dans le h2 "... avocat specialiste en ..."
    for h2 in soup.find_all("h2"):
        m = re.search(r"sp[eé]cialiste en\s+(.+)$",
                      h2.get_text(" ", strip=True), re.I)
        if m:
            raw = m.group(1)
            parts = [re.sub(r"\s+", " ", p).strip()
                     for p in re.split(r"[|\n;]+", raw)]
            rec["specialisations"] = ";".join(p for p in parts if p)
            break

    # Email(s)
    emails = []
    for a in soup.select('a[href^="mailto:"]'):
        e = a.get("href", "").split("mailto:")[-1].split("?")[0].strip()
        if e and e not in emails:
            emails.append(e)
    rec["email"] = ";".join(emails)

    # Telephones (on ignore le numero de l'Ordre)
    tels = []
    for a in soup.select('a[href^="tel:"]'):
        href = a.get("href", "")
        t = a.get_text(" ", strip=True)
        if "472606000" in href or "72 60 60 00" in t:
            continue
        if t and t not in tels:
            tels.append(t)
    if tels:
        rec["telephone"] = tels[0]
    if len(tels) > 1:
        rec["telephone_structure"] = tels[1]

    # Site web : lien externe hors barreaulyon / reseaux sociaux
    skip = ("barreaulyon.com", "youtube.", "facebook.", "linkedin.",
            "instagram.", "tiktok.", "google.", "avocat.fr", "prordv.com",
            "googletagmanager", "consultation.avocat", "/maps/")
    for a in soup.select('a[href^="http"]'):
        href = a.get("href", "")
        if any(s in href.lower() for s in skip):
            continue
        rec["site_web"] = href
        break

    # Champs labelises
    rec["structure"] = text_after_label(soup, "Structure")
    rec["adresse"] = text_after_label(soup, "Rue")
    cp_ville = text_after_label(soup, "Code postal")
    if cp_ville:
        mm = re.match(r"\s*(\d{5})\s+(.*)", cp_ville)
        if mm:
            rec["code_postal"] = mm.group(1)
            rec["ville"] = mm.group(2).strip()
        else:
            rec["ville"] = cp_ville
    rec["case"] = text_after_label(soup, "Case")
    rec["langues"] = text_after_label(soup, "Langues")

    serment = text_after_label(soup, "Prestation de serment")
    rec["date_serment"] = serment
    my = re.search(r"(\d{4})", serment)
    if my:
        rec["annee_serment"] = my.group(1)

    # Sections "Specialisation" et "Domaines d'activite" (paragraphes)
    spec_sec, dom_sec = extract_sections(soup)
    rec["domaines_activite"] = dom_sec
    # specialisations : le h2 est prioritaire ; sinon la section
    if not rec["specialisations"]:
        rec["specialisations"] = spec_sec

    return rec


# ----------------------------------------------------------------------------
# Orchestration avec reprise + rapport de couverture
# ----------------------------------------------------------------------------
def load_done():
    done = set()
    if os.path.exists(OUT_CSV):
        with open(OUT_CSV, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row.get("url_fiche"):
                    done.add(row["url_fiche"])
    return done


def main():
    # mode test : python3 scrape_barreau_lyon.py 1000  -> limite a N fiches
    limit = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        limit = int(sys.argv[1])
        print("[mode test] limite a %d fiches" % limit)

    slugs = collect_slugs()
    total_enumerated = len(slugs)
    if limit:
        slugs = slugs[:limit]

    done = load_done()
    print("[scrape] %d fiches deja faites, %d a traiter"
          % (len(done), len(slugs) - len([s for s in slugs
              if "%s/annuaire/avocat/%s/" % (BASE, s) in done])))

    ok = 0
    sans_email = 0
    new_file = not os.path.exists(OUT_CSV)
    with open(OUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()

        for i, slug in enumerate(slugs, 1):
            url = "%s/annuaire/avocat/%s/" % (BASE, slug)
            if url in done:
                continue
            html = get(url)
            if not html:
                print("  [%d/%d] %s: ECHEC" % (i, len(slugs), slug))
                continue
            rec = parse_fiche(html, url)
            w.writerow(rec)
            f.flush()
            ok += 1
            if not rec["email"]:
                sans_email += 1
            if i % 50 == 0:
                print("  [%d/%d] %s" % (i, len(slugs), rec["nom_complet"]))
            time.sleep(DELAY + random.uniform(0, 0.3))

    # rapport de couverture
    total = len(load_done())
    print("\n========== RAPPORT ==========")
    print("Avocats enumeres (total): %d" % total_enumerated)
    print("Slugs traites ce run    : %d" % len(slugs))
    print("Fiches dans le CSV      : %d" % total)
    print("Nouvelles ce run        : %d" % ok)
    print("Sans email ce run       : %d" % sans_email)
    print("CSV                     : %s" % os.path.abspath(OUT_CSV))
    if total_enumerated < EXPECTED_MIN:
        print("ATTENTION: enumeration < %d, couverture possiblement "
              "incomplete." % EXPECTED_MIN)
    print("=============================")


if __name__ == "__main__":
    main()
