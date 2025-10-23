# Azure FSI Landing Zone - Custom RBAC Roles

This directory contains custom Azure RBAC role definitions for deploying and managing the Azure FSI Landing Zone with granular, least-privilege permissions.

## Overview

These custom roles provide an alternative to Azure's built-in roles (Owner, Contributor, etc.) by implementing fine-grained permissions based on the principle of least privilege. Each role is designed for specific team responsibilities in the landing zone deployment lifecycle.

## Custom Roles

| Role Name | File | Purpose | Assigned To |
|-----------|------|---------|-------------|
| **FSI Landing Zone Deployer** | `fsi-landingzone-deployer.json` | Deploy all landing zone infrastructure | Cloud Platform Team, Service Principal |
| **FSI Network Manager** | `fsi-network-manager.json` | Manage VNets, NSGs, Firewall, connectivity | Network Operations Team |
| **FSI Security Operator** | `fsi-security-operator.json` | Manage Defender, Policies, security monitoring | Security & Compliance Team |
| **FSI Key Vault Operator** | `fsi-keyvault-operator.json` | Manage Key Vault secrets for CI/CD | DevOps Team |
| **FSI DevOps Deployer** | `fsi-devops-deployer.json` | Deploy application workloads in spoke VNets | DevOps Team |
| **FSI Compliance Auditor** | `fsi-compliance-auditor.json` | Read-only access + policy compliance data | Auditors, Compliance Team |

## Quick Start

### Prerequisites

1. **Azure CLI** installed and authenticated:
   ```bash
   az login
   az account set --subscription "<SUBSCRIPTION-ID>"
   ```

2. **Permissions**: You need `User Access Administrator` or `Owner` role to create custom roles.

3. **Subscription ID**: Set your subscription ID as an environment variable:
   ```bash
   export AZURE_SUBSCRIPTION_ID="12345678-1234-1234-1234-123456789abc"
   ```

### Deploy All Custom Roles

Use the automated deployment script:

```bash
./deploy-custom-roles.sh
```

This script will:
- Check Azure authentication
- Update JSON files with your subscription ID
- Create or update all custom roles
- Display deployment summary
- Restore original JSON files

### Deploy Individual Role

To create a single custom role:

```bash
# Update subscription ID in JSON file
sed -i "s|<SUBSCRIPTION-ID>|$AZURE_SUBSCRIPTION_ID|g" fsi-landingzone-deployer.json

# Create the role
az role definition create --role-definition fsi-landingzone-deployer.json

# Restore placeholder
sed -i "s|$AZURE_SUBSCRIPTION_ID|<SUBSCRIPTION-ID>|g" fsi-landingzone-deployer.json
```

## Role Assignments

After creating custom roles, assign them to security groups or service principals:

### Assign to Entra ID Group

```bash
# Get group Object ID
GROUP_OBJECT_ID=$(az ad group show \
  --group "AZ-FSI-CloudPlatform-Team" \
  --query "id" \
  --output tsv)

# Assign role at subscription scope
az role assignment create \
  --assignee "$GROUP_OBJECT_ID" \
  --role "FSI Landing Zone Deployer" \
  --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID"
```

### Assign to Service Principal

```bash
# Get service principal Object ID
SP_OBJECT_ID=$(az ad sp show \
  --id "<APP-ID>" \
  --query "id" \
  --output tsv)

# Assign role at subscription scope
az role assignment create \
  --assignee "$SP_OBJECT_ID" \
  --role "FSI Landing Zone Deployer" \
  --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID"
```

### Assign at Resource Group Scope

```bash
# For roles that should be scoped to specific resource groups
az role assignment create \
  --assignee "$GROUP_OBJECT_ID" \
  --role "FSI Network Manager" \
  --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/rg-demo-hub-networking-staging"
```

## Role Details

### 1. FSI Landing Zone Deployer

**Permissions Highlights:**
- ✅ Create/delete resource groups
- ✅ Deploy Azure resources (VNets, Firewall, Bastion, Key Vault, etc.)
- ✅ Assign Azure Policies
- ✅ Create role assignments (for managed identities)
- ✅ Configure budgets and cost management
- ❌ Cannot create/delete custom role definitions
- ❌ Cannot modify classic administrators
- ❌ Cannot create/delete blueprints

**Use Cases:**
- Automated landing zone deployment via Service Principal
- Cloud Platform Team infrastructure management
- IaC pipeline execution (Bicep, Terraform)

---

### 2. FSI Network Manager

**Permissions Highlights:**
- ✅ Full VNet management (create, modify, delete)
- ✅ Subnet management and VNet peering
- ✅ NSG and firewall rule management
- ✅ Private DNS Zones
- ✅ Route tables and private endpoints
- ❌ Cannot modify DDoS Protection Plans
- ❌ Cannot modify VPN Gateways

**Use Cases:**
- Network Operations Team day-to-day management
- Firewall rule updates
- VNet peering configuration
- NSG troubleshooting

---

### 3. FSI Security Operator

**Permissions Highlights:**
- ✅ Full Microsoft Defender for Cloud management
- ✅ Azure Policy assignment and definition
- ✅ Security alert management
- ✅ Log Analytics queries (read-only)
- ✅ Read-only access to infrastructure (VNets, Key Vault, etc.)
- ❌ Cannot delete Defender pricing tiers

