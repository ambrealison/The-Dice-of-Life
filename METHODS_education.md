# METHODS_education.md — facteurs éducation figés (niveau 5)

Méthode et facteurs **figés avant de dérouler les pays**, appliqués identiquement
partout. Le niveau 5 combine une **base** (par pays) et des **facteurs**
multiplicatifs, avec renormalisation finale à 1.

## 1. Base adulte — attainment 4 niveaux

Buckets (figés, `dimensions.education_adult`) : `aucune`, `primaire`,
`secondaire`, `superieur`.

**Source de collecte (lot 1)** : indicateurs cumulés d'attainment de la
population 25+ du World Bank WDI (redistribution UIS / Barro-Lee) —
`SE.TER.CUAT.BA.ZS` (≥ licence), `SE.SEC.CUAT.UP.ZS` (≥ secondaire supérieur),
`SE.PRM.CUAT.ZS` (≥ primaire complété). Passage cumulé → distribution par
différence :

```
superieur  = SE.TER.CUAT.BA.ZS
secondaire = SE.SEC.CUAT.UP.ZS − SE.TER.CUAT.BA.ZS      (borné ≥ 0)
primaire   = SE.PRM.CUAT.ZS   − SE.SEC.CUAT.UP.ZS       (borné ≥ 0)
aucune     = 100              − SE.PRM.CUAT.ZS          (borné ≥ 0)
```

puis normalisation à 1. `source_id = barrolee` (primaire déclarée au schéma,
secondaire `uis`), `coverage = national`, `year` = année de la donnée WDI.

> La base reste **par pays** pour le lot 1 (comme le seed : `attainment_base[iso]`).
> La généralisation à `iso × groupe d'âge adulte × sexe` avec Barro-Lee brut est
> **autorisée** mais optionnelle (voir `METHODS_engine.md`) ; elle sera activée
> quand la base Barro-Lee complète sera récupérée (barrolee.com a un certificat
> cassé ; à faire via un miroir OWID).

## 2. Base enfant — scolarisation (`child_enrollment`)

Part scolarisée pour les 5–14 ans (`ecole` vs `hors`).

**Source (lot 1)** : `SE.PRM.UNER.ZS` (enfants hors école, % de l'âge primaire) →
`in_school = 1 − SE.PRM.UNER.ZS/100`. Repli : `SE.PRM.NENR` (taux net de
scolarisation) si l'indicateur hors-école manque (ex. Chine, non reporté →
laissé au repli du seed, signalé dans `COVERAGE_REPORT.md`). `coverage = national`.

## 3. Facteurs multiplicatifs (figés, identiques partout)

Les facteurs modulent la base selon la situation tirée, puis on **renormalise à 1**.

### 3.1 `rural_penalty` — par niveau
Effet du milieu rural sur l'attainment (moins de supérieur, plus d'absence
d'école), calibré comme l'effet multiplicatif moyen lieu de résidence des
enquêtes DHS/MICS (fréquentation par milieu). Valeur figée :

```
rural_penalty = { aucune: 1.60, primaire: 1.15, secondaire: 0.70, superieur: 0.45 }
```

### 3.2 `income_prime` — par quintile
Effet du niveau de vie (les quintiles aisés accèdent plus au supérieur), calibré
comme l'effet multiplicatif moyen par quintile de richesse (DHS/MICS). Figé :

```
income_prime.superieur  (q1..q5) = [0.40, 0.70, 1.00, 1.40, 1.90]
income_prime.aucune     (q1..q5) = [1.90, 1.35, 1.00, 0.70, 0.45]
income_prime.secondaire (q1..q5) = [0.70, 0.85, 1.00, 1.15, 1.30]
```

### 3.3 `gender_gap` — par pays × sexe
Appliqué **uniquement là où l'écart hommes-femmes est significatif**, dérivé du
ratio d'attainment hommes/femmes de Barro-Lee. Multiplicateur sur `aucune`,
`secondaire`, `superieur` pour le sexe féminin. Figé (pays à écart marqué) :

```
gender_gap[IND] = gender_gap[NER] = { aucune: 1.50, superieur: 0.65, secondaire: 0.85 }
```

Les pays sans écart significatif n'ont pas d'entrée `gender_gap` (facteur neutre).

## 4. Ordre d'application (résolveur `education`)

1. petite enfance (a00_04) → `petite` déterministe ;
2. 5–14 ans → `child_enrollment` (ecole/hors) ;
3. adultes → base `attainment_base[iso]`, puis × `rural_penalty` (si rural),
   × `income_prime` (selon quintile), × `gender_gap` (si femme et pays concerné) ;
4. **renormalisation à 1**.

## Calibration des facteurs (statut)

Les valeurs des §3 sont **figées** et appliquées globalement, calibrées sur les
ordres de grandeur des enquêtes DHS/MICS (fréquentation scolaire par milieu et
par quintile de richesse). L'accès direct aux microdonnées DHS demande une
inscription (hors périmètre réseau actuel) ; les facteurs restent donc des
multiplicateurs globaux documentés, à re-caler quand les tabulations DHS/MICS
seront disponibles. Le `gender_gap` par pays se dérive du ratio Barro-Lee dès que
la base Barro-Lee complète est récupérée.
