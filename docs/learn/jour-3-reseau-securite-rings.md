# Jour 3 — Réseau, sécurité et Ring-Based Architecture

Objectifs du jour:
- Comprendre hub/spoke, DNS privé, bastion, firewall, NSG, DDoS Protection.
- Maîtriser la logique des rings (0 fondation, 1 plateforme, 2 workloads) et des depths (minimal/standard/advanced).
- Préparer un plan réseau minimal viable pour FSI.

Lecture repo (60–90 min):
- Ring-Based Architecture: `docs/azure-fsi/architecture/rings.md`
- Guides Azure FSI (workflow/quickstarts):
  - `docs/azure-fsi/guides/workflow.md`
  - `docs/azure-fsi/guides/quickstart-mono.md`
  - `docs/azure-fsi/guides/quickstart-squad.md`

Rappels essentiels:
- Ring 0 (fondation) regroupe sécurité/gouvernance/monitoring/réseau de base (hub VNet, firewall, DNS, DDoS, KV, Log Analytics, Policies…).
- Ring 1 (plateforme) ajoute CI/CD, ACR, artefacts, shared KV, sous-réseaux agents.
- Ring 2 (workloads) porte VNets applicatifs, compute, data, intégration.
- Depths: `minimal` (POC/quickstart), `standard` (par défaut prod FSI), `advanced` (exigences avancées).

Mini-lab (45–60 min):
1) Choisissez votre stratégie: `ring0` seul (baseline) OU `ring0 + ring2` (chemin minimal vers app), depth=`minimal`.
2) Dessinez le schéma (hub + spoke app) avec flux entrants/sortants, DNS privés, endpoints privés, journaux.
3) Listez 3 contrôles sécurité prioritaires (ex: deny public access KV/Storage, TLS >= 1.2, diagnostics vers LA Workspace).

Mise en pratique avec l'agent (optionnel):
- Mode solo: `cd agents/azure-fsi-landingzone && python agent.py` → Prompt: « Génère un modèle Bicep de hub VNet + Azure Firewall pour le Ring 0 (minimal). »
- Mode squad: `python agent.py --squad` → Prompt: « Passe en revue mon schéma ring0+ring2 minimal (sécurité/réseau/DevOps) et propose un plan d'action priorisé. »

Sources:
- [Microsoft Azure hub-spoke network topology](https://learn.microsoft.com/azure/architecture/reference-architectures/hybrid-networking/hub-spoke)
- [Microsoft Azure Firewall overview](https://learn.microsoft.com/azure/firewall/overview)
- [Microsoft DDoS Protection Standard](https://learn.microsoft.com/azure/ddos-protection/ddos-protection-overview)
- [Microsoft Private DNS zones](https://learn.microsoft.com/azure/dns/private-dns-privatednszone)
- [Microsoft Azure Monitor/diagnostic settings](https://learn.microsoft.com/azure/azure-monitor/essentials/diagnostic-settings)
