# Solo Mode vs Squad Mode: Comparison Guide

## Overview

This document compares the **solo mode** (default) with the **squad mode** (`--squad` flag) for the Azure FSI Landing Zone agent.

---

## 🎯 Which One Should You Use?

### Use **Solo Mode** (default: `python agent.py`) when:
- ✅ You need to **quickly generate templates**
- ✅ Your task is **simple and focused** (e.g., "generate a hub-vnet template")
- ✅ You prefer **simplicity** over depth
- ✅ You want **lower cost** (single agent invocation)
- ✅ You're **getting started** with FSI Landing Zones

### Use **Squad Mode** (`python agent.py --squad`) when:
- ✅ You need **comprehensive security/compliance review**
- ✅ You want **expert analysis** in multiple domains (DevOps, Security, Network, Architecture)
- ✅ You need to **detect drift** between local templates and deployed infrastructure
- ✅ You're preparing for **production deployment or audit**
- ✅ You want **parallel analysis** for faster results on complex tasks
- ✅ You need **cross-domain insights** (e.g., security + network + DevOps)

---

## 📊 Feature Comparison

| Feature | Solo Mode | Squad Mode |
|---------|-----------|------------|
| **Simplicity** | ⭐⭐⭐⭐⭐ Simple | ⭐⭐⭐ Moderate |
| **Setup** | 1 agent | 1 orchestrator + 4 sub-agents |
| **Expertise Depth** | ⭐⭐⭐ Generalist | ⭐⭐⭐⭐⭐ Deep specialists |
| **Template Generation** | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐⭐ Same speed |
| **Security Analysis** | ⭐⭐⭐ Basic | ⭐⭐⭐⭐⭐ Expert-level |
| **Compliance Review** | ⭐⭐⭐ Generic | ⭐⭐⭐⭐⭐ Regulation-specific |
| **Drift Detection** | ⭐⭐⭐ Manual | ⭐⭐⭐⭐⭐ Automated |
| **Parallelization** | ❌ Sequential | ✅ Parallel analysis |
| **Cost** | ⭐⭐⭐⭐ Lower | ⭐⭐⭐ Higher (multiple invocations) |
| **Maintenance** | ⭐⭐⭐⭐⭐ Single codebase | ⭐⭐⭐⭐ 5 agents in one |
| **Extensibility** | ⭐⭐⭐ Add tools | ⭐⭐⭐⭐⭐ Add new sub-agents |

---

## 🔄 Example Use Cases

### Example 1: Generate a Hub VNet Template

**Solo Mode:**
```
User: "Generate a hub-vnet template for Ring 0"
Agent: [Generates Bicep template]
Time: ~30 seconds
Quality: ⭐⭐⭐⭐⭐ Perfect for this task
```

**Squad Mode:**
```
User: "Generate a hub-vnet template for Ring 0"
Orchestrator: [Generates Bicep template] (same as solo mode)
Time: ~30 seconds
Quality: ⭐⭐⭐⭐⭐ Same result
```

**Winner:** **Tie** - Both equally good for simple generation tasks

---

### Example 2: Review Security Configuration

**Solo Mode:**
```
User: "Review my Ring 0 security configuration"
Agent:
  - Reads Key Vault template
  - Generic security checks
  - Basic recommendations

Result:
  ✅ Key Vault: Purge protection enabled
  ✅ Private endpoints configured
  ⚠️  Consider adding diagnostic settings

Time: ~2 minutes
Quality: ⭐⭐⭐ Correct but basic
```

**Squad Mode:**
```
User: "Review my Ring 0 security configuration"
Orchestrator → Security Specialist:
  - Reads all security templates (Key Vault, NSG, Policies)
  - Cross-references with GDPR/DORA/PSD2 requirements
  - Checks both local templates AND deployed state (Azure CLI)
  - Compares against FSI security baseline

Result:
  ✅ Key Vault: Purge protection ✓, soft-delete ✓, RBAC ✓
  ❌ CRITICAL: Diagnostic settings missing (GDPR requirement!)
  ❌ CRITICAL: Private DNS zone not configured
  ⚠️  NSG rule allows port 22 from 0.0.0.0/0 (security risk)
  ⚠️  CMK not configured (PSD2 recommends customer-managed keys)
  ⚠️  Firewall missing deny rule for public access

  📊 Compliance Score: 65/100
  🏛️  GDPR: Non-compliant (diagnostic settings required)
  🏛️  DORA: Partial compliance
  🏛️  PSD2: Needs improvement (CMK recommended)

Time: ~2 minutes
Quality: ⭐⭐⭐⭐⭐ Comprehensive, regulation-specific
```

