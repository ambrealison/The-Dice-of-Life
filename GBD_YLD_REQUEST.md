# GBD_YLD_REQUEST.md — obtenir le fichier YLDs (requête B) via la demande groupée

Marche à suivre exacte pour récupérer l'export GBD qui permettra de passer les
**4 bandes de sévérité physique** en données nationales (`severity_base[iso][âge]
[sexe]`, coverage `national`). À lancer quand tu auras le temps ; on branchera la
sévérité physique à la réception du fichier. (La santé mentale, elle, est déjà
intégrée en national.)

## 1. Où : la demande groupée

Outil : **GBD Results** — https://vizhub.healthdata.org/gbd-results/ (connecté à
ton compte GHDx). Quand la sélection dépasse la limite de téléchargement direct,
le bouton **« Download »** propose une **demande groupée** (« We'll email you a
link when it's ready » / *Request a large data set*). C'est ce mode qu'on vise :
il accepte les gros volumes et t'envoie un lien par courriel.

## 2. Réglages exacts du formulaire

Sélectionne **exactement** ceci (un seul export suffit) :

| Champ | Valeur |
|---|---|
| **GBD Round / Cycle** | GBD 2023 (ou 2021 si 2023 indisponible) |
| **Measure** | **YLDs (Years Lived with Disability)** ET **Prevalence** |
| **Metric** | **Rate** ET **Number** |
| **Cause** | **All causes** (total) **+** toutes les causes de **Niveau 2** (Level 2) |
| **Location** | les 23 pays du domaine (liste §4) |
| **Age** | tous les groupes 5 ans : `<5, 5-9, 10-14, 15-19, 20-24, 25-29, 30-34, 35-39, 40-44, 45-49, 50-54, 55-59, 60-64, 65-69, 70-74, 75-79, 80-84, 85-89, 90-94, 95+` |
| **Sex** | **Male** et **Female** (pas « Both ») |
| **Year** | **2021** |
| **Context** | Cause (par défaut) |

> Pourquoi ce choix : le **YLD Rate par personne = poids d'incapacité moyen**
> (ancre la moyenne par cellule pays×âge×sexe) ; le détail **par cause de niveau 2**
> (musculo-squelettique, mental, sensoriel, cardio, etc.) donne la **forme de la
> distribution** du poids d'incapacité, nécessaire pour répartir dans les 4 bandes
> selon les seuils figés de `METHODS_health.md` (bonne <0.05, gêne 0.05-0.12,
> modérée 0.12-0.30, sévère >0.30). C'est volumineux mais borné : ~20 causes N2 ×
> 20 âges × 2 sexes × 23 pays × 2 mesures ≈ 37 000 lignes — la demande groupée
> passe sans souci.

**Variante minimale** (si tu veux un fichier plus léger d'abord) : garde tout
pareil mais **Cause = All causes** seulement (total). Ça me donne le poids
d'incapacité **moyen** par cellule ; je produirai alors les 4 bandes via un modèle
d'étalement documenté (marqué « modélisé », coverage national). La variante N2
ci-dessus reste préférable car elle reconstruit la vraie forme, pas seulement la
moyenne.

## 3. Ce que tu m'envoies

Le **CSV** (ou le zip) reçu par courriel — comme pour la santé mentale. Je le mets
en cache dans `data/raw/`, j'applique la méthode figée (`METHODS_health.md` §1-§5,
modèle de comorbidité multiplicatif), et je remplace `severity_base_group`
(coverage `income_group`) par `severity_base[iso][âge][sexe]` (coverage
`national`). Le résolveur santé du moteur lira alors la base nationale.

## 4. Les 23 pays (Location)

Inde, Chine, États-Unis, Indonésie, Pakistan, Nigéria, Brésil, Bangladesh,
Russie, Éthiopie, Mexique, Japon, Égypte, Philippines, RD Congo, Vietnam, Iran,
Turquie, Allemagne, Thaïlande, France, Autriche, Niger.

*(Noms tels qu'affichés par le portail : « Iran (Islamic Republic of) »,
« Türkiye », « Russian Federation », « Democratic Republic of the Congo »,
« United States of America », « Viet Nam ».)*
