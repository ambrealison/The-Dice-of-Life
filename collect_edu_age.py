#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_edu_age.py — base éducation adulte par pays × groupe d'âge × sexe
(Barro-Lee 2010, redistribué par World Bank EdStats, réharmonisé ISO3).

Corrige le ressenti "Chine tout en primaire" : la base par âge donne aux jeunes
cohortes leur vrai niveau (ex. Chine 20-24 : ~81 % secondaire), là où la base
unique 25+ écrasait tout sur "primaire".

Partition des 4 niveaux (somme = 100 %, vérifié) par âge :
  aucune     = BAR.NOED.<age>[.FE].ZS
  primaire   = BAR.PRM.ICMP.<age>[.FE].ZS   (« Total incomplete+completed primary »)
  secondaire = BAR.SEC.ICMP.<age>[.FE].ZS
  superieur  = BAR.TER.ICMP.<age>[.FE].ZS

WDI ne fournit que le total et le féminin (.FE) ; le masculin est reconstitué par
pondération population : part_M = (part_tot·N_tot − part_F·N_F) / N_M, avec les
effectifs par bande d'âge×sexe de WDI (WPP). Agrégation des groupes 5 ans vers les
6 buckets adultes, pondérée par la population de chaque groupe.

Écrit education.attainment_by_age[iso][bucket][sex] = {shares, coverage, year}.
La base pays education.attainment_base[iso] est conservée comme repli.
"""
import json
from collect import fetch, wdi, load, save   # réutilise le cache data/raw/

YEAR_BL = 2010
BL_AGES = ["1519","2024","2529","3034","3539","4044","4549","5054","5559","6064","6569","7074","75UP"]
BUCKET_BL = {
    "a15_19": ["1519"],
    "a20_34": ["2024","2529","3034"],
    "a35_49": ["3539","4044","4549"],
    "a50_64": ["5054","5559","6064"],
    "a65_79": ["6569","7074","75UP"],
    "a80p":   ["75UP"],
}
# bande WDI d'effectifs correspondant à chaque groupe Barro-Lee (75+ = 7579+80UP)
POP_BANDS = {"1519":["1519"],"2024":["2024"],"2529":["2529"],"3034":["3034"],
             "3539":["3539"],"4044":["4044"],"4549":["4549"],"5054":["5054"],
             "5559":["5559"],"6064":["6064"],"6569":["6569"],"7074":["7074"],
             "75UP":["7579","80UP"]}
LEVELS = [("aucune","BAR.NOED.%s"),("primaire","BAR.PRM.ICMP.%s"),
          ("secondaire","BAR.SEC.ICMP.%s"),("superieur","BAR.TER.ICMP.%s")]

def norm4(d):
    t = sum(d.values())
    return {k: v/t for k, v in d.items()} if t > 0 else None

def main():
    domain = [r["iso3"] for r in load("countries")["rows"]]
    # 1) Barro-Lee par âge : total et féminin
    bar = {}  # bar[(level_id, age, variant)] = {iso:(yr,val)}
    for lid, pat in LEVELS:
        for age in BL_AGES:
            for variant in ("tot", "fe"):
                ind = (pat % age) + (".FE.ZS" if variant == "fe" else ".ZS")
                bar[(lid, age, variant)] = wdi(ind, domain, date="2005:2010")
    # 2) effectifs par bande d'âge × sexe (pondération)
    popb = {}  # popb[(band, sex)] = {iso:(yr,val)}
    bands = sorted({b for lst in POP_BANDS.values() for b in lst})
    for band in bands:
        for sex, suf in (("F","FE"),("M","MA")):
            popb[(band, sex)] = wdi("SP.POP.%s.%s" % (band, suf), domain, date="2018:2024")

    def pop_of(iso, blage, sex):
        return sum(popb[(b, sex)].get(iso, (0,0.0))[1] for b in POP_BANDS[blage])

    e = load("education")
    e.setdefault("attainment_by_age", {})
    e.setdefault("attainment_by_age_source", {"source_id": "barrolee", "year": YEAR_BL,
                 "note": "Base adulte par pays x groupe d'age x sexe (Barro-Lee via WDI EdStats). "
                         "Masculin reconstitue par ponderation population. Repli: attainment_base[iso]."})
    built = 0
    for iso in domain:
        per_age = {}   # per_age[blage][sex] = {4 levels} normalisé
        for blage in BL_AGES:
            tot = {lid: bar[(lid, blage, "tot")].get(iso) for lid, _ in LEVELS}
            fe  = {lid: bar[(lid, blage, "fe")].get(iso)  for lid, _ in LEVELS}
            if any(tot[lid] is None for lid, _ in LEVELS):
                continue
            tv = {lid: tot[lid][1] for lid, _ in LEVELS}
            # féminin : direct (repli sur total si absent)
            fv = {lid: (fe[lid][1] if fe[lid] is not None else tv[lid]) for lid, _ in LEVELS}
            # masculin : reconstitué par population
            Nf, Nm = pop_of(iso, blage, "F"), pop_of(iso, blage, "M")
            if Nm > 0:
                mv = {lid: max(0.0, (tv[lid]*(Nf+Nm) - fv[lid]*Nf) / Nm) for lid, _ in LEVELS}
            else:
                mv = dict(tv)
            sf, sm = norm4(fv), norm4(mv)
            if sf and sm:
                per_age[blage] = {"F": sf, "M": sm}
        if not per_age:
            continue
        # agrégation vers les 6 buckets, pondérée population
        by_bucket = {}
        for bucket, blages in BUCKET_BL.items():
            for sex in ("F","M"):
                acc = {lid: 0.0 for lid, _ in LEVELS}
                wtot = 0.0
                for blage in blages:
                    if blage not in per_age:
                        continue
                    w = pop_of(iso, blage, sex) or 1.0
                    for lid, _ in LEVELS:
                        acc[lid] += per_age[blage][sex][lid] * w
                    wtot += w
                if wtot > 0:
                    sh = norm4({lid: acc[lid]/wtot for lid, _ in LEVELS})
                    by_bucket.setdefault(bucket, {})[sex] = {"shares": sh, "coverage": "national", "year": YEAR_BL}
        if by_bucket:
            e["attainment_by_age"][iso] = by_bucket
            built += 1
    save("education", e)
    # petit contrôle
    chn = e["attainment_by_age"].get("CHN", {}).get("a20_34", {}).get("M", {}).get("shares")
    print("attainment_by_age construit pour %d/%d pays." % (built, len(domain)))
    if chn:
        print("  contrôle CHN a20_34 M:", {k: round(v,3) for k,v in chn.items()})

if __name__ == "__main__":
    main()