**Use Cases:**
- Security & Compliance Team policy enforcement
- Compliance framework management (GDPR, DORA, PSD2)
- Security posture monitoring
- Incident response (read-only infrastructure access)

---

### 4. FSI Key Vault Operator

**Permissions Highlights:**
- ✅ Read Key Vault properties
- ✅ Get/Set secrets (data plane)
- ✅ Read certificates
- ❌ Cannot create/delete Key Vaults
- ❌ Cannot modify access policies
- ❌ Cannot manage keys (cryptographic operations)
- ❌ Cannot purge secrets

**Use Cases:**
- DevOps pipeline secret management
- CI/CD integration
- Application configuration management
- Certificate deployment (read-only)

**Scope:** Typically assigned at Key Vault or Resource Group level, not subscription.

---

### 5. FSI DevOps Deployer

**Permissions Highlights:**
- ✅ Deploy App Service, AKS, VMs
- ✅ Manage Container Registry (push/pull images)
- ✅ Manage Storage Accounts (blobs, queues)
- ✅ Read VNet and subnet information
- ✅ Manage NICs and load balancers
- ❌ Cannot modify VNets or NSGs
- ❌ Cannot assign roles

**Use Cases:**
- Application workload deployment
- Container image management
- DevOps pipeline execution
- Blue/green deployments

**Scope:** Typically assigned at App/DevOps Resource Group level.

---

### 6. FSI Compliance Auditor

**Permissions Highlights:**
- ✅ Read-only access to all resources (`*/read`)
- ✅ Full policy compliance insights
- ✅ Query Log Analytics
- ✅ View cost management data
- ✅ View role assignments and definitions
- ❌ No write permissions

**Use Cases:**
- Internal audit reviews
- External compliance assessments
- Regulatory reporting
- Security posture validation

---

## Validation

### List Custom Roles

```bash
az role definition list \
  --custom-role-only true \
  --query "[?contains(roleName, 'FSI')].{Name:roleName, Type:roleType, Assignable:assignableScopes[0]}" \
  --output table
```

### Check Role Assignments

```bash
# For a specific group
az role assignment list \
  --assignee "<GROUP-OBJECT-ID>" \
  --output table

# For a specific scope
az role assignment list \
  --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID" \
  --query "[?contains(roleDefinitionName, 'FSI')]" \
  --output table
```

### Test Service Principal Permissions

```bash
# Login as service principal
az login --service-principal \
  --username "<APP-ID>" \
  --password "<CLIENT-SECRET>" \
  --tenant "<TENANT-ID>"

# Verify permissions (should succeed)
az group list --output table
az network vnet list --output table

# Logout
az logout
```

## Maintenance

### Update Custom Role

If you need to modify a custom role:

1. Edit the JSON file with new permissions
2. Get the role definition ID:
   ```bash
   az role definition list \
     --name "FSI Landing Zone Deployer" \
     --query "[0].name" \
     --output tsv
   ```
3. Update the role:
   ```bash
   az role definition update --role-definition fsi-landingzone-deployer.json
   ```

### Delete Custom Role

```bash
az role definition delete --name "FSI Landing Zone Deployer"
```

**Warning:** Deleting a custom role will remove all role assignments using that role.

## Best Practices

1. **Scope Appropriately**
   - Use subscription scope only when necessary
   - Prefer resource group scope for team-specific roles
   - Use resource scope for highly sensitive resources (Key Vault)

2. **Regular Audits**
   - Review role assignments quarterly
   - Remove unused role assignments
   - Document changes to custom role definitions

3. **Version Control**
   - Track changes to JSON files in Git
   - Use meaningful commit messages
   - Tag versions for production deployments

4. **Testing**
   - Test new role definitions in non-production subscription first
   - Validate with actual service principals/users before production
   - Use Azure Policy to audit role assignments

5. **Documentation**
   - Document why specific permissions are required
   - Maintain a mapping of roles to teams
   - Update this README when adding/modifying roles

## Troubleshooting

### Error: "Insufficient privileges"

**Solution:** Ensure you have `User Access Administrator` or `Owner` role to create custom roles.

### Error: "Role definition already exists"

**Solution:** Use `az role definition update` instead of `create`, or delete the existing role first.

### Error: "InvalidRoleDefinition"

**Solution:** Check JSON syntax, ensure all `AssignableScopes` are valid subscription/RG paths.

### Role assignment not taking effect

**Solution:** Wait 5-10 minutes for role propagation in Azure AD. Logout and login to refresh tokens.

## References

- [Azure Built-in Roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)
- [Azure Custom Roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/custom-roles)
- [Resource Provider Operations](https://learn.microsoft.com/en-us/azure/role-based-access-control/resource-provider-operations)
- [RBAC Best Practices](https://learn.microsoft.com/en-us/azure/role-based-access-control/best-practices)

## Support

For questions or issues:
1. Check the main specification: [../rbac-specification.md](../rbac-specification.md)
2. Review Azure FSI Landing Zone documentation: [../../README.md](../../README.md)
3. Open an issue in the repository

---

**Version:** 1.0
**Last Updated:** 2025-10-22
