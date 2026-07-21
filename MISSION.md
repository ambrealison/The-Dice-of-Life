# Mission Claude Code : constituer les données du Dé de la Vie

Tu reprends un projet existant et fonctionnel. Une app web data-driven tourne déjà, avec un moteur générique (`engine.js`), un contrat de données (`schema.json`), un validateur (`validate.js`) et un seed de 7 pays dans `data/`. Ta mission n'est pas de refaire l'app. Ta mission est de remplir `data/` pour tous les pays, source par source, en respectant le contrat.

Lis d'abord `schema.json`, `README.md`, et un des fichiers `data/*.json` du seed pour voir la forme exacte attendue. Le seed est ton patron. Ne change pas sa structure, remplace ses chiffres approximatifs par des chiffres sourcés et étends le domaine à tous les pays.

## Règles non négociables

1. Tout doit rester conforme à `schema.json`. Les ids de buckets sont figés, ne les renomme jamais.
2. N'invente jamais une valeur. Si une donnée nationale manque, applique la hiérarchie de repli et marque `coverage` en conséquence. Une estimation régionale honnête vaut mieux qu'un chiffre inventé étiqueté national.
3. Chaque valeur porte sa provenance (`source_id`, `year`, `coverage`). Renseigne le champ `retrieved` de chaque source dans le manifeste au moment de la collecte.
4. Cache chaque téléchargement brut dans `data/raw/` et sauvegarde à côté l'URL de requête exacte. La collecte doit être reproductible et auditable.
5. Harmonise tout en code pays ISO3 avant de bucketiser.
6. Fige et documente les méthodes délicates (bandes de sévérité GBD, facteurs éducation) avant de dérouler tous les pays. Applique-les identiquement partout.
7. Lance `node validate.js` après chaque lot. Ne considère pas un lot terminé tant qu'il n'est pas au vert.
8. Livre par lots, priorisés par population. Le jeu doit rester jouable et crédible en cours de route.

## Environnement à prévoir

Accès réseau aux domaines : population.un.org, pip.worldbank.org, ghdx.healthdata.org, vizhub.healthdata.org, barrolee.com, data.uis.unesco.org, uis.unesco.org, un.org, data.worldbank.org, washdata.org, datahub.itu.int, github.com et raw.githubusercontent.com (pour Our World in Data). Python 3 avec pandas, et Node pour le validateur.

Raccourci recommandé : Our World in Data (github.com/owid, ou le paquet pip `owid-catalog`) a déjà réharmonisé PIP, WPP, Barro-Lee et une partie du WDI en CSV propres sous licence CC BY, avec les codes ISO3. Pour les niveaux 1, 4, 5 (partie adulte) et 8, passe par OWID pour gagner du temps, tout en citant la source primaire dans le manifeste. Réserve l'accès aux sources primaires directes aux niveaux qu'OWID couvre mal (âge x sexe fin, santé détaillée, statut matrimonial).

## Playbook par niveau

### Niveau 1 : countries.json (WPP 2024)
Domaine : les pays souverains de WPP 2024, environ 195. Décide d'inclure ou non les territoires, documente le choix. Pour chaque pays : population totale (année 2024), `name_fr`, `name_en`, `region` (sous-région ONU M49), `income_group` (classification Banque mondiale, low, lower_middle, upper_middle, high), `prep` (préposition française, voir plus bas), `coverage` national.
Accès : API du portail ONU (population.un.org/dataportalapi) indicateur population totale, ou CSV bulk WPP. Groupe de revenu depuis le fichier de classification Banque mondiale. La préposition FR se dérive par règle : `aux` pour les noms pluriels (États-Unis, Pays-Bas, Émirats arabes unis), `au` pour un masculin singulier commençant par une consonne (Niger, Brésil, Maroc, Japon), `en` pour les féminins et ceux commençant par une voyelle (France, Inde, Autriche, Iran). Prévois une liste de correction à la main pour les cas ambigus.

