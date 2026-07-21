# Le Dé de la Vie

Jeu web qui tire une vie humaine au hasard, étape par étape, pondérée par de vraies données démographiques. Le message (prendre conscience de sa chance) passe par le jeu, pas par un discours.

## Principe d'architecture

Les données sont séparées du code. Le moteur (`engine.js`) est générique : il ne contient aucun chiffre pays. Tout vient des fichiers `data/*.json`, conformes à `schema.json`. Ajouter un pays, c'est ajouter des lignes de données, jamais toucher au code.

## Bilingue (FR / EN)

L'interface est disponible en français et en anglais. Toutes les chaînes visibles sont externalisées dans un objet de traductions `I18N = { fr, en }` en tête de `engine.js` (titres, étapes, légendes, portrait final, question d'échange, boutons, fenêtre « voir les probas », libellés de source). Le markup statique porte des attributs `data-i18n`, remplis à l'affichage.

- **Sélecteur de langue** : un bouton `FR / EN` visible en bas à droite (en haut au centre sur mobile). Le choix est mémorisé (`localStorage`).
- **Détection auto** : au premier chargement, la langue suit celle du navigateur (`fr*` → français, sinon anglais).
- **Données** : les noms de pays viennent de `name_fr` / `name_en`, les libellés de dimensions de `label_fr` / `label_en` (`schema.json`). Aucune logique de données n'est traduite : on ne touche qu'aux chaînes d'interface.
- **Grammaire du portrait** : gabarit de phrase distinct par langue. Le français emploie la préposition `en / au / aux` (champ `prep` de `countries.json`) devant le nom français ; l'anglais emploie « in » devant le nom anglais.

Le changement de langue est instantané et reconstruit l'écran courant (partie en cours, portrait final, fenêtre des probas), y compris en plein milieu d'une vie.

## Structure

```
index.html        page servie (markup + styles), charge engine.js et les données
engine.js         moteur générique data-driven (tirage conditionnel, compteur, UI)
schema.json       le contrat de données (buckets figés, forme des tables, sources, repli)
build_seed.py     génère les data du seed (7 pays) depuis des paramètres bruts
validate.js       vérifie data/ contre schema.json
data/
  countries.json   niveau 1, poids population + table de référence
  age_sex.json     niveau 2, jointe âge x sexe par pays
  settlement.json  niveau 3, milieu de vie
  income.json      niveau 4, position mondiale de revenu
  education.json   niveau 5, base + facteurs
  health.json      niveau 6, base + facteurs (états dérivés des YLD GBD)
  family.json      niveau 7, paramètres de branches matrimoniales
  living.json      niveau 8, accès électricité, internet, eau
```

## Lancer

En local, servir le dossier (le jeu charge `data/` via fetch) :

```
cd projet
python3 -m http.server 8000
# ouvrir http://localhost:8000
```

`index.html` embarque aussi une copie du seed en repli, donc il tourne même ouvert en fichier local (`file://`) si le fetch échoue. La version `de-de-la-vie-autonome.html` fournie à part est entièrement autonome (tout inline, `index.html` + `engine.js` fusionnés), pratique pour un aperçu sans serveur. On la régénère depuis les sources avec :

```
node -e 'const fs=require("fs");let h=fs.readFileSync("index.html","utf8");const e=fs.readFileSync("engine.js","utf8");fs.writeFileSync("de-de-la-vie-autonome.html",h.replace(String.raw`<script src="engine.js"></script>`,"<script>\n"+e+"\n</script>"));'
```

## Valider les données

```
node validate.js
```

Vérifie que chaque distribution somme à 1, que tous les pays du domaine sont présents dans chaque table, qu'aucun bucket inconnu n'est utilisé, et que les valeurs sont dans les bornes. Sort en erreur sinon.

## Ajouter des pays

Deux façons. Soit étendre `build_seed.py` avec les paramètres bruts d'un pays et relancer `python3 build_seed.py`. Soit écrire directement les lignes dans les 8 fichiers `data/*.json` en respectant `schema.json`. Dans les deux cas, relancer `node validate.js`.

## Suite (pour Claude Code)

1. Remplir `data/` pour les 195 pays, source par source, contre `schema.json`.
2. Prioriser par population (Inde, Chine, puis les gros pays couvrent l'essentiel du poids du tirage). Le jeu est crédible dès une vingtaine de pays.
3. Figer une fois pour toutes la méthode de passage des YLD du GBD vers les 4 bandes de sévérité (niveau 6), et les facteurs éducation, avant de dérouler les 195 pays.
4. Renseigner le champ `coverage` de chaque valeur (national, regional, income_group, world) selon la hiérarchie de repli du schéma. Aucune valeur inventée.
5. Lancer `node validate.js` à chaque lot.

Les 7 pays actuels (France, Autriche, États-Unis, Brésil, Inde, Chine, Niger) sont un seed dont les chiffres sont approximatifs mais dirigés par les vraies distributions. Ils servent de patron de forme, à remplacer par les données sourcées.
