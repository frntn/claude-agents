# Jour 1 — Fondamentaux Azure et contexte FSI

Objectifs du jour:
- Comprendre tenant, abonnement, management groups, resource groups, régions, zones, tags et conventions.
- Situer les exigences FSI: souveraineté, gouvernance, conformité, traçabilité.
- Préparer l'environnement local et valider l'installation du dépôt.

À faire (90–120 min):
- Lecture guidée repo:
  - `README.md` (vue d'ensemble du dépôt)
  - `docs/getting-started.md` (mise en route)
  - `docs/azure-fsi/README.md` (capabilités et modes solo/squad)
- Mise en place locale:
  - `./scripts/setup.sh`
  - `source .venv/bin/activate`
  - `uv run python scripts/test_setup.py`
- Vérification basique:
  - `uv run pytest tests/test_repository.py` (optionnel si l'environnement est déjà validé)

Concepts indispensables (récap):
- Tenant vs Subscription: séparation identité/locataire vs facturation/limite administrative.
- Management Groups: hiérarchie pour spolitiques (Azure Policy), RBAC, et gouvernance multi-subscriptions.
- Resource Groups: frontière de cycle de vie et de déploiement (Bicep), scoping RBAC le plus fréquent.
- Régions/Zones: latence, disponibilité, résidence des données; préférer EU pour FSI (ex. `francecentral`, `westeurope`).
- Nommage/Tags: cohérence, filtrage, coûts, conformité.

Références dans le repo:
- Ring-Based Architecture: `docs/azure-fsi/architecture/rings.md` (vision progressive ring0→ring2)

Sources :
- [Microsoft Cloud Adoption Framework — Azure landing zones](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/)
- [Microsoft Subscriptions and management groups](https://learn.microsoft.com/azure/governance/management-groups/overview)
- [Microsoft Resource groups](https://learn.microsoft.com/azure/azure-resource-manager/management/manage-resource-groups-portal)
- [Microsoft Azure regions](https://learn.microsoft.com/azure/reliability/availability-zones-overview)
- [Microsoft Resource tagging](https://learn.microsoft.com/azure/azure-resource-manager/management/tag-resources)
