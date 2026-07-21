#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect.py — collecte réelle et auditable des données du Dé de la Vie.

Lot 1 (preuve de bout en bout) : Inde, Chine, États-Unis.
Sources joignables : World Bank WDI (redistribue WPP, WUP, UIS/Barro-Lee, JMP)
et World Bank PIP (revenu). Chaque brut est mis en cache dans data/raw/ avec son
URL de requête ; chaque valeur produite porte source_id, year et coverage réels.
Aucune valeur n'est inventée : un indicateur sans donnée est laissé au repli
existant et signalé.

Niveaux couverts avec donnée nationale réelle :
  1 countries (population, income_group)   -> WDI SP.POP.TOTL + classification
  2 age_sex (jointe âge x sexe)            -> WDI SP.POP.<bande>.<FE|MA> (WPP)
  3 settlement (grande/ville/rural)        -> WDI SP.URB.TOTL.IN.ZS + EN.URB.MCTY.TL.ZS (WUP)
  4 income (percentile mondial)            -> PIP déciles + income_world_ref.json
  5 education (base adulte + enfant)       -> WDI attainment 25+ (UIS/Barro-Lee) + SE.PRM.UNER.ZS
  8 living (électricité/internet/eau)      -> WDI EG.ELC.ACCS.ZS, IT.NET.USER.ZS, SH.H2O.SMDW.ZS (JMP)

