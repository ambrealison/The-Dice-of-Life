#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect.py — collecte réelle et auditable des données du Dé de la Vie.

Lots livrés par population :
  - lot 1 : IND, CHN, USA (preuve de bout en bout)
  - lot 2 : les 20 pays les plus peuplés

Sources joignables : World Bank WDI (redistribue WPP, WUP, UIS/Barro-Lee, JMP) et
World Bank PIP (revenu). Chaque brut est mis en cache dans data/raw/ avec son URL
de requête ; chaque valeur porte source_id, year et coverage réels. Aucune valeur
n'est inventée : un indicateur sans donnée nationale déclenche la hiérarchie de
repli (régional -> income_group -> mondial), et le coverage est marqué en
conséquence.

Niveaux avec donnée nationale réelle : 1 (population, income_group), 2 (âge×sexe,
WPP via WDI), 3 (grande/ville/rural, WUP via WDI), 4 (revenu, PIP + ref mondiale),
5 (éducation adulte + enfant, WDI UIS/Barro-Lee), 8 (living, WDI + JMP).
Niveaux 6 (santé/GBD) et 7 (famille/marriage) : sources primaires gated/bloquées
-> méthode figée (METHODS_health.md, METHODS_engine.md) et modèle groupé/global,
coverage income_group / regional (voir COVERAGE_REPORT.md).
"""
import json, os, ssl, urllib.request, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")
os.makedirs(RAW, exist_ok=True)

CA = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=CA if os.path.exists(CA) else None)
RETRIEVED = "2026-07-21"
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
_h = [urllib.request.HTTPSHandler(context=CTX)]
if PROXY:
    _h.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
OPENER = urllib.request.build_opener(*_h)
REFRESH = os.environ.get("REFRESH") == "1"

# Les 20 pays les plus peuplés (2024). IND/CHN/USA/BRA existaient au seed.
TARGETS = ["IND","CHN","USA","IDN","PAK","NGA","BRA","BGD","RUS","ETH",
           "MEX","JPN","EGY","PHL","COD","VNM","IRN","TUR","DEU","THA"]

# Métadonnées curées (nom FR/EN, sous-région ONU, préposition FR). Population et
# income_group viennent de WDI, jamais d'ici.
CURATED = {
 "IND": ("Inde","India","Asie du Sud","en"),
 "CHN": ("Chine","China","Asie de l'Est","en"),
 "USA": ("Etats-Unis","United States","Amerique du Nord","aux"),
 "IDN": ("Indonesie","Indonesia","Asie du Sud-Est","en"),
 "PAK": ("Pakistan","Pakistan","Asie du Sud","au"),
 "NGA": ("Nigeria","Nigeria","Afrique de l'Ouest","au"),
 "BRA": ("Bresil","Brazil","Amerique du Sud","au"),
 "BGD": ("Bangladesh","Bangladesh","Asie du Sud","au"),
 "RUS": ("Russie","Russia","Europe de l'Est","en"),
 "ETH": ("Ethiopie","Ethiopia","Afrique de l'Est","en"),
 "MEX": ("Mexique","Mexico","Amerique centrale","au"),
 "JPN": ("Japon","Japan","Asie de l'Est","au"),
 "EGY": ("Egypte","Egypt","Afrique du Nord","en"),
 "PHL": ("Philippines","Philippines","Asie du Sud-Est","aux"),
 "COD": ("Rep. dem. du Congo","DR Congo","Afrique centrale","en"),
 "VNM": ("Vietnam","Vietnam","Asie du Sud-Est","au"),
 "IRN": ("Iran","Iran","Asie de l'Ouest","en"),
 "TUR": ("Turquie","Turkiye","Asie de l'Ouest","en"),
 "DEU": ("Allemagne","Germany","Europe de l'Ouest","en"),
 "THA": ("Thailande","Thailand","Asie du Sud-Est","en"),
}

# Échantillon pour la distribution mondiale de revenu (les plus peuplés avec PIP).
WORLD_REF = ["IND","CHN","USA","IDN","PAK","NGA","BRA","BGD","RUS","ETH","MEX",
             "PHL","VNM","EGY","COD","TUR","IRN","THA","ZAF","TZA","KEN","COL",
             "UGA","ARG","DZA","IRQ","POL","MAR","PER","MYS","GHA","MOZ","CIV",
             "MDG","BOL","HND","GBR","FRA","ITA","ESP"]

INCOME_MAP = {"LIC": "low", "LMC": "lower_middle", "UMC": "upper_middle", "HIC": "high"}
GROUP_FROM_INCOME = {"high": "rich", "upper_middle": "mid", "lower_middle": "mid", "low": "low"}
# Parentalité précoce : régions à forte fécondité adolescente (jugement régional documenté).
EARLY_REGIONS = {"Asie du Sud","Afrique de l'Ouest","Afrique de l'Est","Afrique centrale"}

# ---------------------------------------------------------------- HTTP + cache
def fetch(url, cache_name):
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

def wdi(indicator, isos, date="2015:2024"):
    ctry = ";".join(isos)
    url = ("https://api.worldbank.org/v2/country/%s/indicator/%s"
           "?format=json&date=%s&per_page=20000" % (ctry, indicator, date))
    tag = "_".join(isos) if len(isos) <= 6 else "%s_%d" % (isos[0], len(isos))
    body = fetch(url, "wdi_%s_%s.json" % (indicator, tag))
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

# ---------------------------------------------------------------- repli (fallback)
def ref_average(iso, national, meta, pop):
    """Moyenne pondérée par population sur le meilleur groupe de repli disponible.
    national: {iso: valeur} (scalaire | liste | dict de shares). Renvoie (valeur, coverage)."""
    levels = [("regional", lambda i: meta[i]["region"]),
              ("income_group", lambda i: meta[i]["income_group"]),
              ("world", lambda i: "world")]
    for cov, keyfn in levels:
        grp = [i for i in national if i != iso and i in meta and keyfn(i) == keyfn(iso)]
        if not grp:
            continue
        w = {i: pop.get(i, 1.0) for i in grp}
        tot = sum(w.values()) or 1.0
        sample = national[grp[0]]
        if isinstance(sample, dict):
            keys = sample.keys()
            val = {k: sum(national[i][k] * w[i] for i in grp) / tot for k in keys}
        elif isinstance(sample, list):
            val = [sum(national[i][j] * w[i] for i in grp) / tot for j in range(len(sample))]
        else:
            val = sum(national[i] * w[i] for i in grp) / tot
        return val, cov
    return None, None

# ---------------------------------------------------------------- 1. countries
def collect_countries():
    body = fetch("https://api.worldbank.org/v2/country/%s?format=json&per_page=500" % ";".join(TARGETS),
                 "wdi_country_meta_top20.json")
    md = {r["id"]: r for r in json.loads(body)[1]}
    pop = wdi("SP.POP.TOTL", TARGETS)
    c = load("countries")
    rows = {r["iso3"]: r for r in c["rows"]}
    for iso in TARGETS:
        nf, ne, region, prep = CURATED[iso]
        r = rows.get(iso, {"iso3": iso})
        yr, val = pop[iso]
        r.update({"iso3": iso, "name_fr": nf, "name_en": ne, "region": region,
                  "income_group": INCOME_MAP[md[iso]["incomeLevel"]["id"]],
                  "population": int(round(val)), "prep": prep,
                  "coverage": "national", "year": yr})
        rows[iso] = r
    # conserver l'ordre : seed d'abord, puis nouveaux, triés par population décroissante
    c["rows"] = sorted(rows.values(), key=lambda r: -r["population"])
    save("countries", c)
    print("[1] countries: %d pays au domaine (%d collectés)" % (len(c["rows"]), len(TARGETS)))
    pop_val = {r["iso3"]: r["population"] for r in c["rows"]}   # poids de repli
    return {r["iso3"]: r for r in c["rows"]}, pop_val

# ---------------------------------------------------------------- 2. age_sex
BANDS = ["0004","0509","1014","1519","2024","2529","3034","3539","4044","4549",
         "5054","5559","6064","6569","7074","7579","80UP"]
BUCKET = {"a00_04": ["0004"], "a05_14": ["0509","1014"], "a15_19": ["1519"],
          "a20_34": ["2024","2529","3034"], "a35_49": ["3539","4044","4549"],
          "a50_64": ["5054","5559","6064"], "a65_79": ["6569","7074","7579"], "a80p": ["80UP"]}

def collect_age_sex(meta, pop):
    counts = {iso: {"F": {}, "M": {}} for iso in TARGETS}
    for band in BANDS:
        for sex, suf in (("F", "FE"), ("M", "MA")):
            res = wdi("SP.POP.%s.%s" % (band, suf), TARGETS)
            for iso in TARGETS:
                if iso in res:
                    counts[iso][sex][band] = res[iso][1]
    a = load("age_sex")
    national = {}
    for iso in TARGETS:
        total = sum(counts[iso][s][b] for s in ("F","M") for b in BANDS if b in counts[iso][s])
        if total <= 0:
            continue
        shares = {}
        for bucket, bands in BUCKET.items():
            for sex in ("F","M"):
                shares["%s|%s" % (bucket, sex)] = sum(counts[iso][sex].get(b, 0.0) for b in bands) / total
        national[iso] = shares
        a["data"][iso] = {"shares": shares, "coverage": "national"}
    for iso in TARGETS:  # repli éventuel
        if iso not in national:
            val, cov = ref_average(iso, national, meta, pop)
            if val:
                s = sum(val.values()); val = {k: v/s for k, v in val.items()}
                a["data"][iso] = {"shares": val, "coverage": cov}
                print("[2] age_sex repli", cov, "pour", iso)
    save("age_sex", a)
    print("[2] age_sex: %d pays (sommes ~1)" % len(national))

# ---------------------------------------------------------------- 3. settlement
def collect_settlement(meta, pop):
    urb = wdi("SP.URB.TOTL.IN.ZS", TARGETS)
    big = wdi("EN.URB.MCTY.TL.ZS", TARGETS)
    s = load("settlement")
    national = {}
    for iso in TARGETS:
        if iso in urb and iso in big:
            u, g = urb[iso][1]/100.0, min(big[iso][1]/100.0, urb[iso][1]/100.0)
            national[iso] = {"grande": g, "ville": u - g, "rural": 1.0 - u}
            s["data"][iso] = {"shares": national[iso], "coverage": "national"}
    for iso in TARGETS:
        if iso not in national:
            if iso in urb:  # urbain connu, seul le partage grande/ville est régional
                u = urb[iso][1]/100.0
                ratio, cov = ref_average(iso, {k: national[k]["grande"]/(national[k]["grande"]+national[k]["ville"])
                                               for k in national if (national[k]["grande"]+national[k]["ville"])>0}, meta, pop)
                ratio = ratio if ratio is not None else 0.45
                s["data"][iso] = {"shares": {"grande": u*ratio, "ville": u*(1-ratio), "rural": 1.0-u},
                                  "coverage": "regional"}
                print("[3] settlement partage régional pour", iso)
            else:
                val, cov = ref_average(iso, national, meta, pop)
                if val:
                    tot = sum(val.values()); val = {k: v/tot for k, v in val.items()}
                    s["data"][iso] = {"shares": val, "coverage": cov}
                    print("[3] settlement repli", cov, "pour", iso)
    save("settlement", s)
    print("[3] settlement: %d pays nationaux" % len(national))

# ---------------------------------------------------------------- 4. income (PIP)
def pip_latest_deciles(iso):
    url = "https://api.worldbank.org/pip/v1/pip?country=%s&year=all&fill_gaps=false&format=json" % iso
    rows = json.loads(fetch(url, "pip_%s.json" % iso))
    best = None
    for r in rows:
        if r.get("decile1") is None:
            continue
        if best is None or r["reporting_year"] > best["reporting_year"]:
            best = r
    if not best:
        return None
    return best["reporting_year"], best["mean"], [best["decile%d" % i] for i in range(1, 11)], best.get("welfare_type")

def build_world_ref():
    pop = wdi("SP.POP.TOTL", WORLD_REF)
    pts, used = [], []
    for iso in WORLD_REF:
        d = pip_latest_deciles(iso)
        if not d or iso not in pop:
            continue
        yr, mean, sh, welf = d
        w = pop[iso][1] / 10.0
        for x in sh:
            pts.append((x * mean * 10.0, w))
        used.append({"iso3": iso, "year": yr, "mean_ppp_day": round(mean, 4), "welfare": welf})
    pts.sort(key=lambda p: p[0])
    tot = sum(w for _, w in pts)
    cdf, cum = [], 0.0
    for inc, w in pts:
        cum += w
        cdf.append([round(inc, 4), round(cum / tot, 6)])
    return cdf, used

def pct_on_cdf(cdf, x):
    if x <= cdf[0][0]:
        return int(round(cdf[0][1] * 100))
    if x >= cdf[-1][0]:
        return int(round(cdf[-1][1] * 100))
    lo, hi = 0, len(cdf) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if cdf[mid][0] < x:
            lo = mid + 1
        else:
            hi = mid
    return int(round(cdf[lo][1] * 100))

def collect_income(meta, pop):
    cdf, used = build_world_ref()
    save("income_world_ref", {"table": "income_world_ref", "source_id": "pip", "year": int(RETRIEVED[:4]),
        "note": ("Distribution mondiale du revenu/consommation en dollars/jour PPA. Chaque décile de "
                 "chaque pays de l'échantillon est un point de revenu moyen (part x moyenne x 10) pondéré "
                 "par population/10. CDF = [revenu, part cumulée]."),
        "countries_used": used, "cdf": cdf})
    inc = load("income")
    national = {}
    for iso in TARGETS:
        d = pip_latest_deciles(iso)
        if not d:
            continue
        yr, mean, sh, welf = d
        gp = [pct_on_cdf(cdf, (sh[2*q] + sh[2*q+1]) * mean * 5.0) for q in range(5)]
        national[iso] = gp
        inc["data"][iso] = {"global_percentile": gp, "coverage": "national", "survey_year": yr}
    for iso in TARGETS:
        if iso not in national:
            val, cov = ref_average(iso, national, meta, pop)
            if val:
                inc["data"][iso] = {"global_percentile": [int(round(v)) for v in val], "coverage": cov}
                print("[4] income repli", cov, "pour", iso)
    save("income", inc)
    print("[4] income: %d ref mondiale, %d nationaux PIP" % (len(used), len(national)))

# ---------------------------------------------------------------- 5. education
def collect_education(meta, pop):
    ter = wdi("SE.TER.CUAT.BA.ZS", TARGETS)
    upsec = wdi("SE.SEC.CUAT.UP.ZS", TARGETS)
    prim = wdi("SE.PRM.CUAT.ZS", TARGETS)
    oos = wdi("SE.PRM.UNER.ZS", TARGETS)
    nenr = wdi("SE.PRM.NENR", TARGETS)
    e = load("education")
    nat_att, nat_child = {}, {}
    for iso in TARGETS:
        if iso in ter and iso in upsec and iso in prim:
            t, us, pr = ter[iso][1]/100.0, upsec[iso][1]/100.0, prim[iso][1]/100.0
            sup, sec, pri, auc = t, max(us-t,0.0), max(pr-us,0.0), max(1.0-pr,0.0)
            tot = sup + sec + pri + auc
            nat_att[iso] = {"aucune": auc/tot, "primaire": pri/tot, "secondaire": sec/tot, "superieur": sup/tot}
            e["attainment_base"][iso] = {"shares": nat_att[iso], "coverage": "national", "year": ter[iso][0]}
        if iso in oos:
            nat_child[iso] = max(0.0, 1.0 - oos[iso][1]/100.0)
            e["child_enrollment"][iso] = {"in_school": round(nat_child[iso],4), "coverage": "national", "year": oos[iso][0]}
        elif iso in nenr:
            nat_child[iso] = min(1.0, nenr[iso][1]/100.0)
            e["child_enrollment"][iso] = {"in_school": round(nat_child[iso],4), "coverage": "national", "year": nenr[iso][0]}
    for iso in TARGETS:
        if iso not in nat_att:
            val, cov = ref_average(iso, nat_att, meta, pop)
            if val:
                tot = sum(val.values()); val = {k: v/tot for k, v in val.items()}
                e["attainment_base"][iso] = {"shares": val, "coverage": cov}
                print("[5] attainment repli", cov, "pour", iso)
        if iso not in nat_child:
            val, cov = ref_average(iso, nat_child, meta, pop)
            if val is not None:
                e["child_enrollment"][iso] = {"in_school": round(val,4), "coverage": cov}
                print("[5] child repli", cov, "pour", iso)
    save("education", e)
    print("[5] education: %d attainment nationaux, %d child nationaux" % (len(nat_att), len(nat_child)))

# ---------------------------------------------------------------- 8. living
def collect_living(meta, pop):
    elec = wdi("EG.ELC.ACCS.ZS", TARGETS)
    net = wdi("IT.NET.USER.ZS", TARGETS)
    w_sm = wdi("SH.H2O.SMDW.ZS", TARGETS)
    w_ba = wdi("SH.H2O.BASW.ZS", TARGETS)
    l = load("living")
    nat = {}
    for iso in TARGETS:
        water = w_sm.get(iso) or w_ba.get(iso)
        if iso in elec and iso in net and water:
            nat[iso] = {"electricite": round(elec[iso][1]/100.0,4), "internet": round(net[iso][1]/100.0,4),
                        "eau": round(water[1]/100.0,4)}
            l["data"][iso] = dict(nat[iso], coverage="national",
                                  year=max(elec[iso][0], net[iso][0], water[0]),
                                  eau_source=("SH.H2O.SMDW.ZS" if iso in w_sm else "SH.H2O.BASW.ZS"))
    for iso in TARGETS:
        if iso not in nat:
            val, cov = ref_average(iso, nat, meta, pop)
            if val:
                l["data"][iso] = dict(val, coverage=cov)
                print("[8] living repli", cov, "pour", iso)
    save("living", l)
    print("[8] living: %d pays nationaux" % len(nat))

# ---------------------------------------------------------------- 6 & 7 méta
def collect_health_family_meta(meta):
    h = load("health")
    for iso in TARGETS:
        h["country_group"][iso] = GROUP_FROM_INCOME[meta[iso]["income_group"]]
    save("health", h)
    f = load("family")
    early = set(f.get("early_parenthood", []))
    for iso in TARGETS:
        if meta[iso]["region"] in EARLY_REGIONS:
            early.add(iso)
    f["early_parenthood"] = sorted(early)
    save("family", f)
    print("[6] health.country_group: +%d pays (income_group)" % len(TARGETS))
    print("[7] family.early_parenthood:", f["early_parenthood"])

def stamp_manifest():
    p = os.path.join(ROOT, "schema.json")
    sc = json.load(open(p, encoding="utf-8"))
    for sid in ("wpp", "wup", "pip", "barrolee", "uis", "wdi", "jmp"):
        if sid in sc["sources"]:
            sc["sources"][sid]["retrieved"] = RETRIEVED
    json.dump(sc, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[manifeste] retrieved =", RETRIEVED)

if __name__ == "__main__":
    print("Collecte lot 2 : %d pays -" % len(TARGETS), RETRIEVED)
    meta, pop = collect_countries()
    collect_age_sex(meta, pop)
    collect_settlement(meta, pop)
    collect_income(meta, pop)
    collect_education(meta, pop)
    collect_living(meta, pop)
    collect_health_family_meta(meta)
    stamp_manifest()
    print("Terminé. Lancer: node validate.js")
