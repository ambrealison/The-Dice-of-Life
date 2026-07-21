# COVERAGE_REPORT.md — couverture des données

Collecte du 2026-07-21 (`collect.py`, bruts en cache dans `data/raw/` avec URLs).
Chaque valeur porte son `coverage` réel. Aucune valeur inventée : un indicateur
sans donnée nationale déclenche la hiérarchie de repli (régional → income_group →
mondial), marquée en conséquence.

- **Lot 1** : IND, CHN, USA (preuve de bout en bout).
- **Lot 2** : les 20 pays les plus peuplés — IND, CHN, USA, IDN, PAK, NGA, BRA,
  BGD, RUS, ETH, MEX, JPN, EGY, PHL, COD, VNM, IRN, TUR, DEU, THA.
- **Domaine total** : 23 pays (top 20 + FRA, AUT, NER conservés du seed).

## Couverture par table — top 20 (lot 2)

| Table (niveau) | national | repli | source primaire |
|---|---|---|---|
| countries (1) — population, income_group | 20 | — | WDI `SP.POP.TOTL` + classification (wpp/wdi) |
| age_sex (2) — âge×sexe | 20 | — | WDI `SP.POP.<bande>.<FE\|MA>` (wpp) |
| settlement (3) — grande/ville/rural | 20 | — | WDI `SP.URB.TOTL.IN.ZS` + `EN.URB.MCTY.TL.ZS` (wup) |
| income (4) — percentile mondial | 20 | — | PIP déciles + `income_world_ref.json` (pip) |
| education (5) — base adulte pays | 20 | — | WDI attainment 25+ (barrolee/uis) |
| education (5) — base **par âge × sexe** | 21/23 | NGA, ETH → repli base pays | Barro-Lee par âge (WDI EdStats) |
| education (5) — scolarisation enfant | 18 | **CHN** régional, **COD** income_group | WDI `SE.PRM.UNER.ZS` (repli `SE.PRM.NENR`) |
| living (8) — électricité/internet/eau | 20 | — | WDI `EG.ELC.ACCS.ZS`, `IT.NET.USER.ZS`, `SH.H2O.*` (wdi/jmp) |
| health (6) — sévérité + mental | — | **20 × income_group** | modèle groupé GBD (`METHODS_health.md`) |
| family (7) — célibataire ↔ couple | **23 (SMAM)** | — | WDI `SP.DYN.SMAM.FE/MA` + modèle nuptialité |
| family (7) — veuvage / parentalité | — | regional/world | modèle documenté (`METHODS_family.md`) |

### Détail des replis (top 20)

- **CHN, scolarisation enfant** → `regional` : Chine ne reporte ni `SE.PRM.UNER.ZS`
  ni `SE.PRM.NENR` → moyenne pondérée population de la sous-région (Asie de l'Est).
- **COD, scolarisation enfant** → `income_group` : pas de donnée régionale
  disponible dans le domaine → moyenne du groupe de revenu (low).
- **CHN, eau** → national via repli d'indicateur `SH.H2O.BASW.ZS` (service de base,
  JMP) faute de `SH.H2O.SMDW.ZS`. Idem pour d'autres pays sans « géré en sécurité ».
- **health (6)** : microdonnées GBD (séquelles × disability weights) non accessibles
  sans compte GHDx → modèle groupé par palier de revenu (`rich`/`mid`/`low`, dérivé
  de l'income_group), **coverage `income_group`**. Méthode nationale figée et prête
  (`METHODS_health.md`).
- **family (7)** : World Marriage Data (`un.org`) bloqué (403) → modèle paramétrique
  global + drapeau `early_parenthood` par région, **coverage `regional`/`world`**.
  `early_parenthood = [BGD, COD, ETH, IND, NER, NGA, PAK]` (régions à forte
  fécondité adolescente : Asie du Sud, Afrique de l'Ouest/Est/centrale).
  Généralisation nationale documentée (`METHODS_engine.md`).

## income_world_ref.json

Distribution mondiale de référence construite à partir des **40 pays** les plus
peuplés avec enquête PIP récente (400 points de déciles pondérés par population,
dollars/jour PPA). Sert à convertir un quintile national en percentile mondial.
Provenance de chaque pays dans `countries_used`. Contrôle de plausibilité :
COD `[0,1,2,4,26]`, NGA `[3,6,12,22,49]`, IND `[12,22,32,41,60]`,
CHN `[37,56,65,76,88]`, USA `[81,90,96,98,100]`, DEU `[84,92,94,96,99]`.

## Reste du domaine (seed)

| Pays | Statut |
|---|---|
| FRA, AUT, NER | seed (approximatif, dirigé par les vraies distributions), hors top 20 — à recollecter aux lots suivants |

## Prochaines étapes

1. Étendre `collect.py` au-delà du top 20 (reste du domaine WPP ~195), mêmes
   sources WDI/PIP, mêmes replis.
2. Barro-Lee brut (miroir OWID) → base éducation par âge×sexe + `gender_gap`
   dérivé ; activer la généralisation 1 du moteur.
3. Export GBD (compte GHDx) → `severity_base[iso][age][sex]` national (niveau 6).
4. World Marriage Data (miroir OWID / repli) → distributions famille nationales ;
   activer la généralisation 2 du moteur.
5. Recollecter FRA, AUT, NER pour retirer les dernières valeurs seed.
