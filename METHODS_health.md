# METHODS_health.md — méthode santé figée (niveau 6)

Ce document **fige** la méthode de passage des données GBD (IHME) vers les 4 bandes
de sévérité du schéma, **avant** de dérouler les pays. La méthode s'applique
identiquement partout. Elle est figée maintenant ; son application pays par pays
dépend de l'accès aux microdonnées GBD (voir « État d'accès » plus bas).

## 1. Buckets cibles (figés, `dimensions.health_states`)

| id | libellé FR | libellé EN | plage de poids d'incapacité (DW) par personne |
|---|---|---|---|
| `bonne`         | En pleine forme        | In great shape       | DW < 0.05 |
| `gene_legere`   | Une gêne légère        | A slight impairment  | 0.05 ≤ DW < 0.12 |
| `incap_moderee` | Une incapacité modérée | A moderate disability| 0.12 ≤ DW < 0.30 |
| `incap_severe`  | Une incapacité sévère  | A severe disability  | DW ≥ 0.30 |

Ces seuils sont **fixes** et documentés une fois pour toutes. Ils reprennent les
ordres de grandeur des *disability weights* du GBD (une cataracte légère ≈ 0.03,
une dépression modérée ≈ 0.15, une cécité ≈ 0.19, une incapacité motrice sévère ≈ 0.40).

## 2. Poids d'incapacité combiné par personne (modèle de comorbidité GBD)

Le GBD publie, par pays × âge × sexe, la **prévalence de chaque séquelle** et son
**disability weight** `dw_i`. Une personne peut cumuler plusieurs séquelles. Le
GBD combine les poids par un **modèle multiplicatif** (les incapacités ne
s'additionnent pas linéairement) :

```
DW_combiné(personne) = 1 − Π_i (1 − dw_i)     pour les séquelles i présentes
```

Procédure figée, par cellule pays × âge × sexe :

1. Récupérer la liste des séquelles avec leur prévalence `p_i` et leur `dw_i`.
2. Reconstituer la **distribution du DW combiné par personne** en tirant les
   séquelles comme des indicatrices indépendantes de probabilité `p_i` (approche
   Monte-Carlo, ≥ 100 000 tirages par cellule), puis en appliquant la formule
   multiplicative ci-dessus. C'est la même hypothèse d'indépendance que le GBD
   pour le calcul des YLD avec correction de comorbidité.
3. Ranger chaque personne simulée dans une des 4 bandes selon son `DW_combiné`.
4. Les 4 parts obtenues forment `severity_base[iso][age][sex]` (somme = 1).

> Le passage se fait bien **des YLD/prévalences de séquelles** vers les bandes,
> ce n'est pas une variable prête à l'emploi. La correction de comorbidité évite
> de surcompter les personnes polymorbides.

## 3. Santé mentale (`mental`) — ✅ NATIONALE (intégrée)

Prévalence d'**au moins un trouble mental ou addictif** par pays × âge × sexe,
combinée depuis la prévalence GBD des troubles mentaux (cause 558) et addictifs
(cause 973) par `1 − (1 − p_mental)(1 − p_substance)` pour éviter le double compte.
Dignité : on ne nomme jamais une pathologie, on décrit un niveau de limitation.

**Statut : intégrée** (GBD 2023, requête A fournie 2026-07-21). Brut en cache
`data/raw/gbd_mental_2021.csv`. Agrégation des groupes 5 ans du GBD vers les 8
buckets, pondérée population (WDI). Écrit `health.mental_prevalence[iso][âge][sexe]`,
coverage **national**, 23/23 pays. Repli : ancien modèle global `health.mental`
si une case manque. Voir `collect_mental.py`.

Effet (P(trouble mental), avant modèle global → après GBD national) :
USA 20-34 F **11 % → 31 %** ; Inde 20-34 F 11 % → 17 % ; Japon 35-49 H 11 % → 15 %.

## 4. Gradient de revenu (`income_penalty`)

Multiplicateur des états dégradés par quintile de revenu, calibré sur la relation
pauvreté–santé du GBD par **SDI** (Socio-Demographic Index) : les quintiles bas
portent davantage de morbidité à âge égal. Le multiplicateur est appliqué aux
états `incap_moderee`/`incap_severe` puis la distribution est renormalisée à 1.
Facteur figé (identique à tous les pays), calibré sur le gradient morbidité–SDI :

```
income_penalty (q1..q5) = [1.40, 1.20, 1.00, 0.85, 0.70]
```

## 5. Renormalisation

Après application des facteurs (âge, income_penalty), **renormaliser à 1** chaque
distribution pays × âge × sexe (tolérance 1e-6).

## État d'accès (2026-07-21) et repli honnête

Avancement en deux temps :

1. **Santé mentale (requête A) : intégrée en national** (§3). L'export GBD de
   prévalence des troubles mentaux/addictifs a été fourni et branché
   (`mental_prevalence`, coverage `national`, 23/23 pays).
2. **Sévérité physique (4 bandes, requête B YLDs) : encore en modèle groupé.**
   L'export fin (YLDs / séquelles × disability weights par pays × âge × sexe) est
   bloqué au téléchargement direct par le portail GBD (volume trop gros → demande
   groupée requise). En attendant, `data/health.json` conserve le **modèle groupé
   documenté** pour les 4 bandes physiques :
   - `severity_base_group` par palier de revenu (`rich`/`mid`/`low`) ;
   - `age_factors` (dégradation avec l'âge), `income_penalty` (§4).

Le modèle groupé physique vaut **coverage `income_group`** (pas `national`) :
estimation honnête par palier, pas un chiffre inventé. La méthode §1–§5 est
**figée** et prête à produire `severity_base[iso][age][sex]` en national dès que
le fichier YLDs de la demande groupée arrive — voir `GBD_YLD_REQUEST.md` pour la
marche à suivre exacte. Le résolveur `sante` lira alors une base par pays × âge ×
sexe (généralisation moteur, `METHODS_engine.md`).
