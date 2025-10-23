# Jour 5 — Conformité, licences et coûts (FSI)

Objectifs du jour:
- Lancer une première vérification de conformité (agent compliance) et comprendre l'évidence attendue.
- Clarifier les besoins de licences/abonnements pour les briques FSI.
- Estimer un ordre de grandeur des coûts (méthode et hypothèses), sans chiffrage non vérifié.

Parcours (90–120 min):
- Agent de conformité: `agents/azure-compliance-checker/README.md`
  - Lancer l'agent et charger la checklist FSI FR → « Validate all controls » → générer un rapport.
  - Identifier 2–3 écarts et noter les remédiations proposées.
- Licences/Plans/SKU — repères (sans inventer):
  - Entra PIM: nécessite Microsoft Entra ID P2 (voir sources).
  - Defender for Cloud: plans par ressource (évaluer l'opportunité/portée, pas de prix ici).
  - DDoS Protection Standard: service managé (activer au hub si exigence résilience).
  - Azure Firewall/Bastion: services managés; ne pas publier de chiffres, utilisez le Pricing Calculator.
- Coûts — méthode:
  - Listez hypothèses (région, env, volumétrie, ring0 minimal, 1 vnet spoke ring2, journaux 30/90/365j…).
  - Ouvrez le Pricing Calculator et créez un « estimate » avec les composants du ring choisi.
  - Exportez/attachez la capture et conservez l'URL de l'estimation.

Mini-lab (45–60 min):
1) Faites tourner l'agent de conformité et exportez un rapport Markdown.
2) Alignez 3 remédiations infra via l'agent FSI (ex: activer diagnostics, restreindre public access, forcer TLS).
3) Réalisez une estimation Pricing Calculator pour Ring 0 minimal (hypothèses EU), joignez l'URL.

Important — exactitude:
- Si vous n'êtes pas certain d'un prix/licence, écrivez « Je ne sais pas » et citez la source officielle pour vérification interne.

Sources:
- [Microsoft Microsoft Entra ID PIM — Licences](https://learn.microsoft.com/entra/id-governance/licensing-fundamentals#valid-licenses-for-pim)
- [Microsoft Microsoft Defender for Cloud overview](https://learn.microsoft.com/azure/defender-for-cloud/defender-for-cloud-introduction)
- [Microsoft Azure DDoS Protection pricing/overview](https://learn.microsoft.com/azure/ddos-protection/ddos-protection-overview)
- [Microsoft Azure Firewall docs](https://learn.microsoft.com/azure/firewall/overview)
- [Microsoft Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
- [Microsoft Microsoft Cloud Security Benchmark](https://learn.microsoft.com/security/benchmark/azure/overview)
- [Microsoft FSI Landing Zone (industrie)](https://learn.microsoft.com/industry/financial-services/fsi-lz)
