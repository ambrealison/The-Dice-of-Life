# UN_MARRIAGE_REQUEST.md — obtenir le statut matrimonial complet (famille nationale)

Marche à suivre pour récupérer la distribution **complète** du statut matrimonial
(jamais marié / marié-union / veuf / divorcé) par pays × âge × sexe, qui
permettra de finir la **famille nationale** : nationaliser le **veuvage** et la
**parentalité**, et activer entièrement la généralisation 2 du moteur. À garder
pour plus tard ; rien à lancer maintenant.

État actuel : le calendrier **célibataire ↔ couple** est déjà national (via le
SMAM, WDI) ; il ne manque que le veuvage et le partage couple/parent nationaux.
Voir `METHODS_family.md`.

## Contexte d'accès (pourquoi ce n'est pas déjà fait)

- **World Marriage Data** (ONU DESA), le jeu qui contient les 4 statuts par âge ×
  sexe, est distribué en fichier sur `un.org` → **bloqué par la politique
  d'egress ici** (403). Ce n'est pas une question de compte : le blocage est réseau.
- Le **UN Data Portal API** (`population.un.org/dataportalapi`) est joignable, mais
  ses endpoints **données** exigent un **jeton** (401) et n'exposent que
  « Currently married » (indicateurs 42-45), pas les 4 statuts complets.

Deux routes, par ordre de préférence.

## Route A (recommandée) — télécharger le fichier World Marriage Data et me l'envoyer

C'est le même schéma que pour la santé mentale (tu télécharges, tu m'envoies le
fichier ; je fais le reste). `un.org` n'est pas bloqué depuis ta machine.

1. **Page** : https://www.un.org/development/desa/pd/data/world-marriage-data
   (« World Marriage Data 2019 », ou l'édition la plus récente).
2. **Télécharger** le classeur Excel complet (`UN_WorldMarriageData_2019.xlsx`
   ou équivalent). Il contient, par pays × groupe d'âge × sexe, les pourcentages :
   **Single (never married)**, **Married**, **Widowed**, **Divorced**,
   **Separated**, et souvent **Married or in union**.
3. **Ce dont j'ai besoin dans le fichier** (garde toutes les colonnes, je trie) :
   `Country`, `ISO`/code, `Sex`, `Age group`, l'`année` de la source, et les
   colonnes de statut ci-dessus en **pourcentage**. Prends la ligne d'année la
   plus récente par pays.
4. **M'envoyer** le `.xlsx` (ou un `.csv` exporté). Je le mets en cache dans
   `data/raw/`, je mappe vers les buckets famille (célibataire / couple / veuf /
   parent) et les 8 tranches d'âge, et je passe le résolveur famille en
   distributions entièrement nationales.

## Route B (alternative partielle) — jeton API du UN Data Portal

Ne débloque que « Currently married » (part mariée par âge, et par âge de la
femme) — utile pour valider/affiner la part en couple, mais **sans veuvage ni
divorce**. À réserver si la Route A n'est pas possible.

1. **Compte / jeton** : s'inscrire sur https://population.un.org/dataportal/about/dataapi
   et générer un **API token** (Bearer).
2. **Endpoint** (exemple, Inde = location 356, « Currently married by age of
   woman » = indicateur 44) :
   ```
   GET https://population.un.org/dataportalapi/api/v1/data/indicators/44/locations/356/start/2015/end/2024
   Header:  Authorization: Bearer <TON_TOKEN>
   ```
   Indicateurs utiles : **42** Currently married (Percent), **44** Currently
   married by age of woman (Percent).
3. **M'envoyer** le token (ou les JSON exportés) + je requête les 23 pays.
   Je nationaliserai la part mariée ; veuvage/parentalité resteraient au repli
   documenté faute des statuts complets.

## Ce que je fais à réception

- Route A → `family` complet : `family[iso][âge][sexe]` sur {célibataire, couple,
  parent, veuf}, coverage **national**, généralisation 2 du moteur pleinement
  activée (fin du repli `elder_widow` et du partage parent global).
- Route B → part mariée nationale branchée en complément du SMAM ; le reste en
  repli documenté.

## Les 23 pays

Inde, Chine, États-Unis, Indonésie, Pakistan, Nigéria, Brésil, Bangladesh,
Russie, Éthiopie, Mexique, Japon, Égypte, Philippines, RD Congo, Vietnam, Iran,
Turquie, Allemagne, Thaïlande, France, Autriche, Niger.
