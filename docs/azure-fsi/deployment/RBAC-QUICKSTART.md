# Azure FSI Landing Zone - RBAC Quick Start Guide

**For:** Enterprise IT Security Teams & Cloud Architects
**Purpose:** Quick reference for manual prerequisites and RBAC setup
**Time Required:** 4-8 hours (depending on organization approval processes)

---

## Overview

This guide provides a streamlined checklist for setting up manual prerequisites before deploying the Azure FSI Landing Zone using automated agents. Choose between two RBAC approaches:

- **Option A:** Minimal Built-in Roles (faster, standard Azure roles)
- **Option B:** Strict Custom Roles (maximum security, granular permissions)

📄 **Full Specification:** [rbac-specification.md](rbac-specification.md)

---

## Phase 1: Entra ID Security Baseline (2-3 hours)

### 1.1 Enable MFA
```
☐ Enable MFA for all users (except break-glass accounts)
☐ Configure Microsoft Authenticator app as primary method
☐ Test MFA enrollment for pilot users
```

### 1.2 Configure PIM (Requires Azure AD Premium P2)
see [Valid licenses for PIM](https://learn.microsoft.com/en-us/entra/id-governance/licensing-fundamentals#valid-licenses-for-pim)
```
☐ Enable PIM features
☐ Set activation duration: 8 hours maximum
☐ Enable approval workflow for Owner role
☐ Enable MFA on activation
☐ Test PIM activation with test user
```

### 1.3 Deploy Conditional Access Policies (5 policies)
```
☐ CA001: Require MFA for all users
☐ CA002: Block legacy authentication
☐ CA003: Geo-blocking (EU only for FSI)
☐ CA004: Require compliant device
☐ CA005: Block high-risk sign-ins
```

### 1.4 Create Break-Glass Accounts (2 accounts)
```
☐ Create break-glass-01@<tenant>.onmicrosoft.com
☐ Create break-glass-02@<tenant>.onmicrosoft.com
☐ Assign Global Administrator (permanent)
☐ Disable MFA (emergency access requirement)
☐ Store credentials in physical vault + Azure Key Vault
☐ Configure sign-in alerts
```

---

## Phase 2: Create Security Groups (1 hour)

Create these Entra ID security groups:

```
☐ AZ-FSI-CloudPlatform-Team       → Cloud architects, platform engineers
☐ AZ-FSI-Security-Team            → Security officers, compliance managers
☐ AZ-FSI-Network-Team             → Network engineers
☐ AZ-FSI-DevOps-Team              → DevOps engineers
☐ AZ-FSI-App-Developers           → Application developers
☐ AZ-FSI-Auditors                 → Internal/external auditors
☐ AZ-FSI-Emergency-Responders     → PIM-eligible incident responders
```

**For each group:**
1. Set type: `Security`
2. Set membership: `Assigned` (not dynamic)
3. Add group owner(s)
4. Add group member(s)
5. Document Object ID : `<OBJECT-ID>`

TODO : for deeper separation of concerns and more granular access management split `-Team` groups in `-Owners` and `-Members` groups

---

## Phase 3: Service Principal for Automation (30 minutes)

```bash
# Create App Registration
az ad app create --display-name "sp-azure-fsi-landingzone-deployment"

# Create Service Principal
az ad sp create --id <APP-ID>

# Create Client Secret (1 year validity)
az ad app credential reset --id <APP-ID> --years 1
```

```
☐ Store Application (Client) ID in secure vault
☐ Store Client Secret in secure vault
☐ Store Tenant ID in secure vault
☐ Document secret expiration date (set calendar reminder)
☐ Define secret rotation process
```

---

## Phase 4: RBAC Configuration (2-4 hours)

### Option A: Minimal Built-in Roles (Recommended for Quick Start)

#### Subscription-Level Assignments

**Cloud Platform Team + Service Principal:**
`AZ-FSI-CloudPlatform-Team` 
```bash
# Option 1: Owner role (simplest)
az role assignment create --assignee <OBJECT-ID> --role "Owner" --scope "/subscriptions/<SUBSCRIPTION-ID>"

# Option 2: Separated permissions (more secure and cleaner audit trail for the security team)
az role assignment create --assignee <OBJECT-ID> --role "Contributor" --scope "/subscriptions/<SUBSCRIPTION-ID>"
az role assignment create --assignee <OBJECT-ID> --role "User Access Administrator" --scope "/subscriptions/<SUBSCRIPTION-ID>"

# **Note:** 
# Just-in-time access is configured for `User Access Administrator` and `Owner` roles via PIM.
# Require Approvals/MFA/Justification all set to true
```
```
☐ Assign role to AZ-FSI-CloudPlatform-Team
☐ Assign role to Service Principal
☐ Verify assignments
```

**Security & Compliance Team:**
`AZ-FSI-Security-Team`
```bash
az role assignment create --assignee <OBJECT-ID> --role "Security Admin" --scope "/subscriptions/<SUBSCRIPTION-ID>"
az role assignment create --assignee <OBJECT-ID> --role "Reader" --scope "/subscriptions/<SUBSCRIPTION-ID>"
az role assignment create --assignee <OBJECT-ID> --role "Resource Policy Contributor" --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
```
☐ Assign roles to AZ-FSI-Security-Team
☐ Verify assignments
```

**Network Operations Team:**
`AZ-FSI-Network-Team`
```bash
az role assignment create --assignee <OBJECT-ID> --role "Network Contributor" --scope "/subscriptions/<SUBSCRIPTION-ID>"
az role assignment create --assignee <OBJECT-ID> --role "Reader" --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
```
☐ Assign roles to AZ-FSI-Network-Team
☐ Verify assignments
```

**Auditors:**
```bash
az role assignment create --assignee <OBJECT-ID> --role "Reader" --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
```
☐ Assign role to AZ-FSI-Auditors
☐ Verify assignments
```

---

### Option B: Strict Custom Roles (Maximum Security)

#### Step 1: Deploy Custom Roles

```bash
cd docs/azure-fsi/deployment/custom-roles
export AZURE_SUBSCRIPTION_ID="<YOUR-SUBSCRIPTION-ID>"
./deploy-custom-roles.sh
```
```
☐ Review deployment output
☐ Verify all 6 custom roles created
```

#### Step 2: Assign Custom Roles

**Cloud Platform Team + Service Principal:**
```bash
az role assignment create \
  --assignee <OBJECT-ID> \
  --role "FSI Landing Zone Deployer" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
```
☐ Assign to AZ-FSI-CloudPlatform-Team
☐ Assign to Service Principal
```

**Security Team:**
```bash
az role assignment create \
  --assignee <OBJECT-ID> \
  --role "FSI Security Operator" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
```
☐ Assign to AZ-FSI-Security-Team
```

**Network Ops:**
```bash
az role assignment create \
  --assignee <OBJECT-ID> \
  --role "FSI Network Manager" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
```
☐ Assign to AZ-FSI-Network-Team
```

**DevOps Team:**
```bash
az role assignment create \
  --assignee <OBJECT-ID> \
  --role "FSI Key Vault Operator" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-security-<env>"

az role assignment create \
  --assignee <OBJECT-ID> \
  --role "FSI DevOps Deployer" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-app-<env>"
```
```
☐ Assign Key Vault Operator role
☐ Assign DevOps Deployer role
```

**Auditors:**
```bash
az role assignment create \
  --assignee <OBJECT-ID> \
  --role "FSI Compliance Auditor" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>"
```
```
☐ Assign to AZ-FSI-Auditors
```

---

## Phase 5: Key Vault RBAC (After Ring 0/Ring 1 Deployment)

**For Option A (Built-in Roles):**
```bash
# Cloud Platform Team: Full access
az role assignment create \
  --assignee <CLOUD-PLATFORM-TEAM-OBJECT-ID> \
  --role "Key Vault Administrator" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-security-<env>/providers/Microsoft.KeyVault/vaults/kv-<project>-core-<env>"

# DevOps Team: Read secrets only
az role assignment create \
  --assignee <DEVOPS-TEAM-OBJECT-ID> \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<SUBSCRIPTION-ID>/resourceGroups/rg-<project>-security-<env>/providers/Microsoft.KeyVault/vaults/kv-<project>-shared-<env>"
```

**For Option B (Custom Roles):**
DevOps Team already has "FSI Key Vault Operator" role assigned at RG scope.

```
☐ Assign Key Vault Administrator to Cloud Platform Team
☐ Assign Key Vault Secrets User (or FSI Key Vault Operator) to DevOps Team
☐ Test Key Vault access
```

---

## Phase 6: Validation & Testing (1 hour)

### Test User Access
```bash
# Test MFA login
az login --username user@domain.com

# Test role permissions
az group list --output table
az network vnet list --output table
```
```
☐ Test 2-3 users from each group
☐ Verify MFA prompts
☐ Verify Conditional Access enforcement
```

### Test Service Principal
```bash
az login --service-principal \
  --username <APP-ID> \
  --password <CLIENT-SECRET> \
  --tenant <TENANT-ID>

# Should succeed (list resources)
az group list --output table

# Test deployment permissions
az deployment sub what-if \
  --name "test-deployment" \
  --location westeurope \
  --template-file test.bicep

az logout
```
```
☐ Test Service Principal authentication
☐ Verify deployment permissions
☐ Test Key Vault access (if applicable)
```

### Test PIM Activation
```bash
# List eligible roles
az rest --method GET \
  --url "https://graph.microsoft.com/v1.0/me/roleEligibilityScheduleInstances"

# Activate role (via Azure Portal → PIM)
```
```
☐ Test PIM activation for Emergency Responders group
☐ Verify approval workflow
☐ Verify MFA on activation
☐ Verify 8-hour time limit
```

### Test Break-Glass Accounts
```bash
# Login as break-glass account (should NOT prompt for MFA)
az login --username break-glass-01@<tenant>.onmicrosoft.com
az account show
az logout
```
```
☐ Test break-glass-01 login
☐ Test break-glass-02 login
☐ Verify no MFA prompt
☐ Verify Global Administrator access
☐ Check sign-in alerts triggered
```

---

## Phase 7: Documentation & Handover (1 hour)

```
☐ Document all group Object IDs
☐ Document Service Principal App ID and Object ID
☐ Store Client Secret in enterprise vault (with expiration date)
☐ Create RBAC assignment summary spreadsheet
☐ Update emergency contact list
☐ Create break-glass account access procedures
☐ Document PIM activation process
☐ Schedule quarterly access review
☐ Schedule annual custom role review (Option B only)
☐ Brief DevOps team on deployment prerequisites complete
```

---

## Quick Reference: Required Information

Before starting deployment, collect these values:

```
Azure Subscription:
- Subscription ID: _______________________________________
- Tenant ID: _____________________________________________

Service Principal:
- Application (Client) ID: _______________________________
- Client Secret: _________________________________________ (expires: _______)
- Object ID: _____________________________________________

Entra ID Groups (Object IDs):
- AZ-FSI-CloudPlatform-Team: _____________________________
- AZ-FSI-Security-Team: __________________________________
- AZ-FSI-Network-Team: ____________________________________
- AZ-FSI-DevOps-Team: ____________________________________
- AZ-FSI-App-Developers: _________________________________
- AZ-FSI-Auditors: _______________________________________
- AZ-FSI-Emergency-Responders: ___________________________

Break-Glass Accounts:
- break-glass-01@<tenant>.onmicrosoft.com (password stored in: _______)
- break-glass-02@<tenant>.onmicrosoft.com (password stored in: _______)

RBAC Approach Selected:
☐ Option A: Minimal Built-in Roles
☐ Option B: Strict Custom Roles
```

---

## Common Issues & Solutions

### Issue: "Insufficient privileges to complete operation"
**Solution:** Verify you have `User Access Administrator` or `Owner` role at subscription level.

### Issue: "Conditional Access policy blocking access"
**Solution:** Ensure you're connecting from an EU IP address and using a compliant device. Contact security team to add exception if needed.

### Issue: "Service Principal authentication fails"
**Solution:** Verify Client Secret hasn't expired. Check Application ID and Tenant ID are correct. Ensure Service Principal has been created (`az ad sp create`).

### Issue: "PIM activation not working"
**Solution:** Verify Azure AD Premium P2 license is active. Check user is member of PIM-eligible group. Wait 5-10 minutes for role propagation.

### Issue: "Break-glass account prompts for MFA"
**Solution:** Verify account is excluded from CA001 (Require MFA) policy. Update Conditional Access policy exclusions.

---

## Next Steps

After completing this checklist:

1. ✅ **Notify DevOps Team**: Prerequisites are complete, ready for automated deployment
2. ✅ **Provide Credentials**: Share Service Principal credentials via secure channel
3. ✅ **Review Deployment Guide**: [../../../agents/azure-fsi-landingzone/demo-squad/DEPLOYMENT-GUIDE.md](../../../agents/azure-fsi-landingzone/demo-squad/DEPLOYMENT-GUIDE.md)
4. ✅ **Schedule Deployment**: Coordinate with platform team for Ring 0 → Ring 1 → Ring 2 deployment
5. ✅ **Plan Validation**: Schedule compliance validation using [azure-compliance-checker agent](../../../agents/azure-compliance-checker/)

---

## Support & Documentation

- **Full RBAC Specification:** [rbac-specification.md](rbac-specification.md)
- **Custom Roles Details:** [custom-roles/README.md](custom-roles/README.md)
- **Deployment Guide:** [../../../agents/azure-fsi-landingzone/demo-squad/DEPLOYMENT-GUIDE.md](../../../agents/azure-fsi-landingzone/demo-squad/DEPLOYMENT-GUIDE.md)
- **Compliance Summary:** [../compliance/summary.md](../compliance/summary.md)
- **Architecture Overview:** [../architecture/rings.md](../architecture/rings.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-22
**Estimated Completion Time:** 4-8 hours
