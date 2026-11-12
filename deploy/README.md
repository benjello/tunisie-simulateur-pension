# Déploiement

L'app Shiny de pension calcule via OpenFisca-Tunisia (package
`openfisca_tunisia_pension`). Deux architectures possibles :

## Retenue : moteur en direct sur shinyapps.io (un seul service)

L'app importe `openfisca_tunisia_pension` et calcule **dans le même process**
(`OPENFISCA_MODE=local`). Rien d'autre à héberger. C'est l'approche du
simulateur de paie. Voir [`shinyapps/README.md`](shinyapps/README.md).

```bash
deploy/shinyapps/push.sh benjello simulateur-pension-tunisie
```

> ⚠️ Nécessite openfisca-tunisia **≥ 0.164** (correctif d'éligibilité « 120
> mois », PR #527). Attendre la publication PyPI de 0.164, ou utiliser le
> fallback git dans `shinyapps/requirements.txt`.

## Alternative : API OpenFisca hébergée séparément (deux services)

Héberger `openfisca serve --country-package openfisca_tunisia_pension` (Docker :
HF Space, VPS, Fly.io…) et pointer l'app via `OPENFISCA_API_URL=https://…`
(mode `api`, le défaut). Plus « pur » architecturalement, mais deux services à
maintenir et une API publique à exposer. Non outillé ici (voir le dépôt paie
pour un `Dockerfile.api` de référence).

> Rappel : déploiement 100 % navigateur (GitHub Pages / WebAssembly) impossible
> tant qu'OpenFisca importe `pendulum`/`numexpr`/`psutil` (absents de Pyodide).
