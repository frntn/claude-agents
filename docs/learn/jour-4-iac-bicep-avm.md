# Jour 4 — IaC: Bicep + Azure Verified Modules (AVM) et déploiements

Objectifs du jour:
- Comprendre la logique Bicep (modulaire, déclaratif) et l'intérêt d'AVM (modules validés Microsoft).
- Générer/valider des templates pour le ring0/ring2 à partir de l'agent FSI.
- Savoir où et comment versionner/valider les templates dans ce repo.

Lecture repo (45–60 min):
- AVM (implémentation et versions): `docs/azure-fsi/implementation/avm-usage.md`
- Manifeste AVM: `agents/azure-fsi-landingzone/avm-modules.yaml`
- Exemples/validation: `agents/azure-fsi-landingzone/test_avm_templates.py`

Mise en pratique (60–90 min):
1) Exécutez l'agent FSI (solo ou squad) et demandez:
   - « Génère un template Bicep de hub VNet (Ring 0, minimal) qui utilise AVM. »
   - « Génère un template Storage/Key Vault avec diagnostics et accès privé. »
2) Validez les templates localement (si CLI/avm installés):
   - `cd agents/azure-fsi-landingzone && uv run pytest test_avm_templates.py` (optionnel selon env.)
3) Inspectez les modules référencés (ex: `br/public:avm/res/network/virtual-network:<version>`). Vérifiez cohérence des paramètres (tags, diagnostics, RBAC…)

Bonnes pratiques:
- Figez les versions AVM via le manifest YAML pour la reproductibilité.
- Centralisez diagnostics (Log Analytics), RBAC et tags.
- Préférez endpoints privés et `publicNetworkAccess: Disabled` sur les ressources sensibles.

## Déterminisme vs non‑déterminisme et garde‑fous anti‑hallucinations

Ce qui est non‑déterministe (varie entre exécutions)
- Réponses de l'agent (rédaction, exemples, noms de variables, suggestions). Toujours traiter comme des propositions à valider.
- Ordre/présentation des idées et alternatives proposées.

Ce qui doit être déterministe (ne doit pas varier)
- Versions AVM épinglées: `agents/azure-fsi-landingzone/avm-modules.yaml:1` (mêmes versions ⇒ mêmes modules).
- Compilation Bicep: à fichier + paramètres identiques, `az bicep build` produit le même ARM JSON.
- Garde‑fous Azure Policy (effet « Deny »): une policy correctement assignée à Ring 0 bloque un déploiement non conforme.
- Gating d'accès: RBAC + PIM (activation JIT, MFA, approbation) pour qui peut déployer.

Workflow anti‑hallucinations (à appliquer systématiquement)
- Génération (agent): limiter l'agent aux actions de génération/analyse, pas de déploiement direct. Sorties attendues: fichiers `.bicep` avec références AVM versionnées (`br/public:avm/...:<version>`).
- Validation hors ligne: `az bicep build --file <template>.bicep` (échec = correction requise). Inspecter manuellement `publicNetworkAccess`, diagnostics, TLS minimum.
- What‑if contrôlé (pas de changement d'état): `az deployment group what-if --resource-group rg-<project>-<env> --template-file <template>.bicep`.
- Garde‑fous Policy (Ring 0): assignations qui refusent les écarts critiques (EU‑only, diagnostics requis, pas d'accès public). Voir `docs/azure-fsi/architecture/rings.md:1`.
- Revue humaine et tests: versionner les `.bicep`, relecture par pair, tests de validation `agents/azure-fsi-landingzone/test_avm_templates.py:1`.
- Conformité: exécuter l'agent de conformité après déploiement test: `agents/azure-compliance-checker/README.md:1`.

Sources:
- [Microsoft Bicep — docs officielles](https://learn.microsoft.com/azure/azure-resource-manager/bicep/overview)
- [Microsoft Azure Verified Modules (AVM)](https://aka.ms/AVM)
- [GitHub Bicep Registry Modules (index)](https://aka.ms/BRM)
- [Microsoft Deploy Bicep files — az CLI](https://learn.microsoft.com/azure/azure-resource-manager/bicep/deploy-cli)
- [Azure Policy — Overview](https://learn.microsoft.com/azure/governance/policy/overview)
- [Azure Policy — Effects (deny)](https://learn.microsoft.com/azure/governance/policy/concepts/effects)
