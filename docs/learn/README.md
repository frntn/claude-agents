# Parcours d'onboarding Azure FSI — 5 jours

Objectif: en 5 jours, amener un·e débutant·e sur Azure (secteur Finance) à comprendre les concepts clés, les bonnes pratiques FSI, et à prendre en main ce dépôt pour préparer et déployer une Landing Zone Azure conforme (rings, depths, Bicep/AVM, RBAC/Entra, coûts, licences).

Public cible:
- Equipes IT/plateforme, sécurité/compliance, DevOps entrant sur Azure et le FSI.

Prérequis techniques minimaux:
- Python 3.10+, Azure CLI, accès à un abonnement de test, ANTHROPIC_API_KEY en `.env`.
- Installation repo: `./scripts/setup.sh` puis `source .venv/bin/activate` et `uv run python scripts/test_setup.py`.

Comment suivre le parcours:
- Avancez « par jour », exécutez les mini-labs, et cochez les checklists.
- Ne dupliquez rien: on lie systématiquement vers la documentation existante du repo et de Microsoft.

Plan de la semaine:
- Jour 1 — Fondamentaux Azure et FSI: `docs/learn/jour-1-fondamentaux-azure.md`
- Jour 2 — Identité, RBAC, gouvernance: `docs/learn/jour-2-identite-gouvernance.md`
- Jour 3 — Réseau, sécurité et rings: `docs/learn/jour-3-reseau-securite-rings.md`
- Jour 4 — Infrastructure as Code (Bicep/AVM) et déploiements: `docs/learn/jour-4-iac-bicep-avm.md`
- Jour 5 — Conformité, licences et coûts: `docs/learn/jour-5-compliance-licences-couts.md`
- Capstone — Checklist de mise en main: `docs/learn/capstone-checklist.md`

Livrables fin de semaine (attendus):
- Un projet d'atterrissage « Ring 0 (minimal) + Ring 2 (minimal) » prêt à générer/déployer via l'agent FSI.
- Un schéma d'architecture (hub/spoke, services clés) validé par les parties prenantes.
- Un plan RBAC/Entra (groupes, PIM, CA) coché dans `RBAC-QUICKSTART.md`.
- Une première estimation de coûts (méthode, hypothèses, capture du Pricing Calculator).

Liens repo utiles:
- Azure FSI Landing Zone (README): `docs/azure-fsi/README.md`
- Ring-Based Architecture: `docs/azure-fsi/architecture/rings.md`
- RBAC Quick Start: `docs/azure-fsi/deployment/RBAC-QUICKSTART.md`
- AVM (implémentation): `docs/azure-fsi/implementation/avm-usage.md`

Notes d'exactitude et sources:
- Chaque module contient une section « Sources » avec références Microsoft Learn/Azure (consultées, vérifiables). Pour les coûts, aucune valeur chiffrée n'est garantie: utilisez le Pricing Calculator.

