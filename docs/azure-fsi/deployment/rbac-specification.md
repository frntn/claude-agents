# Azure FSI Landing Zone - RBAC Specification & Manual Prerequisites

**Version:** 1.0
**Last Updated:** 2025-10-22
**Target Audience:** Enterprise IT Security Teams, Cloud Architects, Compliance Officers

---

## Executive Summary

This document specifies all manual prerequisites and Role-Based Access Control (RBAC) requirements for deploying the Azure FSI Landing Zone using automated deployment agents. It provides two RBAC configuration approaches:

1. **Option A: Minimal Built-in Roles** - Using Azure's native roles for faster deployment
2. **Option B: Strict Custom Roles** - Granular permissions with atomic actions for maximum security

All prerequisites must be completed manually by the client's Entra ID and Azure administrators **before** initiating automated deployment.

---

## Table of Contents

1. [Manual Prerequisites](#1-manual-prerequisites)
2. [Entra ID Groups & Membership](#2-entra-id-groups--membership)
3. [Service Principal Configuration](#3-service-principal-configuration)
4. [RBAC Option A: Minimal Built-in Roles](#4-rbac-option-a-minimal-built-in-roles)
5. [RBAC Option B: Strict Custom Roles](#5-rbac-option-b-strict-custom-roles)
6. [Validation Checklist](#6-validation-checklist)
7. [Deployment Phase Roles](#7-deployment-phase-roles)
8. [Security Considerations](#8-security-considerations)

---

## 1. Manual Prerequisites

### 1.1 Entra ID (Azure AD) Configuration

These tasks must be performed manually by Global Administrators:

#### 1.1.1 Multi-Factor Authentication (MFA)
```
Task: Enable MFA for all users
Scope: All users except break-glass accounts
Authentication Methods: Microsoft Authenticator app (preferred), SMS (fallback)
Status: [ ] Completed
Owner: Entra ID Administrator
```

#### 1.1.2 Privileged Identity Management (PIM)
```
Task: Enable Azure AD Premium P2 license
Reason: Required for PIM functionality
Cost: Varies by user count
Status: [ ] Completed

Task: Configure PIM settings
- Maximum activation duration: 8 hours
- Require approval: Yes (for Owner, User Access Administrator)
- Require MFA on activation: Yes
- Require justification: Yes
Status: [ ] Completed
Owner: Global Administrator
```

#### 1.1.3 Conditional Access Policies
Create the following 5 baseline policies:

**Policy 1: Require MFA for All Users**
```json
{
  "displayName": "CA001-Require-MFA-All-Users",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeUsers": ["All"],
      "excludeUsers": ["break-glass-01", "break-glass-02"]
    },
    "applications": {
      "includeApplications": ["All"]
    }
  },
  "grantControls": {
    "operator": "OR",
    "builtInControls": ["mfa"]
  }
}
```
Status: [ ] Completed

**Policy 2: Block Legacy Authentication**
```json
{
  "displayName": "CA002-Block-Legacy-Auth",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeUsers": ["All"]
    },
    "clientAppTypes": ["exchangeActiveSync", "other"]
  },
  "grantControls": {
    "operator": "OR",
    "builtInControls": ["block"]
  }
}
```
Status: [ ] Completed

**Policy 3: Geo-Blocking (EU Only for FSI Compliance)**
```json
{
  "displayName": "CA003-Geo-Blocking-Non-EU",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeUsers": ["All"],
      "excludeUsers": ["break-glass-01", "break-glass-02"]
    },
    "locations": {
      "includeLocations": ["All"],
      "excludeLocations": [
        "FR", "DE", "NL", "IE", "BE", "LU", "AT",
        "IT", "ES", "PT", "SE", "DK", "FI", "NO"
      ]
    }
  },
  "grantControls": {
    "operator": "OR",
    "builtInControls": ["block"]
  }
}
```
Status: [ ] Completed

**Policy 4: Require Compliant Device**
```json
{
  "displayName": "CA004-Require-Compliant-Device",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeUsers": ["All"],
      "excludeUsers": ["break-glass-01", "break-glass-02"]
    },
    "applications": {
      "includeApplications": ["All"]
    }
  },
  "grantControls": {
    "operator": "OR",
    "builtInControls": ["compliantDevice", "domainJoinedDevice"]
  }
}
```
Status: [ ] Completed

**Policy 5: Block High-Risk Sign-ins**
```json
{
  "displayName": "CA005-Block-High-Risk-Signin",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeUsers": ["All"]
    },
    "signInRiskLevels": ["high"]
  },
  "grantControls": {
    "operator": "OR",
    "builtInControls": ["block"]
  }
}
```
Status: [ ] Completed

#### 1.1.4 Break-Glass Accounts
Create emergency access accounts:

```
Account 1:
- UPN: break-glass-01@<tenant>.onmicrosoft.com
- Role: Global Administrator (permanent assignment)
- MFA: DISABLED (emergency access requirement)
- Password: 24+ character complex password
- Storage: Physical secure vault + Azure Key Vault backup
- Review Schedule: Quarterly
Status: [ ] Completed

Account 2:
- UPN: break-glass-02@<tenant>.onmicrosoft.com
- Role: Global Administrator (permanent assignment)
- MFA: DISABLED (emergency access requirement)
- Password: Different 24+ character complex password
- Storage: Different physical location from Account 1
- Review Schedule: Quarterly
Status: [ ] Completed

Alert Configuration:
- Monitor sign-in activity for break-glass accounts
- Send alerts to: security-team@<domain>
- Alert channels: Email, SMS, Microsoft Teams
Status: [ ] Completed
```

#### 1.1.5 Guest User Restrictions
```
Task: Configure external collaboration settings
Path: Entra ID → External Identities → External collaboration settings

Settings:
- Guest user access: Most restrictive
- Guest invite settings: Only admins and users assigned to specific roles can invite
- Collaboration restrictions: Allow invitations only to specified domains (if applicable)
- Guest user access review: Every 30 days
Status: [ ] Completed
```

---

## 2. Entra ID Groups & Membership

Create the following security groups manually. These groups will receive RBAC role assignments at the Azure subscription/resource group level.

### 2.1 Required Security Groups

#### Group 1: Cloud Platform Team
```
Display Name: AZ-FSI-CloudPlatform-Team
Description: Cloud architects and platform engineers managing landing zone infrastructure
Group Type: Security
Membership Type: Assigned (not dynamic)
Owners: IT Director, Cloud Lead
Members:
  - <cloud-architect-01@domain>
  - <cloud-architect-02@domain>
  - <platform-engineer-01@domain>
  - <platform-engineer-02@domain>

Azure RBAC Assignments (see Section 4 & 5):
  - Owner on hub resource groups
  - Contributor on all FSI resource groups
  - PIM-eligible for temporary privileged access

Status: [ ] Created  [ ] Members Added  [ ] RBAC Configured
```

#### Group 2: Security & Compliance Team
```
Display Name: AZ-FSI-Security-Team
Description: Security officers and compliance managers overseeing FSI controls
Group Type: Security
Membership Type: Assigned
Owners: CISO, Compliance Manager
Members:
  - <security-officer-01@domain>
  - <security-officer-02@domain>
  - <compliance-manager-01@domain>

Azure RBAC Assignments:
  - Reader on all resources
  - Security Admin on subscription
  - Policy Contributor for compliance policies
  - Microsoft Defender for Cloud access

Status: [ ] Created  [ ] Members Added  [ ] RBAC Configured
```

#### Group 3: Network Operations Team
```
Display Name: AZ-FSI-Network-Team
Description: Network engineers managing virtual networks, firewall, and connectivity
Group Type: Security
Membership Type: Assigned
Owners: Network Manager
Members:
  - <network-engineer-01@domain>
  - <network-engineer-02@domain>
  - <firewall-admin-01@domain>

Azure RBAC Assignments:
  - Network Contributor on hub and spoke resource groups
  - Reader on other resources
  - PIM-eligible for Firewall Contributor (time-bound)

Status: [ ] Created  [ ] Members Added  [ ] RBAC Configured
```

#### Group 4: DevOps Team
```
Display Name: AZ-FSI-DevOps-Team
Description: DevOps engineers managing CI/CD pipelines and IaC deployments
Group Type: Security
Membership Type: Assigned
Owners: DevOps Manager
Members:
  - <devops-engineer-01@domain>
  - <devops-engineer-02@domain>
  - <automation-lead-01@domain>

Azure RBAC Assignments:
  - Contributor on Ring 1 & Ring 2 resources
  - Owner on deployment pipelines
  - Access to Container Registry and Key Vault (secrets)

Status: [ ] Created  [ ] Members Added  [ ] RBAC Configured
```

#### Group 5: Application Developers
```
Display Name: AZ-FSI-App-Developers
Description: Application developers deploying workloads to spoke networks
Group Type: Security
Membership Type: Assigned
Owners: Development Manager
Members:
  - <developer-01@domain>
  - <developer-02@domain>
  - <developer-03@domain>

Azure RBAC Assignments:
  - Reader on shared resources (hub VNet, shared Key Vault)
  - Contributor on application-specific resource groups
  - App Service Contributor, AKS Contributor

Status: [ ] Created  [ ] Members Added  [ ] RBAC Configured
```

#### Group 6: Read-Only Auditors
```
Display Name: AZ-FSI-Auditors
Description: Internal and external auditors reviewing compliance and configurations
Group Type: Security
Membership Type: Assigned
Owners: Compliance Manager
Members:
  - <auditor-01@domain>
  - <external-auditor-01@partner-domain>

Azure RBAC Assignments:
  - Reader on all resources
  - Log Analytics Reader
  - Policy Reader (view compliance state)

Status: [ ] Created  [ ] Members Added  [ ] RBAC Configured
```

### 2.2 PIM-Eligible Groups (Time-Bound Access)

#### Group 7: Emergency Responders
```
Display Name: AZ-FSI-Emergency-Responders
Description: PIM-eligible group for incident response requiring elevated privileges
Group Type: Security
Membership Type: Assigned
Owners: Security Manager
Members:
  - <incident-responder-01@domain>
  - <incident-responder-02@domain>

PIM Configuration:
  - Eligible Role: Owner on subscription
  - Maximum Duration: 4 hours
  - Approval Required: Yes (by CISO)
  - MFA on Activation: Yes
  - Justification Required: Yes

Status: [ ] Created  [ ] Members Added  [ ] PIM Configured
```

---

## 3. Service Principal Configuration

For automated deployment, create a dedicated Service Principal (App Registration):

### 3.1 Service Principal Creation

```bash
# Step 1: Create App Registration
az ad app create \
  --display-name "sp-azure-fsi-landingzone-deployment" \
  --available-to-other-tenants false

# Capture Application (Client) ID
APP_ID="<output-application-id>"

# Step 2: Create Service Principal
az ad sp create --id $APP_ID

# Capture Service Principal Object ID
SP_OBJECT_ID="<output-object-id>"

# Step 3: Create Client Secret (valid 1 year)
az ad app credential reset \
  --id $APP_ID \
  --years 1 \
  --display-name "LZ-Deployment-Secret-2025"

# Capture Client Secret (store securely)
CLIENT_SECRET="<output-secret>"
```

**Store in secure vault:**
```
Service Principal Details:
- Application (Client) ID: <APP_ID>
- Client Secret: <CLIENT_SECRET>
- Tenant ID: <AZURE_TENANT_ID>
- Subscription ID: <AZURE_SUBSCRIPTION_ID>

Storage Location: Azure Key Vault or Enterprise Secrets Manager
Access Control: Only DevOps/Platform team
Rotation Schedule: Every 365 days
```
Status: [ ] Created  [ ] Credentials Stored  [ ] RBAC Configured

### 3.2 Service Principal RBAC (See Section 4 & 5)

The Service Principal requires the same permissions as the Cloud Platform Team to execute automated deployments.

---

## 4. RBAC Option A: Minimal Built-in Roles

**Approach:** Use Azure's native built-in roles for faster deployment with less administrative overhead.

**Trade-offs:**
- ✅ Faster to implement
- ✅ Microsoft-maintained and updated
- ✅ Less operational complexity
- ⚠️ More permissions than strictly necessary (least privilege not fully enforced)

### 4.1 Subscription-Level Role Assignments

#### For Cloud Platform Team & Service Principal

**Role 1: Owner**
```bash
# Assign to Cloud Platform Team group
az role assignment create \
  --assignee "<AZ-FSI-CloudPlatform-Team-ObjectID>" \
  --role "Owner" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"

# Assign to Service Principal
az role assignment create \
  --assignee "<SP_OBJECT_ID>" \
  --role "Owner" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```

**Role Details:**
- **Role ID:** `8e3af657-a8ff-443c-a75c-2fe8c4bcb635`
- **Description:** Full access to manage all resources and assign roles
- **Why Required:**
  - Create and delete resource groups
  - Assign Azure Policies at subscription level
  - Create role assignments for managed identities
  - Configure subscription-level budgets
  - Manage all resources across rings (hub, spokes, shared services)

**Alternative (More Restrictive):**
```bash
# Instead of Owner, use Contributor + User Access Administrator
az role assignment create \
  --assignee "<AZ-FSI-CloudPlatform-Team-ObjectID>" \
  --role "Contributor" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"

az role assignment create \
  --assignee "<AZ-FSI-CloudPlatform-Team-ObjectID>" \
  --role "User Access Administrator" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```

**Alternative Role Details:**
- **Contributor:** `b24988ac-6180-42a0-ab88-20f7382dd24c` (all resource management)
- **User Access Administrator:** `18d7d88d-d35e-4fb5-a5c3-7773c20a72d9` (role assignments)
- **Why Required:** Separates resource management from access control for better audit trails

Status: [ ] Cloud Platform Team  [ ] Service Principal  [ ] Verified

#### For Security & Compliance Team

**Role 1: Security Admin**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Security-Team-ObjectID>" \
  --role "Security Admin" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
- **Role ID:** `fb1c8493-542b-48eb-b624-b4c8fea62acd`
- **Purpose:** Manage Microsoft Defender for Cloud, view security alerts, update policies

**Role 2: Reader**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Security-Team-ObjectID>" \
  --role "Reader" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
- **Role ID:** `acdd72a7-3385-48ef-bd42-f606fba81ae7`
- **Purpose:** View all resources for compliance auditing

**Role 3: Resource Policy Contributor**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Security-Team-ObjectID>" \
  --role "Resource Policy Contributor" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
- **Role ID:** `36243c78-bf99-498c-9df9-86d9f8d28608`
- **Purpose:** Assign and manage Azure Policies for GDPR, DORA, PSD2, etc.

Status: [ ] Assigned  [ ] Verified

#### For Network Operations Team

**Role 1: Network Contributor**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Network-Team-ObjectID>" \
  --role "Network Contributor" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-hub-networking-<env>"
```
- **Role ID:** `4d97b98b-1d4f-4787-a291-c67834d212e7`
- **Purpose:** Manage VNets, subnets, NSGs, Azure Firewall, VPN Gateway

**Role 2: Reader (Subscription)**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Network-Team-ObjectID>" \
  --role "Reader" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
- **Purpose:** View other resources for troubleshooting

Status: [ ] Assigned  [ ] Verified

#### For DevOps Team

**Role 1: Contributor (Resource Group Scoped)**
```bash
# Ring 1: Platform Services
az role assignment create \
  --assignee "<AZ-FSI-DevOps-Team-ObjectID>" \
  --role "Contributor" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-devops-<env>"

# Ring 2: Application Workloads
az role assignment create \
  --assignee "<AZ-FSI-DevOps-Team-ObjectID>" \
  --role "Contributor" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-app-<env>"
```
- **Purpose:** Deploy and manage application resources

**Role 2: Key Vault Secrets User**
```bash
az role assignment create \
  --assignee "<AZ-FSI-DevOps-Team-ObjectID>" \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-security-<env>/providers/Microsoft.KeyVault/vaults/kv-<project>-shared-<env>"
```
- **Role ID:** `4633458b-17de-408a-b874-0445c86b69e6`
- **Purpose:** Read secrets for CI/CD pipelines

Status: [ ] Assigned  [ ] Verified

#### For Application Developers

**Role 1: Reader (Hub Resources)**
```bash
az role assignment create \
  --assignee "<AZ-FSI-App-Developers-ObjectID>" \
  --role "Reader" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-hub-networking-<env>"
```

**Role 2: Contributor (App Resource Group)**
```bash
az role assignment create \
  --assignee "<AZ-FSI-App-Developers-ObjectID>" \
  --role "Contributor" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-app-<env>"
```

Status: [ ] Assigned  [ ] Verified

#### For Auditors

**Role 1: Reader (Subscription)**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Auditors-ObjectID>" \
  --role "Reader" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```

**Role 2: Log Analytics Reader**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Auditors-ObjectID>" \
  --role "Log Analytics Reader" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-monitoring-<env>/providers/Microsoft.OperationalInsights/workspaces/law-<project>-<env>"
```
- **Role ID:** `73c42c96-874c-492b-b04d-ab87d138a893`
- **Purpose:** View audit logs and compliance reports

Status: [ ] Assigned  [ ] Verified

### 4.2 Key Vault Access Policies (Built-in Roles)

**For Cloud Platform Team:**
```bash
az role assignment create \
  --assignee "<AZ-FSI-CloudPlatform-Team-ObjectID>" \
  --role "Key Vault Administrator" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-security-<env>/providers/Microsoft.KeyVault/vaults/kv-<project>-core-<env>"
```
- **Role ID:** `00482a5a-887f-4fb3-b363-3b7fe8e74483`
- **Purpose:** Full data plane access to secrets, keys, certificates

**For DevOps Team:**
```bash
az role assignment create \
  --assignee "<AZ-FSI-DevOps-Team-ObjectID>" \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-security-<env>/providers/Microsoft.KeyVault/vaults/kv-<project>-shared-<env>"
```
- **Purpose:** Read-only access to secrets for pipelines

Status: [ ] Assigned  [ ] Verified

### 4.3 Summary: Minimal Built-in Roles

| Group/Principal | Scope | Built-in Role | Purpose |
|-----------------|-------|---------------|---------|
| Cloud Platform Team | Subscription | Owner | Full deployment control |
| Cloud Platform Team (Alternative) | Subscription | Contributor + User Access Administrator | Separated permissions |
| Service Principal | Subscription | Owner | Automated deployment |
| Security Team | Subscription | Security Admin + Reader + Resource Policy Contributor | Compliance management |
| Network Ops | Hub RG | Network Contributor | Network infrastructure |
| Network Ops | Subscription | Reader | View other resources |
| DevOps Team | DevOps RG | Contributor | CI/CD management |
| DevOps Team | App RG | Contributor | Application deployment |
| DevOps Team | Shared Key Vault | Key Vault Secrets User | Read pipeline secrets |
| Developers | Hub RG | Reader | View shared resources |
| Developers | App RG | Contributor | Deploy applications |
| Auditors | Subscription | Reader | Compliance auditing |
| Auditors | Log Analytics | Log Analytics Reader | View audit logs |

---

## 5. RBAC Option B: Strict Custom Roles

**Approach:** Create custom roles with granular, atomic permissions for maximum security and compliance.

**Trade-offs:**
- ✅ True least privilege (only required permissions)
- ✅ Better audit trails (specific actions logged)
- ✅ Compliance-friendly (demonstrates due diligence)
- ⚠️ Higher administrative overhead
- ⚠️ Requires maintenance when Azure API changes

### 5.1 Custom Role Definitions

#### Custom Role 1: FSI Landing Zone Deployer

**Purpose:** Deploy landing zone infrastructure without full Owner permissions

**Role Definition JSON:**
```json
{
  "Name": "FSI Landing Zone Deployer",
  "Id": null,
  "IsCustom": true,
  "Description": "Deploy and manage Azure FSI Landing Zone infrastructure with least privilege",
  "Actions": [
    "Microsoft.Resources/subscriptions/resourceGroups/read",
    "Microsoft.Resources/subscriptions/resourceGroups/write",
    "Microsoft.Resources/subscriptions/resourceGroups/delete",
    "Microsoft.Resources/deployments/*",
    "Microsoft.Network/virtualNetworks/*",
    "Microsoft.Network/networkSecurityGroups/*",
    "Microsoft.Network/azureFirewalls/*",
    "Microsoft.Network/bastionHosts/*",
    "Microsoft.Network/virtualNetworkPeerings/*",
    "Microsoft.Network/privateDnsZones/*",
    "Microsoft.Network/ddosProtectionPlans/*",
    "Microsoft.Network/publicIPAddresses/*",
    "Microsoft.KeyVault/vaults/*",
    "Microsoft.KeyVault/vaults/secrets/*",
    "Microsoft.OperationalInsights/workspaces/*",
    "Microsoft.Storage/storageAccounts/*",
    "Microsoft.Security/pricings/write",
    "Microsoft.Security/securityContacts/write",
    "Microsoft.Authorization/policyAssignments/*",
    "Microsoft.Authorization/policyDefinitions/*",
    "Microsoft.Authorization/roleAssignments/read",
    "Microsoft.Authorization/roleAssignments/write",
    "Microsoft.Authorization/roleAssignments/delete",
    "Microsoft.ManagedIdentity/userAssignedIdentities/*",
    "Microsoft.Consumption/budgets/*",
    "Microsoft.CostManagement/budgets/*",
    "Microsoft.Insights/diagnosticSettings/*",
    "Microsoft.Insights/logProfiles/*"
  ],
  "NotActions": [
    "Microsoft.Authorization/roleDefinitions/write",
    "Microsoft.Authorization/roleDefinitions/delete",
    "Microsoft.Authorization/classicAdministrators/*",
    "Microsoft.Authorization/denyAssignments/*",
    "Microsoft.Blueprint/blueprintAssignments/write",
    "Microsoft.Blueprint/blueprintAssignments/delete"
  ],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/<SUBSCRIPTION-ID>"
  ]
}
```

**Deployment:**
```bash
az role definition create --role-definition fsi-landingzone-deployer.json
```

**Assignment:**
```bash
az role assignment create \
  --assignee "<AZ-FSI-CloudPlatform-Team-ObjectID>" \
  --role "FSI Landing Zone Deployer" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"

az role assignment create \
  --assignee "<SP_OBJECT_ID>" \
  --role "FSI Landing Zone Deployer" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```

Status: [ ] Defined  [ ] Created  [ ] Assigned

---

#### Custom Role 2: FSI Network Manager

**Purpose:** Manage networking components without access to other resources

**Role Definition JSON:**
```json
{
  "Name": "FSI Network Manager",
  "Id": null,
  "IsCustom": true,
  "Description": "Manage virtual networks, NSGs, firewall rules, and connectivity for FSI landing zone",
  "Actions": [
    "Microsoft.Network/virtualNetworks/read",
    "Microsoft.Network/virtualNetworks/write",
    "Microsoft.Network/virtualNetworks/delete",
    "Microsoft.Network/virtualNetworks/subnets/*",
    "Microsoft.Network/virtualNetworks/virtualNetworkPeerings/*",
    "Microsoft.Network/networkSecurityGroups/*",
    "Microsoft.Network/azureFirewalls/*",
    "Microsoft.Network/firewallPolicies/*",
    "Microsoft.Network/bastionHosts/read",
    "Microsoft.Network/publicIPAddresses/read",
    "Microsoft.Network/publicIPAddresses/write",
    "Microsoft.Network/routeTables/*",
    "Microsoft.Network/privateDnsZones/*",
    "Microsoft.Network/privateEndpoints/*",
    "Microsoft.Network/networkInterfaces/read",
    "Microsoft.Network/loadBalancers/read",
    "Microsoft.Network/applicationGateways/read",
    "Microsoft.Resources/subscriptions/resourceGroups/read",
    "Microsoft.Resources/deployments/read",
    "Microsoft.Insights/diagnosticSettings/*"
  ],
  "NotActions": [
    "Microsoft.Network/ddosProtectionPlans/write",
    "Microsoft.Network/ddosProtectionPlans/delete",
    "Microsoft.Network/virtualNetworkGateways/write",
    "Microsoft.Network/virtualNetworkGateways/delete"
  ],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/<SUBSCRIPTION-ID>"
  ]
}
```

**Deployment:**
```bash
az role definition create --role-definition fsi-network-manager.json
```

**Assignment:**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Network-Team-ObjectID>" \
  --role "FSI Network Manager" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```

Status: [ ] Defined  [ ] Created  [ ] Assigned

---

#### Custom Role 3: FSI Security Operator

**Purpose:** Manage security and compliance without modifying infrastructure

**Role Definition JSON:**
```json
{
  "Name": "FSI Security Operator",
  "Id": null,
  "IsCustom": true,
  "Description": "Manage Microsoft Defender, Azure Policies, and security monitoring for FSI compliance",
  "Actions": [
    "Microsoft.Security/*",
    "Microsoft.Authorization/policyAssignments/read",
    "Microsoft.Authorization/policyAssignments/write",
    "Microsoft.Authorization/policyDefinitions/read",
    "Microsoft.Authorization/policyDefinitions/write",
    "Microsoft.Authorization/policySetDefinitions/read",
    "Microsoft.Authorization/policySetDefinitions/write",
    "Microsoft.PolicyInsights/*",
    "Microsoft.OperationalInsights/workspaces/read",
    "Microsoft.OperationalInsights/workspaces/query/read",
    "Microsoft.Insights/alertRules/*",
    "Microsoft.Insights/diagnosticSettings/read",
    "Microsoft.Resources/subscriptions/resourceGroups/read",
    "Microsoft.Resources/deployments/read",
    "Microsoft.KeyVault/vaults/read",
    "Microsoft.Network/networkSecurityGroups/read",
    "Microsoft.Network/azureFirewalls/read",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Storage/storageAccounts/read"
  ],
  "NotActions": [
    "Microsoft.Security/pricings/delete"
  ],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/<SUBSCRIPTION-ID>"
  ]
}
```

**Deployment:**
```bash
az role definition create --role-definition fsi-security-operator.json
```

**Assignment:**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Security-Team-ObjectID>" \
  --role "FSI Security Operator" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```

Status: [ ] Defined  [ ] Created  [ ] Assigned

---

#### Custom Role 4: FSI Key Vault Operator

**Purpose:** Manage Key Vault secrets and keys for CI/CD without admin access

**Role Definition JSON:**
```json
{
  "Name": "FSI Key Vault Operator",
  "Id": null,
  "IsCustom": true,
  "Description": "Manage Key Vault secrets and certificates for DevOps pipelines",
  "Actions": [
    "Microsoft.KeyVault/vaults/read",
    "Microsoft.KeyVault/vaults/secrets/read",
    "Microsoft.KeyVault/vaults/secrets/write",
    "Microsoft.KeyVault/vaults/secrets/delete",
    "Microsoft.KeyVault/vaults/certificates/read",
    "Microsoft.Resources/subscriptions/resourceGroups/read"
  ],
  "NotActions": [
    "Microsoft.KeyVault/vaults/write",
    "Microsoft.KeyVault/vaults/delete",
    "Microsoft.KeyVault/vaults/accessPolicies/*",
    "Microsoft.Authorization/roleAssignments/*"
  ],
  "DataActions": [
    "Microsoft.KeyVault/vaults/secrets/getSecret/action",
    "Microsoft.KeyVault/vaults/secrets/setSecret/action",
    "Microsoft.KeyVault/vaults/certificates/read"
  ],
  "NotDataActions": [
    "Microsoft.KeyVault/vaults/keys/*",
    "Microsoft.KeyVault/vaults/secrets/delete",
    "Microsoft.KeyVault/vaults/secrets/purge/action"
  ],
  "AssignableScopes": [
    "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-security-<env>"
  ]
}
```

**Deployment:**
```bash
az role definition create --role-definition fsi-keyvault-operator.json
```

**Assignment:**
```bash
az role assignment create \
  --assignee "<AZ-FSI-DevOps-Team-ObjectID>" \
  --role "FSI Key Vault Operator" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-security-<env>"
```

Status: [ ] Defined  [ ] Created  [ ] Assigned

---

#### Custom Role 5: FSI DevOps Deployer

**Purpose:** Deploy application workloads without access to hub infrastructure

**Role Definition JSON:**
```json
{
  "Name": "FSI DevOps Deployer",
  "Id": null,
  "IsCustom": true,
  "Description": "Deploy and manage application resources in spoke VNets for DevOps pipelines",
  "Actions": [
    "Microsoft.Resources/subscriptions/resourceGroups/read",
    "Microsoft.Resources/deployments/*",
    "Microsoft.Web/sites/*",
    "Microsoft.Web/serverfarms/*",
    "Microsoft.ContainerRegistry/registries/read",
    "Microsoft.ContainerRegistry/registries/pull/read",
    "Microsoft.ContainerRegistry/registries/push/write",
    "Microsoft.ContainerService/managedClusters/read",
    "Microsoft.ContainerService/managedClusters/listClusterAdminCredential/action",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/virtualMachines/write",
    "Microsoft.Compute/disks/*",
    "Microsoft.Storage/storageAccounts/read",
    "Microsoft.Storage/storageAccounts/blobServices/*",
    "Microsoft.Storage/storageAccounts/queueServices/*",
    "Microsoft.Network/virtualNetworks/read",
    "Microsoft.Network/virtualNetworks/subnets/read",
    "Microsoft.Network/networkInterfaces/*",
    "Microsoft.Network/publicIPAddresses/read",
    "Microsoft.Network/loadBalancers/read",
    "Microsoft.Insights/diagnosticSettings/*",
    "Microsoft.OperationalInsights/workspaces/read"
  ],
  "NotActions": [
    "Microsoft.Network/virtualNetworks/write",
    "Microsoft.Network/virtualNetworks/delete",
    "Microsoft.Network/networkSecurityGroups/write",
    "Microsoft.Network/networkSecurityGroups/delete",
    "Microsoft.Authorization/roleAssignments/*"
  ],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-app-<env>",
    "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-devops-<env>"
  ]
}
```

**Deployment:**
```bash
az role definition create --role-definition fsi-devops-deployer.json
```

**Assignment:**
```bash
az role assignment create \
  --assignee "<AZ-FSI-DevOps-Team-ObjectID>" \
  --role "FSI DevOps Deployer" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-app-<env>"

az role assignment create \
  --assignee "<AZ-FSI-DevOps-Team-ObjectID>" \
  --role "FSI DevOps Deployer" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-devops-<env>"
```

Status: [ ] Defined  [ ] Created  [ ] Assigned

---

#### Custom Role 6: FSI Compliance Auditor

**Purpose:** Read-only access to all resources plus policy compliance data

**Role Definition JSON:**
```json
{
  "Name": "FSI Compliance Auditor",
  "Id": null,
  "IsCustom": true,
  "Description": "Read-only access to all FSI landing zone resources and compliance data for auditing",
  "Actions": [
    "*/read",
    "Microsoft.PolicyInsights/*",
    "Microsoft.Security/*/read",
    "Microsoft.OperationalInsights/workspaces/query/read",
    "Microsoft.Authorization/policyAssignments/read",
    "Microsoft.Authorization/policyDefinitions/read",
    "Microsoft.Authorization/roleAssignments/read",
    "Microsoft.Authorization/roleDefinitions/read",
    "Microsoft.CostManagement/*/read",
    "Microsoft.Consumption/*/read"
  ],
  "NotActions": [],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/<SUBSCRIPTION-ID>"
  ]
}
```

**Deployment:**
```bash
az role definition create --role-definition fsi-compliance-auditor.json
```

**Assignment:**
```bash
az role assignment create \
  --assignee "<AZ-FSI-Auditors-ObjectID>" \
  --role "FSI Compliance Auditor" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```

Status: [ ] Defined  [ ] Created  [ ] Assigned

---

### 5.2 Summary: Strict Custom Roles

| Custom Role | Assigned To | Scope | Key Permissions |
|-------------|-------------|-------|-----------------|
| FSI Landing Zone Deployer | Cloud Platform Team, Service Principal | Subscription | RG, VNet, Firewall, Key Vault, Policy, Budget |
| FSI Network Manager | Network Ops Team | Subscription | VNet, NSG, Firewall rules, Peering, Private DNS |
| FSI Security Operator | Security Team | Subscription | Defender, Policies, Alerts, Audit logs (read-only infra) |
| FSI Key Vault Operator | DevOps Team | Security RG | Secrets read/write, Certificates read (no keys) |
| FSI DevOps Deployer | DevOps Team | App RG, DevOps RG | App Service, AKS, VMs, Storage (no network changes) |
| FSI Compliance Auditor | Auditors | Subscription | Read-only all resources + policy compliance |

---

## 6. Validation Checklist

Before initiating automated deployment, verify all prerequisites:

### 6.1 Entra ID Configuration
- [ ] MFA enabled for all users (except break-glass)
- [ ] Azure AD Premium P2 licenses activated
- [ ] PIM configured (8-hour max duration, approval required)
- [ ] 5 Conditional Access policies deployed and enabled
- [ ] 2 break-glass accounts created and tested
- [ ] Guest user restrictions configured

### 6.2 Security Groups
- [ ] AZ-FSI-CloudPlatform-Team created with members
- [ ] AZ-FSI-Security-Team created with members
- [ ] AZ-FSI-Network-Team created with members
- [ ] AZ-FSI-DevOps-Team created with members
- [ ] AZ-FSI-App-Developers created with members
- [ ] AZ-FSI-Auditors created with members
- [ ] AZ-FSI-Emergency-Responders created with PIM configuration

### 6.3 Service Principal
- [ ] App Registration created
- [ ] Service Principal created
- [ ] Client Secret generated and stored securely
- [ ] Secret rotation schedule documented (365 days)

### 6.4 RBAC Assignments (Option A or B)
- [ ] Cloud Platform Team role assignments completed
- [ ] Service Principal role assignments completed
- [ ] Security Team role assignments completed
- [ ] Network Ops role assignments completed
- [ ] DevOps Team role assignments completed
- [ ] Developers role assignments completed
- [ ] Auditors role assignments completed

### 6.5 Key Vault Access
- [ ] Cloud Platform Team: Key Vault Administrator
- [ ] DevOps Team: Key Vault Secrets User (or FSI Key Vault Operator)
- [ ] Service Principal: Key Vault Administrator

### 6.6 Testing
- [ ] Test user login with MFA
- [ ] Test PIM activation for Emergency Responders group
- [ ] Test Service Principal authentication (`az login --service-principal`)
- [ ] Test role assignment verification (`az role assignment list`)
- [ ] Test break-glass account login (without MFA)

### 6.7 Documentation
- [ ] All Object IDs documented (groups, service principal)
- [ ] Client Secret stored in enterprise vault
- [ ] RBAC assignment summary created
- [ ] Emergency contact list updated
- [ ] Handover document prepared for DevOps team

---

## 7. Deployment Phase Roles

### Phase 1: Foundation Deployment (Ring 0)

**Active Roles:**
- Cloud Platform Team: Owner (or FSI Landing Zone Deployer)
- Service Principal: Owner (or FSI Landing Zone Deployer)

**Required Permissions:**
- Create resource groups
- Assign Azure Policies (GDPR, DORA, data residency)
- Create budgets and cost alerts
- Create Log Analytics Workspace
- Create Storage Account for diagnostics

**Duration:** 1-2 hours

---

### Phase 2: Hub Networking (Ring 1)

**Active Roles:**
- Cloud Platform Team: Owner (or FSI Landing Zone Deployer)
- Network Ops Team: Network Contributor (or FSI Network Manager)
- Service Principal: Owner (or FSI Landing Zone Deployer)

**Required Permissions:**
- Create hub VNet with subnets (AzureFirewallSubnet, AzureBastionSubnet, GatewaySubnet)
- Deploy Azure Firewall (Basic or Premium)
- Deploy Azure Bastion
- Create NSGs and associate with subnets
- Create Private DNS Zones
- Deploy DDoS Protection Plan

**Duration:** 2-4 hours

---

### Phase 3: Security & Compliance (Ring 1)

**Active Roles:**
- Cloud Platform Team: Owner (or FSI Landing Zone Deployer)
- Security Team: Security Admin (or FSI Security Operator)
- Service Principal: Owner (or FSI Landing Zone Deployer)

**Required Permissions:**
- Create Key Vault (Standard or Premium)
- Enable Microsoft Defender for Cloud (Standard tier)
- Configure diagnostic settings for all resources
- Apply FSI compliance policy initiatives
- Create managed identities for Key Vault access

**Duration:** 2-3 hours

---

### Phase 4: Spoke Networks (Ring 2)

**Active Roles:**
- Cloud Platform Team: Owner (or FSI Landing Zone Deployer)
- Network Ops Team: Network Contributor (or FSI Network Manager)
- Service Principal: Owner (or FSI Landing Zone Deployer)

**Required Permissions:**
- Create spoke VNets (App, DevOps)
- Configure VNet peering (spoke-to-hub)
- Create NSGs for spoke subnets
- Create route tables (force tunneling to Firewall)

**Duration:** 1-2 hours

---

### Phase 5: Workload Deployment (Ring 2 & 3)

**Active Roles:**
- DevOps Team: Contributor (or FSI DevOps Deployer)
- Developers: Contributor (app RG scope)

**Required Permissions:**
- Deploy App Service Plans
- Deploy AKS clusters
- Deploy Virtual Machines
- Deploy Storage Accounts (application data)
- Configure private endpoints

**Duration:** Ongoing

---

## 8. Security Considerations

### 8.1 Least Privilege Principle

**Option A (Built-in Roles):**
- Use Contributor + User Access Administrator instead of Owner when possible
- Scope roles to resource groups instead of subscription when applicable
- Use PIM for temporary elevation (Emergency Responders)

**Option B (Custom Roles):**
- Regularly review and audit custom role permissions
- Update custom roles when Azure API changes
- Document rationale for each permission in Actions array

### 8.2 Separation of Duties

| Team | Focus Area | Cannot Modify |
|------|------------|---------------|
| Network Ops | Networking | Security policies, Key Vault, IAM |
| Security Team | Compliance | Infrastructure deployment, networking |
| DevOps | Application workloads | Hub networking, security policies |
| Developers | Application code | Shared infrastructure, networking |

### 8.3 Audit Trail

**Enable logging for:**
- Azure Activity Log (90-day retention minimum)
- Entra ID Sign-in logs (30-day retention minimum)
- Entra ID Audit logs (30-day retention minimum)
- Key Vault audit logs (365-day retention)
- RBAC role assignment changes (Activity Log)

**Configure alerts for:**
- Break-glass account sign-in
- PIM activations for Owner role
- Azure Policy non-compliance (critical policies)
- Key Vault access outside business hours
- Role assignment changes

### 8.4 Emergency Access Procedures

**Break-Glass Account Usage:**
1. Retrieve break-glass credentials from physical vault
2. Log incident in security ticketing system (e.g., Jira, ServiceNow)
3. Use break-glass account for emergency changes
4. Document all actions taken
5. Rotate break-glass password after use
6. Conduct post-incident review

**Escalation Path:**
1. Level 1: Cloud Platform Team (standard changes)
2. Level 2: Emergency Responders (PIM activation, 4-hour window)
3. Level 3: Break-Glass Accounts (critical outage, approval from CISO)

---

## Appendix A: Azure CLI Commands Reference

### Create Custom Role
```bash
az role definition create --role-definition @fsi-landingzone-deployer.json
```

### List Custom Roles
```bash
az role definition list --custom-role-only true --output table
```

### Assign Role to Group
```bash
az role assignment create \
  --assignee <GROUP-OBJECT-ID> \
  --role "FSI Landing Zone Deployer" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```

### Assign Role to Service Principal
```bash
az role assignment create \
  --assignee <SP-OBJECT-ID> \
  --role "FSI Landing Zone Deployer" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```

### List Role Assignments for Group
```bash
az role assignment list \
  --assignee <GROUP-OBJECT-ID> \
  --output table
```

### Test Service Principal Authentication
```bash
az login --service-principal \
  --username <APP-ID> \
  --password <CLIENT-SECRET> \
  --tenant <TENANT-ID>

az account show
```

---

## Appendix B: Group Object ID Retrieval

### Get Group Object ID
```bash
az ad group show \
  --group "AZ-FSI-CloudPlatform-Team" \
  --query "id" \
  --output tsv
```

### Get Service Principal Object ID
```bash
az ad sp show \
  --id <APP-ID> \
  --query "id" \
  --output tsv
```

### List All FSI Groups
```bash
az ad group list \
  --filter "startswith(displayName,'AZ-FSI')" \
  --query "[].{Name:displayName, ObjectId:id}" \
  --output table
```

---

## Appendix C: Custom Role JSON Files

All custom role definitions are provided as separate JSON files:

1. `fsi-landingzone-deployer.json`
2. `fsi-network-manager.json`
3. `fsi-security-operator.json`
4. `fsi-keyvault-operator.json`
5. `fsi-devops-deployer.json`
6. `fsi-compliance-auditor.json`

**Deployment Script:**
```bash
#!/bin/bash
# deploy-custom-roles.sh

SUBSCRIPTION_ID="<YOUR-SUBSCRIPTION-ID>"

echo "Creating custom roles for Azure FSI Landing Zone..."

az role definition create --role-definition fsi-landingzone-deployer.json
az role definition create --role-definition fsi-network-manager.json
az role definition create --role-definition fsi-security-operator.json
az role definition create --role-definition fsi-keyvault-operator.json
az role definition create --role-definition fsi-devops-deployer.json
az role definition create --role-definition fsi-compliance-auditor.json

echo "Custom roles created successfully."
az role definition list --custom-role-only true --output table
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | Azure FSI Landing Zone Team | Initial specification |

**Distribution:**
- Client IT Security Team
- Client Cloud Architects
- Client Compliance Officers
- Azure FSI Landing Zone DevOps Team

**Approval:**
- [ ] Client CISO
- [ ] Client IT Director
- [ ] Azure FSI Landing Zone Lead Architect

---

**END OF DOCUMENT**
