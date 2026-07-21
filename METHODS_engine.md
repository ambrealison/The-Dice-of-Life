# METHODS_engine.md — généralisations de résolveur (documentation)

MISSION.md autorise deux généralisations du moteur (`engine.js`) pour la fidélité
complète, en gardant la logique **pilotée par la forme des données**, sans écrire
aucun chiffre pays dans le code. Ce document décrit les deux, et leur **statut**
pour le lot 1 (preuve de bout en bout : IND, CHN, USA).

## Généralisation 1 — Éducation : base par pays × groupe d'âge × sexe ✅ ACTIVÉE

- **Statut** : activée. Le résolveur `education` lit d'abord
  `DATA.education.attainment_by_age[iso][ageId][sex].shares` si présent, sinon
  se rabat sur la base pays `attainment_base[iso].shares`. La forme des données
  commande la profondeur ; aucun chiffre pays n'est écrit dans le code.
- **Source** : Barro-Lee 2010 par groupe d'âge et sexe, redistribué par World
  Bank EdStats (indicateurs `BAR.NOED/PRM.ICMP/SEC.ICMP/TER.ICMP.<age>[.FE].ZS`),
  agrégé vers les 6 buckets adultes pondéré population. Le masculin est
  reconstitué par pondération (WDI ne fournit que total + féminin). Détail :
  `collect_edu_age.py` et `METHODS_education.md`.
- **Effet** : corrige le ressenti « Chine tout en primaire ». Ex. Chine 20-34 :
  secondaire passe de ~24 % (base 25+) à ~82 % ; Chine 65-79 F : sans école
  ~39 % (cohortes âgées moins scolarisées) ; Inde 20-34 F : secondaire ~44 %.
- **Compatibilité facteurs** : quand la base sexuée est utilisée, le facteur
  `gender_gap` est **désactivé** (le sexe est déjà dans la base, sinon double
  compte) ; `rural_penalty` et `income_prime` continuent de s'appliquer.
- **Couverture** : 21/23 pays du domaine. NGA et ETH n'ont pas de série
  Barro-Lee par âge dans WDI → repli sur la base pays (attainment_base).

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
