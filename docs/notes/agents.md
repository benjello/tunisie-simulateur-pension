# Gestion des agents (transmise depuis le chantier paie)

Ce dépôt dispose de la même gestion d'agents que `tunisie-simulateur-paie`.

## Source unique + génération

- **Source de vérité** : `.pi/agents/*.md` (frontmatter name/description/tools/model).
- **Script** : `scripts/deploy_agents.sh` régénère les autres formats et peut
  déployer en user.

```bash
scripts/deploy_agents.sh           # régénère .claude/agents/ et .opencode/agent/ (projet)
scripts/deploy_agents.sh --global  # + user : ~/.pi/agent/agents, ~/.claude/agents, ~/.config/opencode/agent
scripts/deploy_agents.sh --check   # vérifie la synchro (CI), sans écrire
```

N'éditer que `.pi/agents/*.md`, puis relancer le script.

## Agents disponibles

| Agent | Modèle | Outils | Rôle |
|---|---|---|---|
| `analyste-pension` | Haiku | lecture seule | Module `openfisca_tunisia_pension` : régimes, salaire de référence, taux d'annuité, bonifications. Vérifie par le calcul (TunisiaPensionTaxBenefitSystem, numba). |
| `analyste-openfisca` | Haiku | lecture seule | Modèle OpenFisca-Tunisia général. |
| `juriste-fiscal-tn` | Sonnet | lecture + web | Droit fiscal/social tunisien, tranche les désaccords par le texte. |

Les trois sont **déjà déployés en user** (`--global`) : reconnus depuis
n'importe quel répertoire de travail. `analyste-pension` est le profil à
privilégier pour ce chantier.
