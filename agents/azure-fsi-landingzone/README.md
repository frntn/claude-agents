# Azure FSI Landing Zone Agent

An AI-powered deployment agent for Azure Financial Services Industry (FSI) Landing Zones.

## Overview

This agent helps deploy secure, compliant Azure infrastructure for financial services using Microsoft FSI Landing Zone templates, Azure Verified Modules (AVM), and European compliance policies.

**Two modes available:**
- **Solo Mode** (default): Fast template generation and simple deployments
- **Squad Mode** (`--squad`): Multi-agent collaboration with specialist expertise

## Quick Start

### Solo Mode (Default)
```bash
cd agents/azure-fsi-landingzone
python agent.py
```

Example prompts:
- "Generate Ring 0 foundation templates for FSI Landing Zone"
- "Create a hub VNet with Azure Firewall"
- "List available deployment rings"

### Squad Mode (Multi-Agent)
```bash
cd agents/azure-fsi-landingzone
python agent.py --squad
```

Example prompts:
- "Review my entire FSI Landing Zone deployment for production readiness"
- "Analyze security posture for Ring 0 foundation"
- "Detect drift between local templates and deployed Azure resources"
- "Generate comprehensive compliance report"

## Choosing the Right Mode

### ✅ Use **Solo Mode** when:
- You need quick template generation
- Your task is simple and focused
- You're getting started with FSI Landing Zones
- You prefer simplicity and lower cost

### ✅ Use **Squad Mode** when:
- You need comprehensive security/compliance review
- You want expert analysis across multiple domains
- You need drift detection between local templates and deployed infrastructure
- You're preparing for production deployment or audit
- You want parallel analysis for faster results on complex tasks
- You need cross-domain insights (security + network + DevOps + FinOps + PMO)

## Squad Mode Features

When running with `--squad`, you get access to specialist sub-agents:

- 🏗️ **Architect Agent** — Holistic design and architectural recommendations
- 🔒 **Security Agent** — Guardrails, IAM, and compliance evidence
- 🌐 **Network Agent** — Hybrid connectivity and segmentation design
- 🚀 **DevOps Agent** — CI/CD automation, pipelines, and IaC governance
- 💰 **FinOps Agent** — Cost management, tagging strategy, and budgeting
- 🧭 **Cloud PMO Agent** — Delivery governance, milestones, and stakeholder comms
- 🧪 **Validator Agent** — Local Bicep linting and template quality checks

### How Squad Mode Works

The orchestrator agent coordinates specialist agents to provide multi-dimensional analysis:

```
User Request
     ↓
Orchestrator
     ├→ Security Agent   (parallel analysis)
     ├→ Network Agent    (parallel analysis)
     ├→ DevOps Agent     (parallel analysis)
     ├→ FinOps Agent     (parallel analysis)
     ├→ Validator Agent  (parallel analysis)
     ├→ Cloud PMO Agent  (parallel analysis)
     └→ Architect Agent  (synthesizes all inputs)
     ↓
Consolidated Report
```

## Documentation

**All documentation has been centralized. See:**

📚 **[Complete Azure FSI Documentation](../../docs/azure-fsi/)**

### Quick Links
- **[Solo Mode Quick Start](../../docs/azure-fsi/guides/quickstart-mono.md)**
- **[Squad Mode Quick Start](../../docs/azure-fsi/guides/quickstart-squad.md)**
- **[Multi-Agent Architecture](../../docs/azure-fsi/architecture/multi-agent.md)**
- **[Ring Architecture](../../docs/azure-fsi/architecture/rings.md)**
- **[Deployment Workflow](../../docs/azure-fsi/guides/workflow.md)**
- **[Solo vs Squad Comparison](../../docs/azure-fsi/guides/comparison.md)**
- **[Changelog](../../docs/azure-fsi/changelog.md)**

## Configuration

Copy `.env.example` to `.env` and add your `ANTHROPIC_API_KEY`:

```bash
cp .env.example .env
# Edit .env and add your API key
```

## Requirements

- Python 3.10+
- Claude Agent SDK v0.1.0+
- Azure CLI (for deployment and drift detection)
- Anthropic API key

See the [main documentation](../../docs/azure-fsi/) for detailed requirements.

## Key Features

### Solo Mode
- ✅ Fast template generation using Bicep + Azure Verified Modules (AVM)
- ✅ Ring-based deployment strategy (Ring 0/1/2)
- ✅ European compliance (GDPR, DORA, PSD2, MiFID II, EBA GL)
- ✅ Simple, focused operation
- ✅ Lower cost (single agent invocation)

### Squad Mode Additional Features
- ✅ **Specialist Expertise**: Each agent brings deep domain knowledge
  - **DevOps**: Azure DevOps, GitHub Actions, deployment automation
  - **Security**: Azure Defender, Key Vault, compliance policies
  - **Network**: VNets, Firewall, NSGs, private endpoints
  - **Architect**: Design patterns, cost optimization, governance
- ✅ **Parallel Analysis**: Multiple agents work concurrently for faster results
- ✅ **Drift Detection**: Compare local Bicep templates with actual deployed Azure resources
- ✅ **Comprehensive Reports**: Consolidated analysis across all domains with actionable recommendations

---

**Part of the [Claude Agents Repository](../../README.md)**