### Niveau 2 : age_sex.json (WPP 2024)
Accès : indicateur population par âge et sexe, année 2024, par pays. WPP est natif en tranches de 5 ans. Agrège vers les 8 buckets du schéma (a00_04, a05_14, a15_19, a20_34, a35_49, a50_64, a65_79, a80p). Pour chaque pays, calcule les 16 parts jointes `ageid|F` et `ageid|M` (part = population du segment sur population totale). La somme des 16 fait 1. Coverage national partout, WPP couvre tout le domaine.

### Niveau 3 : settlement.json (WUP 2025)
Accès : degré d'urbanisation dans le portail ONU (WUP 2025 y est intégré). Mappe les trois degrés vers grande, ville, rural. Si un pays n'a que le pourcentage urbain sans découpage ville/grande ville, répartis l'urbain avec un ratio régional et marque `coverage` regional. Parts par pays, somme 1.

### Niveau 4 : income.json (PIP, complété WID)
Accès : jeu Percentiles de PIP (licence CC0), déciles de revenu ou consommation par pays, enquête la plus récente. Complète les pays à haut revenu peu couverts par PIP avec WID.
Traitement clé : construis d'abord une distribution mondiale de référence (`data/income_world_ref.json`) en empilant les revenus moyens de déciles de tous les pays, pondérés par population, sur l'échelle en dollars PPA. Pour chaque quintile national, prends son revenu moyen, place-le sur cette distribution mondiale, et stocke le percentile mondial obtenu. Résultat par pays : `global_percentile` de 5 valeurs. Stocke aussi `decile_thresholds_ppp` si tu l'as. Repli income_group pour les pays sans enquête.

### Niveau 5 : education.json (Barro-Lee, UNESCO UIS, facteurs DHS)
Base adultes : Barro-Lee attainment par pays, groupe d'âge et sexe. Agrège les niveaux vers les 4 buckets (aucune, primaire, secondaire, superieur). Important, passe la base en clé par pays x groupe d'âge adulte x sexe (voir adaptations moteur plus bas), Barro-Lee le permet.
Enfants : UIS, taux net de scolarisation ou hors-école, par pays et sexe, pour remplir `child_enrollment.in_school`.
Facteurs : calibre `rural_penalty` et `income_prime` sur les enquêtes DHS et MICS (fréquentation scolaire par lieu de résidence et quintile de richesse), en prenant l'effet multiplicatif moyen sur les pays enquêtés, appliqué globalement. `gender_gap` par pays depuis le ratio hommes-femmes de Barro-Lee, là où l'écart est significatif. Après application des facteurs, renormalise à 1.

### Niveau 6 : health.json (IHME GBD 2023)
C'est le niveau le plus délicat. Accès : GBD Results Tool (vizhub.healthdata.org/gbd-results), prévalence des séquelles avec leurs disability weights, et prévalence des troubles mentaux et addictifs, par pays, âge et sexe.
Méthode à figer et documenter dans `METHODS_health.md` avant de dérouler les pays :
1. Pour chaque pays x âge x sexe, reconstitue la distribution du poids d'incapacité par personne, en appliquant le modèle de comorbidité multiplicatif du GBD (une personne peut cumuler des séquelles).
2. Range chaque personne dans une des 4 bandes selon son poids d'incapacité corrigé, avec des seuils fixes à décider et documenter, par exemple bonne inférieur à 0.05, gene_legere de 0.05 à 0.12, incap_moderee de 0.12 à 0.30, incap_severe supérieur à 0.30.
3. Les 4 parts par pays x âge x sexe forment `severity_base`. Passe de la base par groupe (rich, mid, low) du seed à une vraie base par pays x âge x sexe.
`mental` : prévalence d'au moins un trouble mental ou addictif par pays x âge x sexe. `income_penalty` : calibre le gradient par quintile sur la relation pauvreté-santé du GBD par SDI. Dignité, on décrit un niveau de limitation, jamais une liste de pathologies nommées.

