# Test d'atteignabilité des sources — 2026-07-21

Une requête par domaine source (via le proxy d'egress). Méthode : `curl -sL -m 30 -o /dev/null -w "%{http_code}"` avec le bundle CA `/root/.ccr/ca-bundle.crt`.

Codes : `200` OK · `401` authentification requise · `403` refus de politique d'egress (à signaler, ne pas réessayer) · `000` échec connexion/TLS · `404`/`400` serveur joignable, chemin à préciser.

## Sources directement exploitables

| Domaine / endpoint | Code | Usage (niveau) |
|---|---|---|
| `population.un.org/dataportalapi/api/v1/indicators/` | 200 | métadonnées WPP (listes) |
| `population.un.org/dataportalapi/api/v1/locations` | 200 | domaine pays WPP (niveau 1) |
| `pip.worldbank.org/api/pip?...` | 200 | revenu, déciles PIP (niveau 4) |
| `api.worldbank.org/v2/country/.../indicator/...` | 200 | WDI : income_group, électricité, internet, population (niveaux 1, 8) |
| `washdata.org` | 200 | JMP eau potable (niveau 8) |
| `datahub.itu.int` | 200 | ITU internet (niveau 8) |
| `ghdx.healthdata.org` / `vizhub.healthdata.org/gbd-results/` | 200 | GBD, outil de résultats (niveau 6) |
| `catalog.ourworldindata.org` | 200 (host) | catalogue OWID réharmonisé |
| `raw.githubusercontent.com/owid/...` | 200 | **raccourci OWID** (niveaux 1, 4, 5, 8) |

## Sources gated (authentification requise)

| Endpoint | Code | Note |
|---|---|---|
| `population.un.org/dataportalapi/api/v1/data/indicators/...` | 401 | Les endpoints **données** du Data Portal exigent un jeton (les endpoints métadonnées passent). Repli : WPP via OWID, ou API WDI population. |

## Sources bloquées par la politique d'egress (403 — signalées, non réessayées)

| Domaine | Code | Impact | Repli |
|---|---|---|---|
| `uis.unesco.org`, `data.uis.unesco.org` | 403 | scolarisation enfant (niveau 5) | OWID (UNESCO réharmonisé), sinon hiérarchie de repli |
| `www.un.org` (World Marriage Data) | 403 | statut matrimonial (niveau 7) | OWID / repli régional ; `population.un.org` reste joignable |
| `github.com`, `api.github.com` | 403/400 | — | utiliser `raw.githubusercontent.com` (200) |

## Sources à certificat cassé

| Domaine | Détail | Repli |
|---|---|---|
| `barrolee.com` | TLS : le certificat ne correspond pas au nom d'hôte (`no alternative certificate subject name matches`) | Barro-Lee est disponible via OWID |

## Conclusion

Le cœur des sources est joignable : **PIP** (revenu), **World Bank WDI** (groupes de revenu, conditions de vie), **JMP**, **ITU**, **GBD**, et surtout le **raccourci OWID** via `raw.githubusercontent.com`, qui réharmonise PIP/WPP/Barro-Lee/WDI en CSV propres à codes ISO3 (recommandé par MISSION.md pour les niveaux 1, 4, 5-adulte, 8).

Trois frictions à contourner via OWID + la hiérarchie de repli du schéma :
1. **WPP Data Portal** : endpoints données en 401 (jeton requis) → population et âge×sexe via OWID/WDI.
2. **UNESCO UIS** (403) : scolarisation enfant → OWID.
3. **World Marriage Data un.org** (403) : statut matrimonial → OWID / repli régional.

Aucune valeur ne sera inventée : chaque valeur portera son `source_id`, `year` et `coverage` réels, et tout brut sera mis en cache dans `data/raw/` avec son URL de requête.
