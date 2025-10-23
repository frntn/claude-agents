# Ring-Based Deployment Architecture

## Overview

The FSI Landing Zone agent now supports a **ring-based deployment strategy**, allowing you to deploy your Azure infrastructure progressively in well-defined layers. This approach provides:

- **Structured deployment**: Clear separation of concerns across infrastructure layers
- **Flexible scope**: Deploy only what you need (minimal, standard, or advanced)
- **Progressive rollout**: Deploy rings sequentially based on dependencies
- **Risk mitigation**: Test and validate each layer before moving to the next

## Ring Architecture

### Ring 0: Foundation (Core FSI Compliance)

**Mandatory**: ✅ Yes
**Deployment Order**: 1
**Purpose**: Establish the compliance and security foundation

This ring contains all mandatory components for FSI compliance and forms the bedrock of your landing zone.

#### Components:

**Network Core**
- ✓ Hub VNet (MANDATORY)
- ✓ Azure Firewall (MANDATORY)
- ○ VPN Gateway (Optional in minimal)
- ✓ DDoS Protection (MANDATORY)
- ✓ Private DNS Zones (MANDATORY)

**Security Core**
- ✓ Key Vault Core (MANDATORY)
- ✓ Azure Bastion (MANDATORY)
- ✓ Network Security Groups (MANDATORY)

**Governance Core**
- ✓ Management Groups (MANDATORY)
- ✓ Azure Policies - GDPR, DORA, EBA GL, Data Residency (MANDATORY)

**Monitoring Core**
- ✓ Log Analytics Workspace (MANDATORY)
- ✓ Microsoft Defender for Cloud (MANDATORY)
- ✓ Diagnostic Settings (MANDATORY)

**Identity Core**
- ✓ Entra ID Baseline (MANDATORY)
- ✓ Privileged Identity Management (MANDATORY)
- ✓ Conditional Access Policies (MANDATORY)

---

### Ring 1: Platform Services (DevOps & Shared Infrastructure)

**Mandatory**: ⚠️ Optional
**Deployment Order**: 2
**Depends On**: Ring 0 Foundation
**Purpose**: DevOps tooling, CI/CD infrastructure, and shared services

This ring provides the platform services needed to support application development and deployment.

#### Components:

**DevOps Infrastructure**
- ✓ Container Registry (MANDATORY when deploying Ring 1)
- ○ DevOps Project (Azure DevOps or GitHub)
- ✓ Artifact Storage (MANDATORY when deploying Ring 1)

**CI/CD Infrastructure**
- ✓ Build Agents Subnet (MANDATORY when deploying Ring 1)
- ○ Self-hosted Agents
- ○ Deployment Pipelines (Templates only)

**Shared Services**
- ✓ Shared Key Vault (MANDATORY when deploying Ring 1)
- ✓ Shared Storage Account (MANDATORY when deploying Ring 1)
- ○ API Management (Advanced only)

**Admin Infrastructure**
- ○ Admin VNet
- ○ Jump Boxes
- ○ Privileged Workstations (Advanced only)

---

### Ring 2: Workload Infrastructure (Application Layer)

**Mandatory**: ⚠️ Optional
**Deployment Order**: 3
**Depends On**: Ring 0 Foundation (can be deployed without Ring 1)
**Purpose**: Infrastructure for hosting applications (IaaS/PaaS/CaaS)

This ring contains the compute, data, and integration services for your applications.

#### Components:

**Compute Services**
- ✓ Spoke VNet App (MANDATORY when deploying Ring 2)
- ○ App Service Plan
- ○ AKS Cluster
- ○ Virtual Machines
- ○ Azure Functions

**Data Services**
- ○ SQL Database
- ○ Cosmos DB
- ✓ Storage Accounts (MANDATORY when deploying Ring 2)
- ○ Data Lake

**Integration Services**
- ○ Service Bus
- ○ Event Grid
- ○ Logic Apps
- ○ API Connections

**Frontend Services**
- ○ Application Gateway
- ○ Front Door
- ○ CDN

---

## Deployment Depth Profiles

Each ring can be deployed at different depth levels:

### 🎚️ Minimal
**Description**: Essential components only - quickstart deployment
**Filter**: Mandatory components only
**Use Case**: POC, testing, minimal viable landing zone

### 🎚️ Standard (Default)
**Description**: Recommended components for production FSI workloads
**Filter**: Mandatory + recommended components
**Use Case**: Production deployments, standard FSI requirements

### 🎚️ Advanced
**Description**: All components including advanced features
**Filter**: All components
**Use Case**: Complex workloads, advanced security requirements