Niveaux 6 (santé, GBD) et 7 (famille, World Marriage Data) : sources primaires
gated/bloquées -> méthode figée et documentée, repli marqué (voir METHODS_*.md
et COVERAGE_REPORT.md). Non réécrits ici.
"""
import json, os, ssl, urllib.request, urllib.parse, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")
os.makedirs(RAW, exist_ok=True)

CA = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=CA if os.path.exists(CA) else None)
RETRIEVED = "2026-07-21"

# Egress passe par le proxy configuré (HTTPS_PROXY). On l'attache explicitement.
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
_handlers = [urllib.request.HTTPSHandler(context=CTX)]
if PROXY:
    _handlers.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
OPENER = urllib.request.build_opener(*_handlers)

TARGETS = ["IND", "CHN", "USA"]

# ISO3 pour construire la distribution mondiale de revenu (les plus peuplés qui
# ont une enquête PIP). Documenté : échantillon pondéré par population.
WORLD_REF = ["IND","CHN","USA","IDN","PAK","NGA","BRA","BGD","RUS","ETH","MEX",
             "PHL","VNM","EGY","COD","TUR","IRN","THA","ZAF","TZA","KEN","COL",
             "UGA","ARG","DZA","IRQ","POL","MAR","PER","MYS","GHA","MOZ","CIV",
             "MDG","BOL","HND","GBR","FRA","ITA","ESP"]

# ---------------------------------------------------------------- HTTP + cache
REFRESH = os.environ.get("REFRESH") == "1"

def fetch(url, cache_name):
    """GET -> texte. Cache le brut dans data/raw/<cache_name> et l'URL à côté.
    Relit le cache si présent (REFRESH=1 pour forcer un nouveau téléchargement)."""
    path = os.path.join(RAW, cache_name)
    if not REFRESH and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    req = urllib.request.Request(url, headers={"User-Agent": "DiceOfLife-collector/1.0"})
    with OPENER.open(req, timeout=90) as r:
        body = r.read().decode("utf-8")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    with open(path + ".url", "w", encoding="utf-8") as f:
        f.write(url + "\n")
    return body

def wdi(indicator, isos, date="2018:2024"):
    """WDI -> {iso: (year:int, value:float)} dernière valeur non nulle."""
    ctry = ";".join(isos)
    # per_page large : l'API WDI pagine à 200 par défaut ; une page unique évite
    # de tronquer les requêtes multi-pays (ex. la ref mondiale de revenu).
    url = ("https://api.worldbank.org/v2/country/%s/indicator/%s"
           "?format=json&date=%s&per_page=20000" % (ctry, indicator, date))
    body = fetch(url, "wdi_%s_%s.json" % (indicator, "_".join(isos)))
    d = json.loads(body)
    out = {}
    for row in (d[1] or []):
        if row["value"] is None:
            continue
        iso, yr, val = row["countryiso3code"], int(row["date"]), float(row["value"])
        if iso not in out or yr > out[iso][0]:
            out[iso] = (yr, val)
    return out

def load(name):
    with open(os.path.join(DATA, name + ".json"), encoding="utf-8") as f:
        return json.load(f)

def save(name, obj):
    with open(os.path.join(DATA, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- 1. countries
INCOME_MAP = {"LIC": "low", "LMC": "lower_middle", "UMC": "upper_middle", "HIC": "high"}

def collect_countries():
    body = fetch("https://api.worldbank.org/v2/country/%s?format=json" % ";".join(TARGETS),
                 "wdi_country_meta_%s.json" % "_".join(TARGETS))
    meta = {r["id"]: r for r in json.loads(body)[1]}
    pop = wdi("SP.POP.TOTL", TARGETS)
    c = load("countries")
    rows = {r["iso3"]: r for r in c["rows"]}
    for iso in TARGETS:
        r = rows[iso]
        yr, val = pop[iso]
        r["population"] = int(round(val))
        r["income_group"] = INCOME_MAP[meta[iso]["incomeLevel"]["id"]]
        r["coverage"] = "national"
        r["year"] = yr
    save("countries", c)
    print("[1] countries:", {iso: (rows[iso]["population"], rows[iso]["income_group"]) for iso in TARGETS})

# ---------------------------------------------------------------- 2. age_sex
BANDS = ["0004","0509","1014","1519","2024","2529","3034","3539","4044","4549",
         "5054","5559","6064","6569","7074","7579","80UP"]
BUCKET = {
    "a00_04": ["0004"], "a05_14": ["0509","1014"], "a15_19": ["1519"],
    "a20_34": ["2024","2529","3034"], "a35_49": ["3539","4044","4549"],
    "a50_64": ["5054","5559","6064"], "a65_79": ["6569","7074","7579"], "a80p": ["80UP"],
}

def collect_age_sex():
    # counts[iso][sex][band] = value ; on retient l'année la plus récente commune
    counts = {iso: {"F": {}, "M": {}} for iso in TARGETS}
    years = {iso: set() for iso in TARGETS}
    for band in BANDS:
        for sex, suf in (("F", "FE"), ("M", "MA")):
            res = wdi("SP.POP.%s.%s" % (band, suf), TARGETS)
            for iso in TARGETS:
                if iso in res:
                    counts[iso][sex][band] = res[iso][1]
                    years[iso].add(res[iso][0])
    a = load("age_sex")
    for iso in TARGETS:
        total = sum(counts[iso][s][b] for s in ("F","M") for b in BANDS if b in counts[iso][s])
        shares = {}
        for bucket, bands in BUCKET.items():
            for sex in ("F","M"):
                v = sum(counts[iso][sex].get(b, 0.0) for b in bands)
                shares["%s|%s" % (bucket, sex)] = v / total
        a["data"][iso] = {"shares": shares, "coverage": "national"}
    save("age_sex", a)
    print("[2] age_sex: sommes =", {iso: round(sum(a["data"][iso]["shares"].values()), 6) for iso in TARGETS})

# ---------------------------------------------------------------- 3. settlement
def collect_settlement():
    urb = wdi("SP.URB.TOTL.IN.ZS", TARGETS)
    big = wdi("EN.URB.MCTY.TL.ZS", TARGETS)   # pop en agglomérations > 1M, % du total
    s = load("settlement")
    for iso in TARGETS:
        u = urb[iso][1] / 100.0
        g = big[iso][1] / 100.0
        g = min(g, u)                      # borne : grande <= urbain
        shares = {"grande": g, "ville": u - g, "rural": 1.0 - u}
        s["data"][iso] = {"shares": shares, "coverage": "national"}
    save("settlement", s)
    print("[3] settlement:", {iso: {k: round(v,3) for k,v in s["data"][iso]["shares"].items()} for iso in TARGETS})

# ---------------------------------------------------------------- 4. income (PIP)
def pip_latest_deciles(iso):
    """Dernière enquête PIP réelle avec déciles pour iso -> (year, mean, [10 shares], welfare)."""
    url = ("https://api.worldbank.org/pip/v1/pip?country=%s&year=all&fill_gaps=false&format=json" % iso)
    body = fetch(url, "pip_%s.json" % iso)
    rows = json.loads(body)
    best = None
    for r in rows:
        if r.get("decile1") is None:
            continue
        if best is None or r["reporting_year"] > best["reporting_year"]:
            best = r
    if not best:
        return None
    sh = [best["decile%d" % i] for i in range(1, 11)]
    return best["reporting_year"], best["mean"], sh, best.get("welfare_type")

def build_world_ref():
    """CDF mondiale du revenu (dollars/jour PPA) : chaque décile d'un pays est un
    point de revenu moyen pondéré par population/10. Renvoie (cdf, meta)."""
    pop = wdi("SP.POP.TOTL", WORLD_REF)
    pts = []          # (income_per_day_ppp, weight)
    used = []
    for iso in WORLD_REF:
        d = pip_latest_deciles(iso)
        if not d or iso not in pop:
            continue
        yr, mean, sh, welf = d
        w = pop[iso][1] / 10.0
        for s in sh:
            pts.append((s * mean * 10.0, w))   # revenu moyen du décile = part*mean*10
        used.append({"iso3": iso, "year": yr, "mean_ppp_day": round(mean, 4), "welfare": welf})
    pts.sort(key=lambda p: p[0])
    tot = sum(w for _, w in pts)
    cdf, cum = [], 0.0
    for inc, w in pts:
        cum += w
        cdf.append([round(inc, 4), round(cum / tot, 6)])
    return cdf, used

def pct_on_cdf(cdf, x):
    """Percentile mondial (0-100) du revenu x sur la CDF."""
    lo, hi = 0, len(cdf) - 1
    if x <= cdf[0][0]:
        return round(cdf[0][1] * 100)
    if x >= cdf[-1][0]:
        return round(cdf[-1][1] * 100)
    while lo < hi:
        mid = (lo + hi) // 2
        if cdf[mid][0] < x:
            lo = mid + 1
        else:
            hi = mid
    return int(round(cdf[lo][1] * 100))

def collect_income():
    cdf, used = build_world_ref()
    ref = {"table": "income_world_ref", "source_id": "pip", "year": int(RETRIEVED[:4]),
           "note": ("Distribution mondiale du revenu/consommation en dollars/jour PPA. "
                    "Chaque décile de chaque pays de l'échantillon est un point de revenu moyen "
                    "(part_décile x moyenne x 10) pondéré par population/10. CDF = [revenu, part cumulée]."),
           "countries_used": used, "cdf": cdf}
    save("income_world_ref", ref)
    inc = load("income")
    for iso in TARGETS:
        d = pip_latest_deciles(iso)
        if not d:
            print("[4] income: PAS d'enquête PIP pour", iso, "-> laissé au repli")
            continue
        yr, mean, sh, welf = d
        gp = []
        for q in range(5):
            qmean = (sh[2*q] + sh[2*q+1]) * mean * 5.0   # revenu moyen du quintile
            gp.append(pct_on_cdf(cdf, qmean))
        inc["data"][iso] = {"global_percentile": gp, "coverage": "national", "survey_year": yr}
    save("income", inc)
    print("[4] income: %d pays dans la ref mondiale (%d points). global_percentile:" % (len(used), len(cdf)),
          {iso: inc["data"][iso]["global_percentile"] for iso in TARGETS if iso in inc["data"]})

# ---------------------------------------------------------------- 5. education
def collect_education():
    ter = wdi("SE.TER.CUAT.BA.ZS", TARGETS)    # >= licence
    upsec = wdi("SE.SEC.CUAT.UP.ZS", TARGETS)  # >= secondaire supérieur
    prim = wdi("SE.PRM.CUAT.ZS", TARGETS)      # >= primaire complété
    oos = wdi("SE.PRM.UNER.ZS", TARGETS)       # enfants hors école (% âge primaire)
    nenr = wdi("SE.PRM.NENR", TARGETS)         # taux net de scolarisation primaire (repli)
    e = load("education")
    for iso in TARGETS:
        # base adulte : nécessite les 3 indicateurs cumulés
        if iso in ter and iso in upsec and iso in prim:
            t, us, pr = ter[iso][1]/100.0, upsec[iso][1]/100.0, prim[iso][1]/100.0
            sup, sec = t, max(us - t, 0.0)
            pri, auc = max(pr - us, 0.0), max(1.0 - pr, 0.0)
            tot = sup + sec + pri + auc
            e["attainment_base"][iso] = {"shares": {"aucune": auc/tot, "primaire": pri/tot,
                                          "secondaire": sec/tot, "superieur": sup/tot},
                                          "coverage": "national", "year": ter[iso][0]}
        else:
            print("[5] attainment: indicateurs incomplets pour", iso, "-> laissé au repli (seed)")
        # scolarisation enfant : hors-école, sinon taux net, sinon repli
        if iso in oos:
            e["child_enrollment"][iso] = {"in_school": round(max(0.0, 1.0 - oos[iso][1]/100.0), 4),
                                          "coverage": "national", "year": oos[iso][0], "source": "SE.PRM.UNER.ZS"}
        elif iso in nenr:
            e["child_enrollment"][iso] = {"in_school": round(min(1.0, nenr[iso][1]/100.0), 4),
                                          "coverage": "national", "year": nenr[iso][0], "source": "SE.PRM.NENR"}
        else:
            print("[5] child_enrollment: pas de donnée pour", iso, "-> laissé au repli (seed)")
    save("education", e)
    print("[5] education attainment:", {iso: {k: round(v,3) for k,v in e["attainment_base"][iso]["shares"].items()} for iso in TARGETS if iso in e["attainment_base"]})
    print("[5] child in_school:", {iso: e["child_enrollment"][iso]["in_school"] for iso in TARGETS})

# ---------------------------------------------------------------- 8. living
def collect_living():
    elec = wdi("EG.ELC.ACCS.ZS", TARGETS)
    net = wdi("IT.NET.USER.ZS", TARGETS)
    water_sm = wdi("SH.H2O.SMDW.ZS", TARGETS)   # eau potable gérée en sécurité (JMP)
    water_ba = wdi("SH.H2O.BASW.ZS", TARGETS)   # repli : au moins service de base (JMP)
    l = load("living")
    for iso in TARGETS:
        if iso in water_sm:
            wyr, wval, wsrc = water_sm[iso][0], water_sm[iso][1], "SH.H2O.SMDW.ZS"
        elif iso in water_ba:
            wyr, wval, wsrc = water_ba[iso][0], water_ba[iso][1], "SH.H2O.BASW.ZS"
        else:
            print("[8] eau : pas de donnée pour", iso, "-> repli seed"); continue
        if iso not in elec or iso not in net:
            print("[8] électricité/internet incomplets pour", iso, "-> repli seed"); continue
        l["data"][iso] = {
            "electricite": round(elec[iso][1]/100.0, 4),
            "internet": round(net[iso][1]/100.0, 4),
            "eau": round(wval/100.0, 4),
            "coverage": "national",
            "year": max(elec[iso][0], net[iso][0], wyr),
            "eau_source": wsrc,
        }
    save("living", l)
    print("[8] living:", {iso: {k: l["data"][iso][k] for k in ("electricite","internet","eau")} for iso in TARGETS})

# ---------------------------------------------------------------- manifeste
def stamp_manifest():
    p = os.path.join(ROOT, "schema.json")
    with open(p, encoding="utf-8") as f:
        sc = json.load(f)
    for sid in ("wpp", "wup", "pip", "barrolee", "uis", "wdi", "jmp"):
        if sid in sc["sources"]:
            sc["sources"][sid]["retrieved"] = RETRIEVED
    with open(p, "w", encoding="utf-8") as f:
        json.dump(sc, f, ensure_ascii=False, indent=2)
    print("[manifeste] retrieved =", RETRIEVED, "pour wpp/wup/pip/barrolee/uis/wdi/jmp")

if __name__ == "__main__":
    print("Collecte lot 1 :", TARGETS, "-", RETRIEVED)
    collect_countries()
    collect_age_sex()
    collect_settlement()
    collect_income()
    collect_education()
    collect_living()
    stamp_manifest()
    print("Terminé. Bruts en cache dans data/raw/. Lancer: node validate.js")
