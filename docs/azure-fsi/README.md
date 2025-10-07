# Azure FSI Landing Zone Agents

AI-powered deployment agents for Azure Financial Services Industry (FSI) Landing Zones, built with Claude Agent SDK.

## Overview

These agents help financial institutions deploy compliant, secure Azure infrastructure using:

- **Microsoft FSI Landing Zone Templates**: Industry-specific reference architectures
- **Azure Verified Modules (AVM)**: Production-ready, Microsoft-validated infrastructure modules
- **European Compliance**: Built-in policies for GDPR, DORA, PSD2, MiFID II, and EBA Guidelines

## 📌 Technology Stack Decision (October 2025)

### Why Bicep + AVM (Not Terraform ALZ)?

These agents use **Bicep with Azure Verified Modules (AVM)** as the primary Infrastructure as Code approach:

#### ✅ **Official Microsoft Recommendation**
- Microsoft's **FSI Landing Zone** is built with **Bicep + AVM**
- **Bicep AVM for Platform Landing Zone (ALZ)** is Microsoft's strategic direction (GA expected August 2025)
- Official Microsoft compliance documentation assumes Bicep deployments

#### ✅ **Simplicity**
- **Azure-native**: No external tooling beyond Azure CLI + Bicep
- **Simpler syntax**: More readable than Terraform/HCL
- **Fewer dependencies**: No Terraform state management complexity
- **Faster learning curve**: Especially for Azure-focused teams

#### ✅ **Trust & Support**
- **Direct Microsoft support**: First-class support from Azure product teams
- **Aligned with Microsoft roadmap**: Future-proof investment
- **Validated modules**: AVM modules are tested and maintained by Microsoft

## 🎯 Choosing the Right Mode

The Azure FSI Landing Zone agent supports two operational modes:

### Solo Mode (Default)
**Best for:**
- ✅ Quick template generation
- ✅ Simple and focused tasks (e.g., "generate a hub-vnet template")
- ✅ Getting started with FSI Landing Zones
- ✅ Lower cost (single agent invocation)
- ✅ Simplicity over depth

**Usage**: `python agent.py` (default mode)

### Squad Mode (`--squad` flag)
**Best for:**
- ✅ Comprehensive security/compliance review
- ✅ Expert analysis in multiple domains (DevOps, Security, Network, Architecture)
- ✅ Drift detection between local templates and deployed infrastructure
- ✅ Production deployment or audit preparation
- ✅ Parallel analysis for faster results on complex tasks
- ✅ Cross-domain insights (e.g., security + network + DevOps)

**Usage**: `python agent.py --squad`

**Agent location**: [`/agents/azure-fsi-landingzone/`](../../agents/azure-fsi-landingzone/)

**See the [detailed comparison guide](guides/comparison.md) to help you choose.**

## 📚 Documentation

### Getting Started
- **[Quick Start - Solo Mode](guides/quickstart-mono.md)**: Get started with solo mode in 10 minutes
- **[Quick Start - Squad Mode](guides/quickstart-squad.md)**: Get started with squad mode
- **[Complete Deployment Workflow](guides/workflow.md)**: Step-by-step production deployment guide

### Architecture Documentation
- **[Ring-Based Architecture](architecture/rings.md)**: Progressive deployment strategy (Ring 0, 1, 2)
- **[Multi-Agent Architecture](architecture/multi-agent.md)**: How the specialist squad works
- **[Milestones Mapping](architecture/milestones.md)**: How rings map to deployment milestones

### Reference
- **[Comparison Guide](guides/comparison.md)**: Detailed comparison of solo mode vs squad mode
- **[Microsoft Alignment Analysis](guides/alignment.md)**: How this agent aligns with Microsoft FSI LZ
- **[Changelog](changelog.md)**: Version history and changes

## 🚀 Quick Examples

### Example 1: Generate a Hub VNet Template

**Solo Mode:**
```bash
cd agents/azure-fsi-landingzone
python agent.py
> "Generate a hub VNet template with Azure Firewall for Ring 0"
```

**Squad Mode:**
```bash
cd agents/azure-fsi-landingzone
python agent.py --squad
> "Generate and review a hub VNet template with security analysis"
```

### Example 2: Full Deployment Review

**Squad Mode (Recommended):**
```bash
cd agents/azure-fsi-landingzone
python agent.py --squad
> "Review my entire FSI Landing Zone deployment for production readiness"
```
The squad will:
1. Security Agent → Analyzes security posture
2. Network Agent → Reviews network configuration
3. DevOps Agent → Checks CI/CD setup
4. Architect Agent → Provides holistic recommendations

## 🔑 Key Features

### Common Features (Both Modes)
- ✅ **Ring-Based Deployment**: Progressive rollout (Foundation → Platform → Workload)
- ✅ **Compliance-Ready**: GDPR, DORA, PSD2, MiFID II, EBA GL policies
- ✅ **Azure Verified Modules**: Production-ready Microsoft templates
- ✅ **European Data Residency**: Default `francecentral` region
- ✅ **Template Generation**: Bicep templates for all components

### Squad Mode Additional Features
- ✅ **Specialist Expertise**: 4 specialized sub-agents (DevOps, Security, Network, Architect)
- ✅ **Drift Detection**: Compare local templates with deployed Azure resources
- ✅ **Parallel Analysis**: Faster results through concurrent agent execution
- ✅ **Cross-Domain Insights**: Security + Network + DevOps perspectives
- ✅ **Production Readiness**: Comprehensive compliance and security reviews

## 📖 Additional Resources

### External Documentation
- [Microsoft FSI Landing Zone](https://learn.microsoft.com/en-us/industry/financial-services/fsi-lz)
- [Azure Verified Modules](https://aka.ms/AVM)
- [Azure Compliance Documentation](https://docs.microsoft.com/azure/compliance/)

### Repository Resources
- [Agent Development Guide](../agents/creating-agents.md)
- [Repository Getting Started](../getting-started.md)

---

*For detailed implementation guides, see the [guides directory](guides/).*
