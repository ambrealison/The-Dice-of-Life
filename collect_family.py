#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_family.py — nationalise le calendrier matrimonial (célibataire ↔ couple)
par pays et par sexe, via l'âge médian au mariage (SMAM) de World Bank / UN.

Contexte d'accès : la distribution complète du statut matrimonial (jamais marié /
marié-union / veuf / divorcé) par pays × âge × sexe de World Marriage Data (ONU
DESA) n'est PAS joignable ici — un.org est bloqué (403), les endpoints DONNÉES du
UN Data Portal exigent un jeton (401), et il n'existe pas de miroir OWID de ce jeu.

Ce qui EST joignable : l'indicateur SMAM (Singulate Mean Age at Marriage) par sexe
de WDI (SP.DYN.SMAM.FE / .MA), qui est une sortie de World Marriage Data. À partir
du SMAM national, on résout la part célibataire par âge et sexe avec un modèle de
nuptialité figé (courbe logistique centrée sur le SMAM). Le veuvage (branche âgée)
et le partage couple/parent restent sur le modèle documenté (repli régional/mondial)
faute de données nationales — voir METHODS_family.md.

Écrit family.smam[iso] = {F, M, year, coverage} et family.nuptiality = {sigma, cap}.
"""
import json
from collect import fetch, wdi, load, save, ref_average

SIGMA = 5.0   # étalement (années) des âges au mariage autour du SMAM (figé, documenté)
CAP = 0.94    # part maximale de personnes un jour en union (plancher célibataire 6 %)

def main():
    rows = load("countries")["rows"]
    domain = [r["iso3"] for r in rows]
    meta = {r["iso3"]: r for r in rows}
    pop = {r["iso3"]: r["population"] for r in rows}

    smf = wdi("SP.DYN.SMAM.FE", domain, date="2000:2024")
    smm = wdi("SP.DYN.SMAM.MA", domain, date="2000:2024")

    national = {}
    for iso in domain:
        if iso in smf and iso in smm:
            national[iso] = {"F": round(smf[iso][1], 2), "M": round(smm[iso][1], 2)}

    f = load("family")
    f["nuptiality"] = {"sigma": SIGMA, "cap": CAP,
        "note": "Part célibataire par âge = 1 - cap/(1+exp(-(age-SMAM)/sigma)). "
                "SMAM national par sexe (WDI SP.DYN.SMAM). Veuvage et parentalité "
                "restent sur le modèle documenté (repli), voir METHODS_family.md."}
    f["smam"] = {}
    for iso in domain:
        if iso in national:
            yr = max(smf[iso][0], smm[iso][0])
            f["smam"][iso] = {"F": national[iso]["F"], "M": national[iso]["M"],
                              "coverage": "national", "year": yr}
        else:
            val, cov = ref_average(iso, national, meta, pop)
            if val:
                f["smam"][iso] = {"F": round(val["F"], 2), "M": round(val["M"], 2), "coverage": cov}
                print("[7] SMAM repli", cov, "pour", iso)
    save("family", f)
    print("[7] SMAM national pour %d/%d pays. Ex CHN=%s IND=%s USA=%s" %
          (len(national), len(domain), f["smam"].get("CHN"), f["smam"].get("IND"), f["smam"].get("USA")))

if __name__ == "__main__":
    main()
