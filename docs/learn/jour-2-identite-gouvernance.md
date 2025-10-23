# Jour 2 — Identité (Entra), RBAC et gouvernance

Objectifs du jour:
- Mettre en place les prérequis Entra ID: MFA, PIM, comptes break-glass, Conditional Access.
- Définir RBAC: groupes, rôles, scoping (subscription vs resource group) et séparation des devoirs.
- Comprendre l'alignement gouvernance/politiques avec les besoins FSI.

Parcours guidé (120–150 min):
- Quick start RBAC (checklist exécutable): `docs/azure-fsi/deployment/RBAC-QUICKSTART.md`
- Spécification détaillée (pour sécurité/compliance): `docs/azure-fsi/deployment/rbac-specification.md`
- Architecture rings → portée des rôles par RG: `docs/azure-fsi/architecture/rings.md`

Points clés à valider:
- Groupes Entra par rôle (Cloud Platform, Security, Network, DevOps, App, Auditors, Emergency Responders).
- PIM pour rôles sensibles (Owner, User Access Administrator) — activation JIT, MFA, approbation, justification.
- Conditional Access de base (MFA, blocage legacy auth, géorestriction non-EU, device conforme, blocage sign-in à risque).
- Comptes d'urgence « break-glass » (exclus CA, stockage sécurisé, alerte de connexion).

Attention exactitude/licences:
- PIM requiert Microsoft Entra ID P2. Si vous n'êtes pas certain·e des licences en vigueur, écrivez « Je ne sais pas » et consultez la sécurité.

Sources:
- [Microsoft Microsoft Entra ID PIM — Licences](https://learn.microsoft.com/entra/id-governance/licensing-fundamentals#valid-licenses-for-pim)
- [Microsoft Azure RBAC overview](https://learn.microsoft.com/azure/role-based-access-control/overview)
- [Microsoft Azure built-in roles](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles)
- [Microsoft Conditional Access overview](https://learn.microsoft.com/entra/identity/conditional-access/overview)
- [Microsoft Break-glass accounts](https://learn.microsoft.com/entra/identity/role-based-access-control/security-emergency-access)