**Winner:** **Squad Mode** 🏆 - Much deeper analysis

---

### Example 3: Full Deployment Review (Ring 0 + 1 + 2)

**Solo Mode:**
```
User: "Review my entire FSI Landing Zone deployment"
Agent:
  - Sequentially reads all templates
  - Generic analysis of each component
  - Provides overall assessment

Time: ~5-7 minutes (sequential)
Quality: ⭐⭐⭐ Correct but may miss cross-domain issues
```

**Squad Mode:**
```
User: "Review my entire FSI Landing Zone deployment"
Orchestrator:
  ├─ Security Specialist  → Reviews Ring 0 (security, policies, Key Vault)
  ├─ Network Specialist   → Reviews Ring 0 + 2 (network topology, firewall)
  ├─ DevOps Specialist    → Reviews Ring 1 (CI/CD, deployment scripts)
  └─ All run in PARALLEL ⚡

Architect Specialist:
  - Receives all 3 specialist reports
  - Synthesizes findings
  - Identifies cross-domain issues
  - Prioritizes remediation

Result:
  📊 Overall Architecture Score: 7.5/10

  🔴 CRITICAL Issues (3):
    1. NSG port 22 exposed to internet (Security + Network)
    2. No rollback mechanism in deploy.sh (DevOps)
    3. Key Vault diagnostics missing (Security → GDPR compliance)

  🟡 MEDIUM Issues (5):
    4. Pipeline missing approval gates for PROD (DevOps)
    5. Firewall only has 2 rules (Network)
    6. No drift detection configured (DevOps)
    7. Storage account using Microsoft-managed keys (Security)
    8. No VPN Gateway configured (Network)

  ℹ️  INFO (4):
    9. Consider blue-green deployment (DevOps)
    10. Add cost monitoring (Architect)
    11. Plan for multi-region (Architect)
    12. Document architecture decisions (Architect)

  💡 Recommendations (Prioritized):
    Priority 1: Fix NSG rule immediately (security risk)
    Priority 2: Enable Key Vault diagnostics (compliance blocker)
    Priority 3: Add rollback to deploy.sh (operational resilience)

Time: ~3-4 minutes (parallel analysis)
Quality: ⭐⭐⭐⭐⭐ Comprehensive, cross-domain, prioritized
```

**Winner:** **Squad Mode** 🏆 - Faster + deeper + cross-domain insights

---

### Example 4: Drift Detection (Local Templates vs Deployed)

**Solo Mode:**
```
User: "Check if my deployed infrastructure matches the templates"
Agent:
  - Manually reads template
  - Runs 'az' commands
  - Compares manually
  - May miss some resources

Time: ~5 minutes (manual, sequential)
Risk: ⚠️  May miss resources
Quality: ⭐⭐⭐ Functional but manual
```

**Squad Mode:**
```
User: "Check drift between templates and deployed infrastructure"
Orchestrator:
  ├─ Security Specialist  → Compares: Key Vault, NSG, Policies
  ├─ Network Specialist   → Compares: VNet, Firewall, Peerings
  └─ DevOps Specialist    → Compares: Storage, Container Registry

Architect Specialist → Synthesizes:

  📊 Drift Detection Report:

  Ring 0 (Foundation):
    ✅ Hub VNet: No drift
    ❌ NSG: 2 rules added manually (NOT in template!)
         Manual rule 1: Allow 10.0.0.0/8 → port 443
         Manual rule 2: Allow AzureLoadBalancer → *
    ⚠️  Key Vault: Diagnostic settings added manually
    ⚠️  Azure Firewall: 1 additional rule (NOT in template)

  Ring 1 (Platform):
    ✅ Container Registry: Synced
    ❌ Storage Account: SKU changed
         Template: Standard_LRS
         Deployed: Standard_GRS (more expensive!)
    ⚠️  Shared Key Vault: Access policies modified manually

  Ring 2 (Workload):
    ✅ Spoke VNet: Synced
    ❌ App Service: Scaled up manually
         Template: B1
         Deployed: S1

  💡 Recommendations:
    1. Update templates to match manual changes OR
    2. Revert manual changes to match templates
    3. Implement change control process to prevent drift
    4. Schedule weekly drift detection scans

Time: ~3 minutes (parallel checks)
Quality: ⭐⭐⭐⭐⭐ Exhaustive, automated
```

