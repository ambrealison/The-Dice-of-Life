# METHODS_family.md — méthode famille (niveau 7)

## Accès aux sources (2026-07-21)

La **distribution complète du statut matrimonial** (jamais marié / marié-union /
veuf / divorcé) par pays × âge × sexe de **World Marriage Data** (ONU DESA) n'est
pas joignable dans cet environnement :

- `un.org` (pages World Marriage Data) → **403** (bloqué par la politique d'egress) ;
- endpoints **données** du UN Data Portal (`population.un.org/dataportalapi`) →
  **401** (jeton requis) ; seuls « currently married » (42-45) sont exposés, et
  gated ;
- **aucun miroir OWID** de ce jeu (tous les slugs marital testés → 404) ;
- WDI n'expose que le mariage précoce (`SP.M18/M15`), pas le statut complet.

## Ce qui est nationalisé (donnée réelle joignable)

L'indicateur **SMAM** (Singulate Mean Age at Marriage, âge médian au premier
mariage) par sexe est joignable via WDI (`SP.DYN.SMAM.FE` / `.MA`) — c'est une
sortie de World Marriage Data. On l'utilise pour résoudre nationalement la part
**célibataire ↔ en couple** par pays, âge et sexe, avec un **modèle de nuptialité
figé** :

```
p_en_union(âge)  = cap / (1 + exp(-(âge − SMAM) / sigma))
part_célibataire = 1 − p_en_union
```

Paramètres figés (identiques partout, `family.nuptiality`) :
`sigma = 5.0` ans (étalement des âges au mariage), `cap = 0.94` (part maximale un
jour en union → plancher célibataire 6 %). `SMAM` est national par sexe
(`family.smam[iso]`, coverage `national`, 23/23 pays ; repli régional/income_group
sinon).

La **parentalité** est traitée comme une part *parmi les personnes en couple*
(`pr = mid_parent / (1 − mid_celibataire)`, × `early_par_mult` dans les régions à
parentalité précoce), donc elle **s'échelonne avec le taux de mise en couple
national** au lieu d'écraser la case « couple ».

### Effet (avant → après, revenu/urbain neutres)

| Cas | Avant (modèle global) | Après (SMAM national) |
|---|---|---|
| IND 20-34 **F** (SMAM 21,4) | célib 19 / couple 29 / parent 52 | célib 29 / couple 14 / parent 57 |
| IND 20-34 **M** (SMAM 26,0) | célib 19 / couple 29 / parent 52 | **célib 48** / couple 10 / parent 41 |
| USA 20-34 **F** (SMAM 27,5) | célib 35 / couple 25 / parent 40 | **célib 55** / couple 17 / parent 27 |

L'écart d'âge au mariage hommes/femmes (Inde) et le mariage tardif (USA) sont
désormais capturés par pays et par sexe.

## Ce qui reste sur le modèle documenté (repli, non national)

- **Veuvage** (branche 65+) : paramètre `elder_widow` (F 0,55 / M 0,28), coverage
  `regional`/`world`. Nationaliser demande le veuvage par âge×sexe de World
  Marriage Data (gated).
- **Divorcé** : non représenté (bucket absent du schéma).
- Le **taux de parentalité** de base (`mid_parent`) reste un paramètre documenté
  (DHS/recensements non joignables), seul son échelonnement est national.

## Ce qu'il faudrait pour le modèle national complet

Un **jeton API du UN Data Portal** (inscription gratuite sur
`population.un.org/dataportal`) OU le déblocage de `un.org` dans la politique
d'egress. Avec l'un des deux, on récupère le statut matrimonial complet (jamais
marié / marié-union / veuf / divorcé) par pays × âge × sexe et on passe la
généralisation 2 du moteur en distributions entièrement nationales (voir
`METHODS_engine.md`).