### Niveau 7 : family.json (ONU DESA Marriage Data, DHS)
Accès : World Marriage Data, statut matrimonial (jamais marié, marié ou en union, veuf, divorcé) par pays x âge x sexe. Mappe vers célibataire, couple, veuf. Sépare couple de parent avec la part de parents par âge et sexe (DHS, recensements). Gère les branches enfant (ages a00_04 et a05_14) et jeune (a15_19).
Recommandation, passe d'un modèle par paramètres globaux (le seed) à des distributions résolues par pays x âge x sexe sur les buckets famille (voir adaptations moteur).

### Niveau 8 : living.json (WDI, JMP, ITU)
Accès : électricité et internet depuis WDI et ITU, eau potable depuis le JMP OMS-UNICEF, par pays et si possible par milieu urbain-rural. Stocke la probabilité d'accès par pays x settlement pour électricité, internet, eau. Assainissement et cuisson en option. Si le découpage rural-urbain manque, garde la valeur nationale et applique la `rural_penalty` du fichier.

## Harmonisation

Tout en ISO3 avant bucketisation. Année cible 2024, sinon l'année disponible la plus proche (et note-la dans `year`). Agrège les tranches d'âge sources vers les 8 buckets. Noms FR et EN cohérents. Region et income_group depuis les classifications officielles, ils servent au repli.

## Repli

Applique table par table, dans l'ordre : national, national année proche, régional (moyenne pondérée par population des pays de la sous-région qui ont la donnée), groupe de revenu, mondial. Chaque valeur produite porte son vrai `coverage`. Produis un `COVERAGE_REPORT.md` listant, par table et par pays, le niveau de couverture obtenu.

## Adaptations moteur autorisées

Le seed a pris deux raccourcis. Pour la fidélité complète, tu es autorisé à généraliser deux résolveurs dans `engine.js`, en gardant leur logique pilotée par la forme des données, sans y écrire de chiffre pays :
1. Éducation, base par pays x groupe d'âge x sexe au lieu d'une base unique par pays. Le résolveur sélectionne la base selon l'âge et le sexe tirés.
2. Famille, distributions résolues par pays x âge x sexe au lieu des paramètres globaux. Le résolveur lit la distribution du pays pour l'âge et le sexe tirés, avec repli sur les branches enfant, jeune, âgé si une case manque.
Toute autre logique du moteur reste inchangée. Documente ces deux changements.

## Critères d'acceptation

Un lot est accepté si `node validate.js` passe au vert, si chaque distribution somme à 1, si tous les pays du lot sont présents dans chaque table avec un `coverage` renseigné, si aucun bucket inconnu n'apparaît, et si un contrôle de cohérence ne révèle aucun profil aberrant (un diplômé du supérieur en zone rurale extrêmement pauvre reste possible mais jamais dominant). Le jeu doit se jouer de bout en bout sur les pays du lot.

## Ordre de marche

1. Remplir countries.json (domaine complet, population, region, income_group, prep).
2. Niveaux 2 et 3 (âge-sexe, milieu), distributions directes WPP et WUP.
3. Niveau 4, avec la table mondiale de référence.
4. Figer et documenter la méthode santé et les facteurs éducation.
5. Niveaux 5, 6, 7 (base plus facteurs et distributions résolues).
6. Niveau 8.
7. Passe de repli, marquage coverage, COVERAGE_REPORT.md.
8. Validation complète.
Livraison par lots priorisés par population, l'Inde et la Chine d'abord, puis les vingt pays les plus peuplés, puis le reste.

## Livrables

Un dossier `data/` rempli pour tous les pays, `data/income_world_ref.json`, `data/raw/` avec les bruts et leurs URLs, `METHODS_health.md`, `COVERAGE_REPORT.md`, le manifeste des sources avec les dates de collecte renseignées, et les deux généralisations de résolveur documentées. Validateur au vert.