**Winner:** **Squad Mode** 🏆 - Comprehensive drift detection across all domains

---

## 💰 Cost Comparison

### Solo Mode
- **Per query**: 1 agent invocation
- **Simple task**: ~$0.001 - $0.01
- **Complex task**: ~$0.05 - $0.10

### Squad Mode
- **Per query**: 1 orchestrator + N sub-agents (typically 3-4)
- **Simple task**: ~$0.001 - $0.01 (same as solo, delegates to 0 sub-agents)
- **Complex task**: ~$0.15 - $0.30 (3-4 sub-agent invocations + orchestrator + architect)

**Cost difference**: Squad mode is **2-3x more expensive** for complex tasks, but provides **5-10x more value** through deeper analysis.

---

## 🎓 Recommendation Strategy

### Getting Started → Use Solo Mode
When learning FSI Landing Zones:
```bash
cd agents/azure-fsi-landingzone
python agent.py
```

### Pre-Production Review → Use Squad Mode
Before deploying to UAT/PROD:
```bash
cd agents/azure-fsi-landingzone
python agent.py --squad
```

### Hybrid Approach (Best of Both)
1. **Generation phase**: Use solo mode for rapid template generation
2. **Review phase**: Use squad mode for comprehensive review
3. **Deployment**: Use solo mode for quick deployments
4. **Audit**: Use squad mode for compliance validation

---

## 📈 Performance Benchmarks

| Task | Solo Mode | Squad Mode | Winner |
|------|-----------|------------|--------|
| Generate 1 template | 30s | 30s | Tie |
| Generate 5 templates | 2 min | 2 min | Tie |
| Review security (Ring 0) | 2 min | 2 min | **Squad** (depth) |
| Review full deployment | 5-7 min | 3-4 min | **Squad** (parallel) |
| Drift detection | 5 min | 3 min | **Squad** (automated) |
| Simple Q&A | 10s | 10s | Tie |

---

## 🚀 Migration Path

Already using solo mode? Here's how to adopt squad mode:

1. **Keep using solo mode** for daily template generation
2. **Try squad mode** (`--squad` flag) for your next security review
3. **Compare results** side-by-side
4. **Adopt squad mode** for pre-production and audit workflows
5. **Stick with solo mode** for quick, simple tasks

You don't have to choose one or the other - use both modes as needed!

---

## 🎯 Decision Matrix

| Your Scenario | Recommended Mode |
|---------------|-------------------|
| "I need a quick VNet template" | **Solo Mode** |
| "Generate all Ring 0 templates" | **Solo Mode** |
| "Is my deployment secure?" | **Squad Mode** |
| "Am I GDPR compliant?" | **Squad Mode** |
| "Review before PROD deployment" | **Squad Mode** |
| "Check drift from templates" | **Squad Mode** |
| "Audit for compliance" | **Squad Mode** |
| "Quick export of deployment plan" | **Solo Mode** |
| "Comprehensive architecture review" | **Squad Mode** |

---

## 📚 See Also

- [Azure FSI Landing Zone Agent README](../../agents/azure-fsi-landingzone/README.md)
- [Multi-Agent Architecture](../architecture/multi-agent.md)
- [Ring Architecture](../architecture/rings.md)

---

**TL;DR**: Use **solo mode** for speed and simplicity. Use **squad mode** for depth and compliance. Or use both modes! 🎉
