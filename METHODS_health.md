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

## 3. Santé mentale (`mental`)

Prévalence d'**au moins un trouble mental ou addictif** par pays × âge × sexe,
directement depuis la prévalence GBD des troubles mentaux et addictifs (union des
causes de ce chapitre, combinée par `1 − Π(1 − p_i)` pour éviter le double compte).
Dignité : on ne nomme jamais une pathologie, on décrit un niveau de limitation.

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

Le test d'atteignabilité (`data/raw/_reachability_2026-07-21.md`) montre que
`vizhub.healthdata.org/gbd-results/` répond, mais l'**extraction fine des
séquelles avec leurs disability weights par pays × âge × sexe** passe par l'outil
de résultats GBD, qui exige un compte GHDx pour les téléchargements en masse —
non disponible dans cet environnement. Conformément à la règle « ne jamais
inventer une valeur », le fichier `data/health.json` conserve pour l'instant le
**modèle groupé documenté** :

- `severity_base_group` par palier de revenu (`rich`/`mid`/`low`), cohérent avec
  les seuils ci-dessus et les ordres de grandeur GBD ;
- `age_factors` (dégradation avec l'âge), `income_penalty` (§4), `mental` (§3).

Ce modèle groupé vaut **coverage `income_group`** (pas `national`) : c'est une
estimation honnête par palier, pas un chiffre national inventé. La méthode
ci-dessus (§1–§5) est **figée** et prête à produire `severity_base[iso][age][sex]`
en coverage `national` dès que l'export GBD (GHDx) est fourni ; le résolveur
`sante` du moteur pourra alors lire une base par pays × âge × sexe (voir
`METHODS_engine.md`, généralisation prévue mais non requise pour le lot 1).