---

## Usage Workflow

### 1. Set Project Name
```
set_project_name(project_name="my-fsi-project")
```

### 2. List Available Rings
```
list_deployment_rings()
```

### 3. Select Rings to Deploy
```
# Deploy all rings
select_deployment_rings(rings="all")

# Or deploy specific rings
select_deployment_rings(rings="ring0_foundation,ring2_workload")
```

### 4. Set Deployment Depth (Optional)
```
set_ring_depth(depth="standard")  # minimal, standard, or advanced
```

### 5. Generate Ring Deployment
```
generate_ring_deployment()
```

This will create:
- `{project-name}/ring0_foundation/` - Ring 0 templates and DEPLOYMENT.md
- `{project-name}/ring1_platform/` - Ring 1 templates and DEPLOYMENT.md (if selected)
- `{project-name}/ring2_workload/` - Ring 2 templates and DEPLOYMENT.md (if selected)
- `{project-name}/deploy.sh` - Main deployment script

---

## File Structure

After generating a ring-based deployment, your project structure will look like:

```
my-fsi-project/
├── deploy.sh                          # Main deployment script
├── ring0_foundation/
│   ├── DEPLOYMENT.md                   # Ring 0 deployment guide
│   ├── hub-vnet.bicep
│   ├── azure-firewall.bicep
│   ├── key-vault-core.bicep
│   ├── log-analytics-workspace.bicep
│   ├── azure-policies.bicep
│   └── ...
├── ring1_platform/                     # Optional
│   ├── DEPLOYMENT.md
│   ├── container-registry.bicep
│   ├── shared-key-vault.bicep
│   └── ...
└── ring2_workload/                     # Optional
    ├── DEPLOYMENT.md
    ├── spoke-vnet-app.bicep
    ├── storage-accounts.bicep
    └── ...
```

---

## Deployment Strategy

### Recommended Approach

1. **Phase 1 - Foundation (Week 1-2)**
   - Deploy Ring 0 with `depth=minimal` first
   - Validate compliance policies
   - Test network connectivity
   - Configure Entra ID and PIM

2. **Phase 2 - Platform (Week 3-4)**
   - Deploy Ring 1 for DevOps/CI/CD
   - Set up build agents
   - Configure deployment pipelines
   - Test end-to-end CI/CD

3. **Phase 3 - Workloads (Week 5+)**
   - Deploy Ring 2 incrementally
   - Start with spoke VNet and storage
   - Add compute services as needed
   - Deploy applications

### Alternative: Minimal Path to Production

For rapid deployment, you can deploy Ring 0 + Ring 2 only:

```
select_deployment_rings(rings="ring0_foundation,ring2_workload")
set_ring_depth(depth="minimal")
generate_ring_deployment()
```

This gives you the compliance foundation and basic application infrastructure without DevOps tooling.

---

## Dependencies

The ring system automatically checks dependencies:

- **Ring 1** requires **Ring 0**
- **Ring 2** requires **Ring 0** (can skip Ring 1)

When you select rings, the agent will warn you if dependencies are missing.

---

## Customization

You can customize the ring configuration in `config.yaml`:

---

## Naming Conventions

### Resource Group Names

- rg-<project>-hub-networking-<env> - Ring 0 hub VNet, firewall, bastion, DNS
- rg-<project>-security-<env> - Ring 0 security services (e.g., core Key Vault)
- rg-<project>-monitoring-<env> - Ring 0 monitoring (Log Analytics, diagnostics)
- rg-<project>-devops-<env> - Ring 1 platform tooling (ACR, shared KV for pipelines)
- rg-<project>-app-<env> - Ring 2 application workloads

Notes
- <project>: short identifier for the landing zone/project (e.g., "demo", "bankx")
- <env>: one of dev, test, staging, prod, sandbox
- This convention is referenced by RBAC quickstart and RBAC specification for role scopes.
- Works for single or multi-subscription setups; apply per target subscription.

- Add/remove components from each ring
- Change mandatory/optional flags
- Modify deployment depth filters
- Add custom rings (Ring 3, Ring 4, etc.)

---

## Alignment with Microsoft FSI Landing Zone

This ring architecture aligns with Microsoft's FSI Landing Zone methodology:

- **Ring 0** = Platform Foundation + Compliance
- **Ring 1** = DevOps & Shared Services
- **Ring 2** = Application Landing Zones (Corp, Online, Confidential)

Each ring can be configured with different Landing Zone types (Corp, Online, Confidential Corp, Confidential Online) based on your workload requirements.
