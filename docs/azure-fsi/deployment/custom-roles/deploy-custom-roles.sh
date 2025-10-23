#!/bin/bash
# deploy-custom-roles.sh
# Deploy all custom RBAC roles for Azure FSI Landing Zone

set -e

# Configuration
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Azure FSI Landing Zone${NC}"
echo -e "${GREEN}Custom RBAC Roles Deployment${NC}"
echo -e "${GREEN}======================================${NC}\n"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}ERROR: Azure CLI not found. Please install: https://aka.ms/azure-cli${NC}"
    exit 1
fi

# Check authentication
echo -e "${YELLOW}Checking Azure authentication...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}ERROR: Not authenticated to Azure. Run: az login${NC}"
    exit 1
fi

# Get subscription ID if not set
if [ -z "$SUBSCRIPTION_ID" ]; then
    SUBSCRIPTION_ID=$(az account show --query id --output tsv)
    echo -e "${YELLOW}Using subscription: $SUBSCRIPTION_ID${NC}"
fi

# Update JSON files with subscription ID
echo -e "\n${YELLOW}Updating JSON files with subscription ID...${NC}"
for json_file in "$SCRIPT_DIR"/*.json; do
    if [ -f "$json_file" ]; then
        sed -i "s|<SUBSCRIPTION-ID>|$SUBSCRIPTION_ID|g" "$json_file"
        echo -e "  ${GREEN}✓${NC} Updated $(basename "$json_file")"
    fi
done

# Define custom roles
declare -a ROLE_FILES=(
    "fsi-landingzone-deployer.json"
    "fsi-network-manager.json"
    "fsi-security-operator.json"
    "fsi-keyvault-operator.json"
    "fsi-devops-deployer.json"
    "fsi-compliance-auditor.json"
)

# Deploy each custom role
echo -e "\n${YELLOW}Deploying custom roles...${NC}"
SUCCESS_COUNT=0
FAIL_COUNT=0

for role_file in "${ROLE_FILES[@]}"; do
    role_path="$SCRIPT_DIR/$role_file"
    role_name=$(jq -r '.Name' "$role_path")

    echo -e "\n${YELLOW}Deploying: $role_name${NC}"

    # Check if role already exists
    existing_role=$(az role definition list \
        --name "$role_name" \
        --custom-role-only true \
        --query "[0].name" \
        --output tsv 2>/dev/null || echo "")

    if [ -n "$existing_role" ]; then
        echo -e "  ${YELLOW}⚠${NC}  Role already exists. Updating..."
        if az role definition update --role-definition "$role_path" &> /dev/null; then
            echo -e "  ${GREEN}✓${NC} Successfully updated: $role_name"
            ((SUCCESS_COUNT++))
        else
            echo -e "  ${RED}✗${NC} Failed to update: $role_name"
            ((FAIL_COUNT++))
        fi
    else
        echo -e "  ${YELLOW}→${NC} Creating new role..."
        if az role definition create --role-definition "$role_path" &> /dev/null; then
            echo -e "  ${GREEN}✓${NC} Successfully created: $role_name"
            ((SUCCESS_COUNT++))
        else
            echo -e "  ${RED}✗${NC} Failed to create: $role_name"
            ((FAIL_COUNT++))
        fi
    fi
done

# Summary
echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "Successfully deployed: ${GREEN}$SUCCESS_COUNT${NC}"
echo -e "Failed: ${RED}$FAIL_COUNT${NC}"
echo -e ""

# List custom roles
echo -e "${YELLOW}Custom roles in subscription:${NC}"
az role definition list \
    --custom-role-only true \
    --query "[?contains(roleName, 'FSI')].{Name:roleName, Type:roleType}" \
    --output table

# Restore original JSON files (remove subscription ID)
echo -e "\n${YELLOW}Restoring JSON files (removing subscription ID)...${NC}"
for json_file in "$SCRIPT_DIR"/*.json; do
    if [ -f "$json_file" ]; then
        sed -i "s|$SUBSCRIPTION_ID|<SUBSCRIPTION-ID>|g" "$json_file"
    fi
done

echo -e "\n${GREEN}Done!${NC}"

if [ $FAIL_COUNT -eq 0 ]; then
    exit 0
else
    echo -e "${RED}Some roles failed to deploy. Please check errors above.${NC}"
    exit 1
fi
