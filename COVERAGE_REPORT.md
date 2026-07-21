# COVERAGE_REPORT.md — couverture des données

Généré pour le **lot 1 (preuve de bout en bout)** : Inde, Chine, États-Unis,
collecte du 2026-07-21 (`collect.py`, bruts en cache dans `data/raw/`).
Les 4 autres pays du domaine (France, Autriche, Brésil, Niger) restent au
**seed** (chiffres approximatifs dirigés par les vraies distributions), en attente
des lots suivants.

Chaque valeur produite porte son `coverage` réel. Aucune valeur n'est inventée :
un indicateur sans donnée nationale est laissé au repli et signalé ci-dessous.

## Lot 1 — pays collectés (données nationales réelles)

| Table (niveau) | IND | CHN | USA | Source de collecte (primaire) |
|---|---|---|---|---|
| countries (1) — population, income_group | national | national | national | WDI `SP.POP.TOTL` + classification revenus (wpp/wdi) |
| age_sex (2) — jointe âge×sexe | national | national | national | WDI `SP.POP.<bande>.<FE\|MA>` (wpp) |
| settlement (3) — grande/ville/rural | national | national | national | WDI `SP.URB.TOTL.IN.ZS` + `EN.URB.MCTY.TL.ZS` (wup) |
| income (4) — percentile mondial | national | national | national | PIP déciles + `income_world_ref.json` (pip) |
| education (5) — base adulte | national | national | national | WDI attainment 25+ (barrolee/uis) |
| education (5) — scolarisation enfant | national | **repli (seed)** | national | WDI `SE.PRM.UNER.ZS` ; CHN non reporté |
| health (6) — sévérité + mental | **income_group** | **income_group** | **income_group** | modèle groupé GBD (voir `METHODS_health.md`) |
| family (7) — situation familiale | **regional/world** | **regional/world** | **regional/world** | paramètres globaux (voir `METHODS_engine.md`) |
| living (8) — électricité/internet/eau | national | national | national | WDI `EG.ELC.ACCS.ZS`, `IT.NET.USER.ZS`, `SH.H2O.*` (wdi/jmp) |

### Notes de repli (lot 1)

- **CHN, scolarisation enfant** : `SE.PRM.UNER.ZS` et `SE.PRM.NENR` non reportés
  par la Chine → valeur du seed conservée (`in_school = 0.98`), non nationale.
  À combler via UIS/OWID (UIS bloqué en direct, 403).
- **CHN, eau** : `SH.H2O.SMDW.ZS` (géré en sécurité) non reporté → repli sur
  `SH.H2O.BASW.ZS` (au moins service de base, JMP), toujours **national**.
- **health (6)** : microdonnées GBD (séquelles × disability weights) non
  accessibles sans compte GHDx → modèle groupé par palier de revenu, **coverage
  `income_group`**. Méthode nationale figée et prête (`METHODS_health.md`).
- **family (7)** : World Marriage Data (`un.org`) bloqué (403) → modèle
  paramétrique global, **coverage `regional`/`world`**. Généralisation nationale
  documentée (`METHODS_engine.md`).

## income_world_ref.json

Distribution mondiale de référence du revenu construite à partir des **40 pays**
les plus peuplés disposant d'une enquête PIP récente (400 points de déciles
pondérés par population, dollars/jour PPA). Sert à convertir un quintile national
en percentile mondial. Provenance de chaque pays listée dans le fichier
(`countries_used`).

## Reste du domaine (seed, à collecter aux lots suivants)

| Pays | Statut |
|---|---|
| FRA, AUT, BRA, NER | seed (approximatif, dirigé par les vraies distributions) — non recollectés au lot 1 |

## Prochaines étapes (lots suivants, priorisés par population)

1. Étendre `collect.py` au reste du top 20 (IDN, PAK, NGA, BRA, BGD, RUS, …) —
   mêmes sources WDI/PIP, mêmes replis.
2. Récupérer Barro-Lee brut (miroir OWID) → base éducation par âge×sexe +
   `gender_gap` dérivé, activer la généralisation 1 du moteur.
3. Export GBD (compte GHDx) → `severity_base[iso][age][sex]` national (niveau 6).
4. World Marriage Data (miroir OWID / repli) → distributions famille nationales,
   activer la généralisation 2 du moteur.
5. Passe de repli complète (régional pondéré / income_group / mondial) pour tout
   pays sans donnée nationale, `coverage` marqué partout.
