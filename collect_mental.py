#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_mental.py — prévalence nationale des troubles mentaux par pays × âge × sexe
(GBD 2023, IHME ; requête A « santé mentale » fournie par l'utilisateur).

Brut : data/raw/gbd_mental_2021.csv (Prevalence, Percent, 2021, causes 558 Mental
disorders + 973 Substance use disorders, 23 pays, groupes 5 ans, F/M).

Combine « au moins un trouble mental ou addictif » = 1 − (1−p_558)(1−p_973), puis
agrège les groupes 5 ans du GBD vers les 8 buckets d'âge, pondéré par la population
(WDI SP.POP.<bande>.<sexe>). Écrit health.mental_prevalence[iso][age][sexe].

Les 4 bandes de sévérité PHYSIQUE restent sur le modèle groupé (coverage
income_group) — voir METHODS_health.md ; requête B (YLDs) à venir.
"""
import csv, os, glob, json
from collect import load, save, RAW

CSV = os.path.join(RAW, "gbd_mental_2021.csv")

def cached_band_pop(band, suf):
    """Effectifs {iso:(yr,val)} pour SP.POP.<band>.<suf> depuis les bruts déjà en
    cache (aucun réseau). Fusionne tous les fichiers wdi_SP.POP.<band>.<suf>_*.json."""
    out = {}
    for f in glob.glob(os.path.join(RAW, "wdi_SP.POP.%s.%s_*.json" % (band, suf))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for r in (d[1] or []):
            if r["value"] is None:
                continue
            iso, yr, v = r["countryiso3code"], int(r["date"]), float(r["value"])
            if iso not in out or yr > out[iso][0]:
                out[iso] = (yr, v)
    return out

GBD2ISO = {
    "Austria":"AUT","Bangladesh":"BGD","Brazil":"BRA","China":"CHN",
    "Democratic Republic of the Congo":"COD","Egypt":"EGY","Ethiopia":"ETH",
    "France":"FRA","Germany":"DEU","India":"IND","Indonesia":"IDN",
    "Iran (Islamic Republic of)":"IRN","Japan":"JPN","Mexico":"MEX","Niger":"NER",
    "Nigeria":"NGA","Pakistan":"PAK","Philippines":"PHL","Russian Federation":"RUS",
    "Thailand":"THA","Türkiye":"TUR","United States of America":"USA","Viet Nam":"VNM",
}
# groupe d'âge GBD -> (bucket schéma, bande WDI d'effectifs)
AGE2 = {
    "<5 years":       ("a00_04","0004"),
    "5-9 years":      ("a05_14","0509"), "10-14 years": ("a05_14","1014"),
    "15-19 years":    ("a15_19","1519"),
    "20-24 years":    ("a20_34","2024"), "25-29 years": ("a20_34","2529"), "30-34 years": ("a20_34","3034"),
    "35-39 years":    ("a35_49","3539"), "40-44 years": ("a35_49","4044"), "45-49 years": ("a35_49","4549"),
    "50-54 years":    ("a50_64","5054"), "55-59 years": ("a50_64","5559"), "60-64 years": ("a50_64","6064"),
    "65-69 years":    ("a65_79","6569"), "70-74 years": ("a65_79","7074"), "75-79 years": ("a65_79","7579"),
    "80-84 years":    ("a80p","80UP"), "85-89 years": ("a80p","80UP"),
    "90-94 years":    ("a80p","80UP"), "95+ years":   ("a80p","80UP"),
}
SEX = {"Male":"M","Female":"F"}

def main():
    domain = [r["iso3"] for r in load("countries")["rows"]]
    # prévalence combinée par (iso, gbd_age, sex)
    p558, p973 = {}, {}
    for row in csv.DictReader(open(CSV, encoding="utf-8")):
        iso = GBD2ISO.get(row["location_name"])
        sex = SEX.get(row["sex_name"])
        age = row["age_name"]
        if not iso or not sex or age not in AGE2:
            continue
        v = float(row["val"])
        key = (iso, age, sex)
        (p558 if row["cause_id"] == "558" else p973)[key] = v
    combined = {}
    for key in set(p558) | set(p973):
        a, b = p558.get(key, 0.0), p973.get(key, 0.0)
        combined[key] = 1.0 - (1.0 - a) * (1.0 - b)

    # poids population par bande d'âge × sexe, depuis le cache (pas de réseau)
    bands = sorted({b for _, b in AGE2.values()})
    popb = {}
    for band in bands:
        for sx, suf in (("F","FE"),("M","MA")):
            popb[(band, sx)] = cached_band_pop(band, suf)
    no_pop = [i for i in domain if i not in popb[("0004","F")]]
    if no_pop:
        print("  poids population absents du cache -> pondération égale intra-bucket pour:", no_pop)

    # agrégation vers 8 buckets, pondérée population (80+ : sous-groupes en poids égal ;
    # pays sans effectifs en cache -> poids 1 = moyenne simple intra-bucket, documenté)
    n80 = sum(1 for a in AGE2 if AGE2[a][0] == "a80p")
    def w(iso, band, sex):
        base = popb[(band, sex)].get(iso, (0, 0.0))[1] or 1.0
        return (base / n80) if band == "80UP" else base

    h = load("health")
    mp = {}
    for iso in domain:
        for gage, (bucket, band) in AGE2.items():
            for sex in ("F","M"):
                key = (iso, gage, sex)
                if key not in combined:
                    continue
                wt = w(iso, band, sex) or 1.0
                mp.setdefault(iso, {}).setdefault(bucket, {}).setdefault(sex, [0.0, 0.0])
                acc = mp[iso][bucket][sex]
                acc[0] += combined[key] * wt
                acc[1] += wt
    out = {}
    for iso in mp:
        out[iso] = {}
        for bucket in mp[iso]:
            out[iso][bucket] = {}
            for sex, (num, den) in mp[iso][bucket].items():
                out[iso][bucket][sex] = round(num / den, 5) if den else None
    h["mental_prevalence"] = out
    h["mental_prevalence_source"] = {"source_id": "gbd", "year": 2021, "coverage": "national",
        "note": "Prévalence d'au moins un trouble mental ou addictif = 1-(1-p_mental)(1-p_substance), "
                "GBD 2023 (IHME). Agrégé 5 ans -> 8 buckets, pondéré population WDI. "
                "Brut: data/raw/gbd_mental_2021.csv."}
    save("health", h)
    # contrôle
    def g(iso,a,s): return out.get(iso,{}).get(a,{}).get(s)
    print("mental_prevalence national pour %d pays." % len(out))
    print("  contrôle USA a20_34 F=%.3f M=%.3f | IND a20_34 F=%.3f | CHN a65_79 F=%.3f" %
          (g("USA","a20_34","F"), g("USA","a20_34","M"), g("IND","a20_34","F"), g("CHN","a65_79","F")))

if __name__ == "__main__":
    main()
