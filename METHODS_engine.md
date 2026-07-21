# METHODS_engine.md — généralisations de résolveur (documentation)

MISSION.md autorise deux généralisations du moteur (`engine.js`) pour la fidélité
complète, en gardant la logique **pilotée par la forme des données**, sans écrire
aucun chiffre pays dans le code. Ce document décrit les deux, et leur **statut**
pour le lot 1 (preuve de bout en bout : IND, CHN, USA).

## Généralisation 1 — Éducation : base par pays × groupe d'âge × sexe

- **Aujourd'hui (lot 1)** : le résolveur `education` lit une base **par pays**,
  `DATA.education.attainment_base[iso].shares` (comme le seed). Suffisant et
  cohérent avec les données WDI collectées (attainment 25+ par pays).
- **Généralisation prévue** : base `attainment_base[iso][adult_age_group][sex]`.
  Le résolveur sélectionnerait la base selon l'âge et le sexe tirés, avec repli
  sur la base pays si une case manque. La forme des données commande : si la
  valeur est un objet à sous-clés d'âge/sexe, on descend ; sinon on lit la base
  pays. Aucune donnée pays dans le code.
- **Déclencheur d'activation** : disposer de la base **Barro-Lee brute** (par
  pays × groupe d'âge 15-19…75+ × sexe × 4 niveaux). Barro-Lee est aujourd'hui
  inaccessible en direct (certificat cassé sur barrolee.com) ; à récupérer via un
  miroir OWID avant d'activer.

## Généralisation 2 — Famille : distributions résolues par pays × âge × sexe

- **Aujourd'hui (lot 1)** : le résolveur `famille` lit des **paramètres globaux**
  (`DATA.family.params` : `young_early/late`, `elder_widow`, `mid_celibataire`,
  `mid_parent`, multiplicateurs `early_*`) plus la liste `early_parenthood`.
  C'est le modèle du seed, conservé faute d'accès aux distributions nationales.
- **Généralisation prévue** : distribution résolue `family[iso][age][sex]` sur
  les buckets famille, avec `parent_share` séparé, et repli sur les branches
  enfant / jeune / âgé si une case manque. Le résolveur lirait la distribution du
  pays pour l'âge et le sexe tirés.
- **Déclencheur d'activation** : disposer du **statut matrimonial par pays × âge
  × sexe** (ONU DESA World Marriage Data). Cette source est actuellement bloquée
  par la politique d'egress (`un.org` → 403). À récupérer via un miroir OWID ou
  la hiérarchie de repli avant d'activer.

## Principe conservé

Toute autre logique du moteur reste inchangée. Les deux généralisations, une fois
activées, resteront **data-driven** : le code choisit la profondeur de clé selon
la forme trouvée dans `DATA`, il n'y écrit jamais de chiffre pays. Tant que les
sources fines ne sont pas récupérées, le lot 1 utilise les résolveurs par pays /
paramètres globaux, ce qui garde `node validate.js` au vert et le jeu jouable.
