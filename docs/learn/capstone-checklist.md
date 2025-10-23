# Capstone — Checklist de mise en main (fin de semaine)

But: démontrer que vous pouvez piloter ce repo et engager un déploiement ring-based minimal conforme aux bonnes pratiques FSI.

Préparation (cocher):
- [ ] Environnement local validé (`scripts/setup.sh`, tests de base ok)
- [ ] Groupes Entra créés (CloudPlatform, Security, Network, DevOps, App, Auditors, Emergency)
- [ ] RBAC Option A ou B sélectionnée et affectée au bon scope (sub/RG)
- [ ] PIM activé (Owner/UAA éligibles, MFA/approbation/justification)
- [ ] CA de base en place (MFA, legacy, géo, device, risk)
- [ ] Comptes break-glass créés, exclus CA, alertes configurées

Atelier déploiement (ring-based):
- [ ] Stratégie choisie: `ring0 (minimal)` seul OU `ring0 + ring2 (minimal)`
- [ ] Agent FSI exécuté (solo ou squad) pour générer les templates Bicep attendus
- [ ] Templates AVM inspectés (références `br/public:avm/...` conformes)
- [ ] Diagnostics centralisés configurés (Log Analytics)
- [ ] Accès public désactivé sur ressources sensibles (KV/Storage, si applicable)

Conformité et coût:
- [ ] Agent de conformité exécuté, rapport exporté (Markdown/JSON)
- [ ] 2–3 écarts identifiés + remédiations planifiées
- [ ] Estimation Pricing Calculator produite (URL conservée), hypothèses notées

Handover (documentation interne):
- [ ] Diagramme réseau (hub/spoke, endpoints privés, flux principaux)
- [ ] Tableau RBAC (groupes → rôles → scopes)
- [ ] Hypothèses d'estimation (région, retention logs, env)
- [ ] Registre des décisions (ex: `Option A/B`, depths, Rings déployés)

Références à utiliser:
- Rings: `docs/azure-fsi/architecture/rings.md`
- RBAC: `docs/azure-fsi/deployment/RBAC-QUICKSTART.md`
- AVM: `docs/azure-fsi/implementation/avm-usage.md`
- Compliance: `agents/azure-compliance-checker/README.md`

