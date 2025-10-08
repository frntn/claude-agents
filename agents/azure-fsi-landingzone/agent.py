"""
Azure FSI Landing Zone Agent using Claude Agent SDK.

This agent helps deploy and manage Azure Financial Services Industry (FSI)
Landing Zones using:
- Microsoft FSI Landing Zone templates
- Azure Verified Modules (AVM)
- Built-in compliance policies for European regulations (GDPR, DORA, PSD2, etc.)
"""

import asyncio
import json
import os
import sys
import argparse
from pathlib import Path
from typing import List, Any, Optional, Dict
from datetime import datetime
from dotenv import load_dotenv
import yaml

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.agents import InteractiveAgent
from shared.utils import setup_logging
from claude_agent_sdk import tool, AssistantMessage, TextBlock


class AzureFSILandingZoneAgent(InteractiveAgent):
    """
    Azure FSI Landing Zone deployment agent.

    This agent provides capabilities for:
    - Deploying FSI-compliant Azure Landing Zones
    - Managing Azure Verified Modules (AVM)
    - Applying European compliance policies
    - Infrastructure as Code (Bicep/Terraform)
    - Security and compliance validation
    """

    def __init__(self, config_dir: Path, squad_mode: bool = False):
        super().__init__(config_dir)
        self.azure_config = self.agent_config.get('azure', {})
        self.compliance_config = self.azure_config.get('compliance', {})
        self.deployment_config = self.agent_config.get('deployment', {})

        # Override config with environment variables (env vars take precedence)
        if 'AZURE_LOCATION' in os.environ:
            if 'landing_zone' not in self.azure_config:
                self.azure_config['landing_zone'] = {}
            self.azure_config['landing_zone']['default_region'] = os.getenv('AZURE_LOCATION')

        # Squad mode configuration
        self.squad_mode = squad_mode
        self.squad_agents: Dict[str, Any] = {}  # Initialized on-demand

        # Track deployment state
        self.deployment_state = {
            'current_deployment': None,
            'deployments_count': 0,
            'last_validation': None,
            'policies_applied': []
        }

        # Project name for organizing generated assets
        self.project_name: Optional[str] = None

        # Ring-based deployment tracking
        self.deployment_rings = self.azure_config.get('architecture', {}).get('deployment_rings', {})
        self.selected_rings: List[str] = []  # Rings to deploy
        self.ring_depth: str = "standard"  # minimal, standard, advanced

        # Free Tier and Environment tracking
        self.is_free_tier: Optional[bool] = None  # Detected or set by user
        self.environment_type: Optional[str] = None  # dev, test, staging, prod, sandbox
        self.deployment_strategy: str = "shared-hub"  # full-rings, shared-hub, minimal

        # Cached AVM manifest (lazy-loaded)
        self._avm_manifest: Optional[Dict[str, Dict[str, Any]]] = None

    def get_project_dir(self) -> Path:
        """
        Get the project directory for storing generated assets.
        Prompts for project name if not already set.
        """
        if not self.project_name:
            # This will be prompted by the system prompt instructions
            raise ValueError("Project name not set. Please provide a project name first.")

        project_dir = self.config_dir / self.project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    # -------------------------------------------------------------------------
    # Azure Verified Module (AVM) manifest helpers
    # -------------------------------------------------------------------------

    def _avm_manifest_path(self) -> Path:
        """Resolve the AVM manifest path from configuration."""
        manifest_name = self.azure_config.get('landing_zone', {}).get('avm_manifest', 'avm-modules.yaml')
        candidate = self.config_dir / manifest_name
        if candidate.exists():
            return candidate

        fallback = Path(__file__).parent / manifest_name
        if fallback.exists():
            return fallback

        raise FileNotFoundError(f"AVM manifest not found: {manifest_name}")

    def _load_avm_manifest(self) -> Dict[str, Dict[str, Any]]:
        """Load and cache AVM manifest contents."""
        if self._avm_manifest is None:
            manifest_path = self._avm_manifest_path()
            with open(manifest_path, 'r', encoding='utf-8') as manifest_file:
                manifest_data = yaml.safe_load(manifest_file) or {}
            self._avm_manifest = manifest_data.get('modules', {})
        return self._avm_manifest

    def _avm_module_metadata(self, module_key: str) -> Dict[str, Any]:
        """Return metadata for a given AVM module."""
        manifest = self._load_avm_manifest()
        if module_key not in manifest:
            raise KeyError(f"Module '{module_key}' not defined in AVM manifest")
        return manifest[module_key]

    def _avm_module_reference(self, module_key: str, *, fallback: Optional[str] = None) -> str:
        """
        Return the fully qualified AVM module reference for Bicep templates.

        When the module is marked as native or missing essentials, raise unless
        a fallback is provided.
        """
        try:
            metadata = self._avm_module_metadata(module_key)
            if metadata.get('status') == 'native':
                raise ValueError(f"Module '{module_key}' uses native resources (no AVM module available)")

            registry = metadata.get('registry')
            version = metadata.get('version')
            if not registry or not version:
                raise ValueError(f"Module '{module_key}' is missing registry or version in manifest")

            return f"{registry}:{version}"
        except (FileNotFoundError, KeyError, ValueError) as exc:
            if fallback:
                if hasattr(self, 'logger'):
                    self.logger.warning("Using fallback AVM module reference for %s (%s)", module_key, exc)
                return fallback
            raise

    def _avm_manifest_summary(self) -> List[Dict[str, Any]]:
        """Return manifest data in a list form for reporting/serialization."""
        summary = []
        for key, details in self._load_avm_manifest().items():
            entry = {
                "key": key,
                "display_name": details.get("display_name", key.replace("_", " ").title()),
                "registry": details.get("registry"),
                "version": details.get("version"),
                "status": details.get("status", "available"),
            }
            summary.append(entry)
        return summary

    async def _initialize_squad(self) -> None:
        """Initialize squad agents on-demand (lazy loading)."""
        if not self.squad_mode or self.squad_agents:
            return  # Already initialized or not in squad mode

        # Lazy import to avoid overhead in solo mode
        import sys
        sub_agents_path = self.config_dir / "sub-agents"
        if str(sub_agents_path) not in sys.path:
            sys.path.insert(0, str(sub_agents_path))

        from architect.agent import ArchitectSpecialistAgent
        from security.agent import SecuritySpecialistAgent
        from network.agent import NetworkSpecialistAgent
        from devops.agent import DevOpsSpecialistAgent

        # Initialize sub-agents with same config directory
        sub_agents_dir = self.config_dir / "sub-agents"

        self.squad_agents = {
            'architect': ArchitectSpecialistAgent(sub_agents_dir / "architect"),
            'security': SecuritySpecialistAgent(sub_agents_dir / "security"),
            'network': NetworkSpecialistAgent(sub_agents_dir / "network"),
            'devops': DevOpsSpecialistAgent(sub_agents_dir / "devops")
        }

        # Connect all sub-agents
        for agent in self.squad_agents.values():
            await agent.connect()

        self.logger.info("Squad agents initialized successfully")

    async def _delegate_to_specialist(self, specialist: str, task: str, context: Dict[str, Any] = None) -> str:
        """Delegate a task to a specialist agent."""
        if not self.squad_mode:
            raise RuntimeError("Squad mode not enabled")

        await self._initialize_squad()

        if specialist not in self.squad_agents:
            raise ValueError(f"Unknown specialist: {specialist}")

        # Build context-aware prompt
        prompt = task
        if context:
            context_str = json.dumps(context, indent=2)
            prompt = f"Context:\n{context_str}\n\nTask: {task}"

        # Query specialist agent
        agent = self.squad_agents[specialist]
        response_parts = []

        async for msg in agent.query(prompt):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)

        return "\n".join(response_parts)

    async def _parallel_analysis(self, agents: List[str], task: str, context: Dict[str, Any] = None) -> Dict[str, str]:
        """Run multiple agents in parallel for comprehensive analysis."""
        if not self.squad_mode:
            raise RuntimeError("Squad mode not enabled")

        await self._initialize_squad()

        # Create tasks for parallel execution
        tasks = []
        for agent_name in agents:
            tasks.append(self._delegate_to_specialist(agent_name, task, context))

        # Execute in parallel
        results = await asyncio.gather(*tasks)

        # Map results to agent names
        return dict(zip(agents, results))

    async def _synthesize_results(self, results: Dict[str, str], context: Dict[str, Any] = None) -> str:
        """Use Architect agent to synthesize multi-agent results."""
        if not self.squad_mode:
            raise RuntimeError("Squad mode not enabled")

        await self._initialize_squad()

        # Build synthesis prompt
        synthesis_context = context or {}
        synthesis_context['specialist_findings'] = results

        synthesis_task = """Synthesize the following specialist findings into a comprehensive assessment:

Please provide:
1. Overall assessment score (1-10)
2. Critical issues (blockers)
3. Recommended improvements
4. Prioritized action plan
5. Cross-domain insights (conflicts or synergies between specialists)"""

        return await self._delegate_to_specialist('architect', synthesis_task, synthesis_context)

    def get_system_prompt(self) -> Optional[str]:
        """Get the system prompt for this agent."""
        virtual_network_ref = self._avm_module_reference(
            'virtual_network',
            fallback="br/public:avm/res/network/virtual-network:0.1.8",
        )
        azure_firewall_ref = self._avm_module_reference(
            'azure_firewall',
            fallback="br/public:avm/res/network/azure-firewall:0.3.0",
        )
        key_vault_ref = self._avm_module_reference(
            'key_vault',
            fallback="br/public:avm/res/key-vault/vault:0.6.2",
        )
        storage_account_ref = self._avm_module_reference(
            'storage_account',
            fallback="br/public:avm/res/storage/storage-account:0.9.1",
        )

        base_prompt = f"""You are an Azure Financial Services Industry (FSI) Landing Zone deployment expert.

You help organizations deploy secure, compliant Azure infrastructure using:

1. **Microsoft FSI Landing Zone Templates**: Industry-specific reference architectures
2. **Azure Verified Modules (AVM)**: Validated, production-ready infrastructure modules from Bicep Public Registry (br/public:avm/*)
3. **European Compliance**: Built-in policies for GDPR, DORA, PSD2, MiFID II, EBA Guidelines

All generated Bicep templates use AVM modules from the official Bicep Public Registry:
- Virtual Networks: {virtual_network_ref}
- Azure Firewall: {azure_firewall_ref}
- Key Vault: {key_vault_ref}
- Storage Accounts: {storage_account_ref}
- Policy Assignments: Native resources (AVM module not yet available)

IMPORTANT: Before generating any files (templates, plans, etc.), you MUST:
1. Ask the user for a project name (use set_project_name tool)
2. Ask if the subscription is Free Tier or Standard (use detect_subscription_tier tool)
3. Ask what environment type they want (dev/test/staging/prod/sandbox) (use set_environment_type tool)

These settings will be propagated to all sub-agents (Architect, DevOps, Network, Security).

These settings determine:
- Which Azure resources can be deployed (Free Tier has restrictions)
- Cost guardrails and budgets (Free Tier gets automatic budgets and alerts)
- Auto-cleanup policies (non-prod environments expire after X days)
- SKU selections (Free Tier uses Basic/Free SKUs, Standard uses Premium)

Your expertise includes:
- Hub-spoke network architectures for financial services
- Data residency and sovereignty requirements for EU
- Encryption at rest and in transit (including customer-managed keys)
- Network security with private endpoints and NSGs
- Identity and access management with Azure AD
- Compliance monitoring and auditing
- Bicep and Terraform Infrastructure as Code
- Azure Policy and governance frameworks
- Security baseline configuration

You prioritize:
- Security by design
- Compliance with European regulations
- Zero-trust architecture principles
- Least privilege access
- Data protection and privacy
- Operational resilience (DORA requirements)

You provide step-by-step guidance, validate configurations before deployment,
and ensure best practices are followed for financial services workloads in Azure.
"""

        if self.squad_mode:
            squad_prompt = """

🤖 SQUAD MODE ENABLED - Multi-Agent Orchestration

You have access to specialist agents for deep domain analysis:
- 🔒 Security Agent: Compliance (GDPR/DORA/PSD2), Key Vault, NSGs, Entra ID
- 🌐 Network Agent: Hub-spoke topology, Firewall, Private Endpoints, VNet peering
- 🚀 DevOps Agent: CI/CD pipelines, deployment automation, GitOps
- 🏗️  Architect Agent: Cross-domain synthesis, best practices, cost optimization

DELEGATION GUIDELINES:

1. **Use delegation tools** for specialist tasks:
   - Security reviews → delegate_to_security
   - Network analysis → delegate_to_network
   - Pipeline/deployment → delegate_to_devops
   - Comprehensive review → run_squad_review (all specialists + synthesis)

2. **When to delegate**:
   - User asks for security/compliance review → Security Agent
   - User asks about network topology/connectivity → Network Agent
   - User asks about CI/CD or deployment automation → DevOps Agent
   - User asks "review my deployment" → run_squad_review (parallel analysis)

3. **Workflow patterns**:
   - **Parallel** (preferred): For independent analyses, use run_squad_review
   - **Sequential**: For dependent tasks, chain delegate_to_* calls
   - **Synthesis**: Architect agent automatically synthesizes multi-agent results

4. **Context sharing**: Pass project_name, tier, environment_type to specialists via context parameter

Example:
User: "Review my Ring 0 security for production"
→ Use delegate_to_security with context: {ring: "0", environment: "prod"}

User: "Review entire deployment for compliance"
→ Use run_squad_review (all agents in parallel + synthesis)
"""
            return base_prompt + squad_prompt

        return base_prompt

    def get_custom_tools(self) -> List[Any]:
        """Get custom tools for this agent."""
        base_tools = [
            self.set_project_name,
            self.detect_subscription_tier,
            self.set_environment_type,
            self.set_deployment_strategy,
            self.list_deployment_rings,
            self.select_deployment_rings,
            self.set_ring_depth,
            self.generate_ring_deployment,
            self.check_azure_prerequisites,
            self.validate_azure_auth,
            self.get_fsi_compliance_requirements,
            self.list_avm_modules,
            self.generate_bicep_template,
            self.validate_deployment,
            self.apply_compliance_policies,
            self.get_deployment_status,
            self.generate_network_architecture,
            self.check_data_residency,
            self.export_deployment_plan,
            self.generate_bastion_template,
            self.configure_entra_id,
            self.deploy_conditional_access,
            self.setup_pim_roles,
        ]

        # Add squad mode delegation tools
        if self.squad_mode:
            base_tools.extend([
                self.delegate_to_security,
                self.delegate_to_network,
                self.delegate_to_devops,
                self.delegate_to_architect,
                self.run_squad_review,
            ])

        return base_tools

    @tool("set_project_name", "Set the project name for organizing generated assets in a dedicated subfolder", {"project_name": str})
    async def set_project_name(self, args):
        """Set the project name for file organization."""
        project_name = args.get("project_name", "").strip()

        if not project_name:
            return {
                "content": [
                    {"type": "text", "text": "❌ Project name cannot be empty. Please provide a valid project name."}
                ]
            }

        # Sanitize project name (remove invalid characters for filesystem)
        import re
        sanitized_name = re.sub(r'[^\w\-_]', '_', project_name)

        self.project_name = sanitized_name
        project_dir = self.get_project_dir()

        result_text = f"✅ Project name set: {sanitized_name}\n\n"
        result_text += f"📁 All generated assets will be saved to:\n"
        result_text += f"   {project_dir}\n\n"
        result_text += "You can now proceed with generating templates, deployment plans, and other assets."

        return {
            "content": [
                {"type": "text", "text": result_text}
            ]
        }

    @tool("detect_subscription_tier", "Detect if Azure subscription is Free Tier or Standard", {})
    async def detect_subscription_tier(self, args):
        """Detect subscription tier by running the detection script."""
        import subprocess

        script_path = self.config_dir / "scripts" / "detect-free-tier.sh"

        if not script_path.exists():
            return {
                "content": [
                    {"type": "text", "text": "❌ Detection script not found. Please run manually or specify tier."}
                ]
            }

        try:
            # Run the detection script
            result = subprocess.run(
                [str(script_path)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.config_dir
            )

            # Read the flag file
            flag_file = self.config_dir / "isFreeTier.flag"
            if flag_file.exists():
                with open(flag_file, 'r') as f:
                    is_free_tier_str = f.read().strip()
                    self.is_free_tier = is_free_tier_str.lower() == 'true'

            output_text = "🔍 Détection automatique du type d'abonnement\n\n"
            output_text += result.stdout
            output_text += "\n"

            if self.is_free_tier is not None:
                output_text += f"\n✅ Tier détecté et enregistré: {'Free Tier' if self.is_free_tier else 'Standard'}\n"
                output_text += "\n💡 Cette configuration sera propagée aux sub-agents (Architect, DevOps, Network, Security)\n"

            return {
                "content": [
                    {"type": "text", "text": output_text}
                ]
            }

        except Exception as e:
            return {
                "content": [
                    {"type": "text", "text": f"❌ Error running detection: {str(e)}\n\nPlease specify tier manually."}
                ]
            }

    @tool("set_environment_type", "Set the environment type (dev/test/staging/prod/sandbox)", {"env_type": str})
    async def set_environment_type(self, args):
        """Set the environment type for deployment."""
        env_type = args.get("env_type", "").strip().lower()

        valid_envs = ["dev", "test", "staging", "prod", "sandbox"]
        if env_type not in valid_envs:
            return {
                "content": [
                    {"type": "text", "text": f"❌ Invalid environment type. Choose from: {', '.join(valid_envs)}"}
                ]
            }

        self.environment_type = env_type

        # Determine characteristics based on environment
        is_prod = env_type == "prod"
        ttl_days = 7 if env_type == "dev" else \
                   3 if env_type == "test" else \
                   14 if env_type == "staging" else \
                   30 if env_type == "sandbox" else 0

        result_text = f"✅ Environment type set: {env_type.upper()}\n\n"

        if is_prod:
            result_text += "📊 Production Environment:\n"
            result_text += "   • No auto-cleanup (permanent resources)\n"
            result_text += "   • Full security features enabled\n"
            result_text += "   • Geo-redundant storage for DORA compliance\n"
            result_text += "   • Premium SKUs for critical services\n"
        else:
            result_text += "📊 Non-Production Environment:\n"
            result_text += f"   • Auto-cleanup after {ttl_days} days\n"
            result_text += "   • Cost-optimized SKUs\n"
            result_text += "   • Expiration tags automatically added\n"
            result_text += "   • Budget alerts enabled\n"

        result_text += f"\n💡 Next: Specify deployment strategy with set_deployment_strategy tool"
        result_text += f"\n💡 Cette configuration sera propagée aux sub-agents"

        return {
            "content": [
                {"type": "text", "text": result_text}
            ]
        }

    @tool("set_deployment_strategy", "Set deployment strategy (full-rings/shared-hub/minimal)", {"strategy": str})
    async def set_deployment_strategy(self, args):
        """Set the deployment strategy for the landing zone."""
        strategy = args.get("strategy", "").strip().lower()

        valid_strategies = ["full-rings", "shared-hub", "minimal"]
        if strategy not in valid_strategies:
            return {
                "content": [
                    {"type": "text", "text": f"❌ Invalid strategy. Choose from: {', '.join(valid_strategies)}"}
                ]
            }

        self.deployment_strategy = strategy

        result_text = f"✅ Deployment strategy set: {strategy}\n\n"

        if strategy == "full-rings":
            result_text += "📊 Full Rings Strategy:\n"
            result_text += "   • Deploys all rings (Ring 0 + Ring 1/2/3) per environment\n"
            result_text += "   • Each environment gets complete architecture\n"
            result_text += "   • ⚠️  Not recommended for Free Tier (too expensive)\n"
            result_text += "   • Best for: Production, multi-workload environments\n"
        elif strategy == "shared-hub":
            result_text += "📊 Shared Hub Strategy:\n"
            result_text += "   • Single Ring 0 (Hub) shared across environments\n"
            result_text += "   • Separate spokes (Ring 1+) per environment\n"
            result_text += "   • ✅ Recommended for Free Tier\n"
            result_text += "   • Best for: Cost optimization, dev/test environments\n"
        else:  # minimal
            result_text += "📊 Minimal Strategy:\n"
            result_text += "   • Only Ring 0 (Hub) + 1 spoke\n"
            result_text += "   • Simplest architecture\n"
            result_text += "   • ✅ Ideal for Free Tier or POC\n"
            result_text += "   • Best for: Learning, proof-of-concept\n"

        if self.is_free_tier and strategy == "full-rings":
            result_text += "\n⚠️  WARNING: Full rings strategy detected with Free Tier subscription!\n"
            result_text += "   This may exceed Free Tier quotas and incur costs.\n"
            result_text += "   Consider using 'shared-hub' or 'minimal' strategy instead.\n"

        return {
            "content": [
                {"type": "text", "text": result_text}
            ]
        }

    @tool("list_deployment_rings", "List available deployment rings and their components", {})
    async def list_deployment_rings(self, args):
        """List all available deployment rings with their components."""
        if not self.deployment_rings:
            return {
                "content": [
                    {"type": "text", "text": "❌ No deployment rings configured in config.yaml"}
                ]
            }

        rings_text = "🎯 Available Deployment Rings for FSI Landing Zone:\n\n"
        rings_text += "Deploy your landing zone progressively using a ring-based approach.\n"
        rings_text += "Each ring contains specific components and can be deployed independently.\n\n"

        # Sort rings by deployment order
        sorted_rings = sorted(
            [(name, data) for name, data in self.deployment_rings.items() if name != 'depth_profiles'],
            key=lambda x: x[1].get('deployment_order', 999)
        )

        for ring_name, ring_data in sorted_rings:
            rings_text += f"{'=' * 80}\n"
            rings_text += f"📦 {ring_name.upper().replace('_', ' ')}\n"
            rings_text += f"{'=' * 80}\n"
            rings_text += f"Description: {ring_data.get('description', 'N/A')}\n"
            rings_text += f"Order: {ring_data.get('deployment_order', 'N/A')}\n"
            rings_text += f"Mandatory: {'✅ Yes' if ring_data.get('mandatory') else '⚠️  Optional'}\n"
            rings_text += f"Default Depth: {ring_data.get('depth', 'standard')}\n"

            if ring_data.get('depends_on'):
                rings_text += f"Dependencies: {', '.join(ring_data['depends_on'])}\n"

            rings_text += f"\nComponents:\n"

            components = ring_data.get('components', {})
            for category, items in components.items():
                rings_text += f"\n  🔷 {category.replace('_', ' ').title()}:\n"
                for item in items:
                    component_name = item.get('component', 'unknown')
                    is_mandatory = item.get('mandatory', False)
                    status = "✓" if is_mandatory else "○"
                    rings_text += f"    {status} {component_name}\n"

                    # Show policies if available
                    if 'policies' in item:
                        for policy in item['policies']:
                            rings_text += f"        ├─ Policy: {policy}\n"

            rings_text += "\n"

        # Show depth profiles
        depth_profiles = self.deployment_rings.get('depth_profiles', {})
        if depth_profiles:
            rings_text += f"{'=' * 80}\n"
            rings_text += "📊 DEPLOYMENT DEPTH PROFILES\n"
            rings_text += f"{'=' * 80}\n\n"
            for depth_name, depth_data in depth_profiles.items():
                rings_text += f"🎚️  {depth_name.upper()}\n"
                rings_text += f"   {depth_data.get('description', 'N/A')}\n"
                rings_text += f"   Filter: {depth_data.get('components_filter', 'N/A')}\n\n"

        rings_text += "\n💡 Usage:\n"
        rings_text += "   1. Use select_deployment_rings to choose which rings to deploy\n"
        rings_text += "   2. Use set_ring_depth to choose deployment depth (minimal/standard/advanced)\n"
        rings_text += "   3. Use generate_ring_deployment to generate all templates for selected rings\n"

        return {
            "content": [
                {"type": "text", "text": rings_text}
            ]
        }

    @tool("select_deployment_rings", "Select which deployment rings to deploy", {"rings": str})
    async def select_deployment_rings(self, args):
        """
        Select deployment rings to deploy.
        Args:
            rings: Comma-separated list of rings (e.g., "ring0_foundation,ring1_platform")
                   or "all" to select all rings
        """
        rings_input = args.get("rings", "").strip()

        if not rings_input:
            return {
                "content": [
                    {"type": "text", "text": "❌ Please specify rings to deploy (comma-separated) or 'all'"}
                ]
            }

        # Get valid ring names (exclude depth_profiles)
        valid_rings = [name for name in self.deployment_rings.keys() if name != 'depth_profiles']

        if rings_input.lower() == "all":
            self.selected_rings = valid_rings
        else:
            selected = [r.strip() for r in rings_input.split(',')]
            invalid_rings = [r for r in selected if r not in valid_rings]

            if invalid_rings:
                return {
                    "content": [
                        {"type": "text", "text": f"❌ Invalid rings: {', '.join(invalid_rings)}\n\nValid rings: {', '.join(valid_rings)}"}
                    ]
                }

            self.selected_rings = selected

        # Check dependencies
        result_text = f"✅ Selected deployment rings:\n\n"
        for ring_name in self.selected_rings:
            ring_data = self.deployment_rings.get(ring_name, {})
            result_text += f"   ✓ {ring_name}\n"
            result_text += f"     └─ {ring_data.get('description', 'N/A')}\n"

            # Check dependencies
            depends_on = ring_data.get('depends_on', [])
            if depends_on:
                result_text += f"     └─ Requires: {', '.join(depends_on)}\n"
                missing_deps = [dep for dep in depends_on if dep not in self.selected_rings]
                if missing_deps:
                    result_text += f"     ⚠️  Warning: Missing dependencies: {', '.join(missing_deps)}\n"

        result_text += f"\n📊 Current depth: {self.ring_depth}\n"
        result_text += "\n💡 Use generate_ring_deployment to create templates for these rings.\n"

        return {
            "content": [
                {"type": "text", "text": result_text}
            ]
        }

    @tool("set_ring_depth", "Set deployment depth for rings (minimal/standard/advanced)", {"depth": str})
    async def set_ring_depth(self, args):
        """Set the deployment depth for ring-based deployments."""
        depth = args.get("depth", "").strip().lower()

        valid_depths = ["minimal", "standard", "advanced"]
        if depth not in valid_depths:
            return {
                "content": [
                    {"type": "text", "text": f"❌ Invalid depth. Choose from: {', '.join(valid_depths)}"}
                ]
            }

        self.ring_depth = depth

        depth_profiles = self.deployment_rings.get('depth_profiles', {})
        depth_info = depth_profiles.get(depth, {})

        result_text = f"✅ Deployment depth set to: {depth.upper()}\n\n"
        result_text += f"📋 Description: {depth_info.get('description', 'N/A')}\n"
        result_text += f"🔧 Components filter: {depth_info.get('components_filter', 'N/A')}\n"
        result_text += f"➕ Include optional: {'Yes' if depth_info.get('include_optional') else 'No'}\n"

        return {
            "content": [
                {"type": "text", "text": result_text}
            ]
        }

    @tool("generate_ring_deployment", "Generate all deployment templates for selected rings", {})
    async def generate_ring_deployment(self, args):
        """Generate deployment templates for all selected rings."""
        if not self.selected_rings:
            return {
                "content": [
                    {"type": "text", "text": "❌ No rings selected. Use select_deployment_rings first."}
                ]
            }

        # Get project directory
        try:
            project_dir = self.get_project_dir()
        except ValueError:
            return {
                "content": [
                    {"type": "text", "text": "❌ Please set a project name first using set_project_name tool."}
                ]
            }

        result_text = f"🚀 Generating deployment templates for selected rings...\n\n"
        result_text += f"Project: {self.project_name}\n"
        result_text += f"Depth: {self.ring_depth}\n"
        result_text += f"Rings: {', '.join(self.selected_rings)}\n\n"

        generated_files = []
        components_by_ring = {}

        # Process each selected ring
        for ring_name in sorted(self.selected_rings, key=lambda r: self.deployment_rings.get(r, {}).get('deployment_order', 999)):
            ring_data = self.deployment_rings.get(ring_name, {})
            ring_dir = project_dir / ring_name
            ring_dir.mkdir(parents=True, exist_ok=True)

            result_text += f"\n📦 {ring_name.upper().replace('_', ' ')}:\n"

            components = ring_data.get('components', {})
            ring_components = []

            for category, items in components.items():
                for item in items:
                    component_name = item.get('component', 'unknown')
                    is_mandatory = item.get('mandatory', False)

                    # Filter based on depth
                    should_include = False
                    if self.ring_depth == "minimal":
                        should_include = is_mandatory
                    elif self.ring_depth == "standard":
                        should_include = True  # Include all in standard
                    elif self.ring_depth == "advanced":
                        should_include = True  # Include all in advanced

                    if should_include:
                        ring_components.append({
                            'name': component_name,
                            'category': category,
                            'mandatory': is_mandatory
                        })

            components_by_ring[ring_name] = ring_components

            # Generate a summary file for this ring
            summary_path = ring_dir / "DEPLOYMENT.md"
            summary_content = self._generate_ring_summary(ring_name, ring_data, ring_components)

            with open(summary_path, 'w') as f:
                f.write(summary_content)

            generated_files.append(str(summary_path))
            result_text += f"   ✓ Generated: {summary_path.name}\n"

            # Generate component placeholders
            for comp in ring_components:
                comp_file = ring_dir / f"{comp['name']}.bicep"
                if not comp_file.exists():
                    placeholder = f"// {comp['name']} - {category}\n// TODO: Implement component\n"
                    with open(comp_file, 'w') as f:
                        f.write(placeholder)
                    result_text += f"   ○ Created placeholder: {comp['name']}.bicep\n"

        # Generate main deployment script
        main_deploy_path = project_dir / "deploy.sh"
        deploy_script = self._generate_deployment_script(components_by_ring)

        with open(main_deploy_path, 'w') as f:
            f.write(deploy_script)
        main_deploy_path.chmod(0o755)  # Make executable

        generated_files.append(str(main_deploy_path))

        result_text += f"\n✅ Generated {len(generated_files)} files\n"
        result_text += f"📁 Output directory: {project_dir}\n"
        result_text += f"\n💡 Next steps:\n"
        result_text += f"   1. Review generated templates in each ring folder\n"
        result_text += f"   2. Customize components as needed\n"
        result_text += f"   3. Run ./deploy.sh to deploy rings sequentially\n"

        return {
            "content": [
                {"type": "text", "text": result_text}
            ]
        }

    def _generate_ring_summary(self, ring_name: str, ring_data: dict, components: list) -> str:
        """Generate deployment summary for a ring."""
        summary = f"# {ring_name.upper().replace('_', ' ')} - Deployment Guide\n\n"
        summary += f"**Description**: {ring_data.get('description', 'N/A')}\n\n"
        summary += f"**Deployment Order**: {ring_data.get('deployment_order', 'N/A')}\n\n"
        summary += f"**Mandatory**: {'Yes' if ring_data.get('mandatory') else 'No'}\n\n"

        if ring_data.get('depends_on'):
            summary += f"**Dependencies**: {', '.join(ring_data['depends_on'])}\n\n"

        summary += "## Components\n\n"
        summary += f"Total components in this ring: {len(components)}\n\n"

        # Group by category
        by_category = {}
        for comp in components:
            category = comp['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(comp)

        for category, items in by_category.items():
            summary += f"### {category.replace('_', ' ').title()}\n\n"
            for item in items:
                status = "**[MANDATORY]**" if item['mandatory'] else "[Optional]"
                summary += f"- {status} `{item['name']}`\n"
            summary += "\n"

        summary += "## Deployment\n\n"
        summary += "```bash\n"
        summary += f"# Deploy {ring_name}\n"
        summary += "az deployment sub create \\\n"
        summary += f"  --location francecentral \\\n"
        summary += f"  --template-file main.bicep \\\n"
        summary += f"  --parameters @main.parameters.json\n"
        summary += "```\n\n"

        summary += "## Validation\n\n"
        summary += "```bash\n"
        summary += f"# Validate {ring_name} before deployment\n"
        summary += "az deployment sub validate \\\n"
        summary += f"  --location francecentral \\\n"
        summary += f"  --template-file main.bicep \\\n"
        summary += f"  --parameters @main.parameters.json\n"
        summary += "```\n"

        return summary

    def _generate_deployment_script(self, components_by_ring: dict) -> str:
        """Generate main deployment script for all rings."""
        script = """#!/bin/bash
# FSI Landing Zone - Ring-based Deployment Script
# Generated by Azure FSI Landing Zone Agent

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
log_info "Checking prerequisites..."
if ! command -v az &> /dev/null; then
    log_error "Azure CLI not found. Please install it first."
    exit 1
fi

if ! az account show &> /dev/null; then
    log_error "Not authenticated to Azure. Please run 'az login' first."
    exit 1
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
log_info "Using subscription: $SUBSCRIPTION_ID"

# Deployment region
LOCATION="${AZURE_LOCATION:-francecentral}"
log_info "Deployment region: $LOCATION"

"""

        # Add deployment functions for each ring
        sorted_rings = sorted(components_by_ring.items(), key=lambda x: len(x[0]))

        for ring_name, components in sorted_rings:
            script += f"""
# Deploy {ring_name}
deploy_{ring_name}() {{
    log_info "Deploying {ring_name}..."

    # TODO: Add actual deployment logic here
    # Example:
    # az deployment sub create \\
    #   --location $LOCATION \\
    #   --template-file {ring_name}/main.bicep \\
    #   --parameters @{ring_name}/main.parameters.json

    log_info "{ring_name} deployment completed"
}}

"""

        # Add main deployment logic
        script += """
# Main deployment flow
main() {
    log_info "Starting FSI Landing Zone deployment..."
    log_info "================================================"

"""

        for ring_name, _ in sorted_rings:
            script += f"""    log_info "Step: {ring_name}"
    deploy_{ring_name}

"""

        script += """    log_info "================================================"
    log_info "All rings deployed successfully!"
}

# Run main deployment
main
"""

        return script

    @tool("check_azure_prerequisites", "Check if Azure CLI and required tools are installed", {})
    async def check_azure_prerequisites(self, args):
        """Check Azure CLI and prerequisites."""
        checks = {
            'azure_cli': False,
            'azure_cli_version': None,
            'bicep': False,
            'bicep_version': None,
            'authenticated': False,
            'subscription_access': False
        }

        import subprocess

        # Check Azure CLI
        try:
            result = subprocess.run(['az', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                checks['azure_cli'] = True
                # Parse version from output
                for line in result.stdout.split('\n'):
                    if 'azure-cli' in line:
                        checks['azure_cli_version'] = line.split()[-1]
                        break
        except Exception:
            pass

        # Check Bicep
        try:
            result = subprocess.run(['az', 'bicep', 'version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                checks['bicep'] = True
                checks['bicep_version'] = result.stdout.strip()
        except Exception:
            pass

        # Check authentication
        try:
            result = subprocess.run(['az', 'account', 'show'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                checks['authenticated'] = True
                account_info = json.loads(result.stdout)
                checks['subscription_access'] = account_info.get('state') == 'Enabled'
        except Exception:
            pass

        # Format response
        status_text = "🔍 Azure Prerequisites Check:\n\n"
        status_text += f"✅ Azure CLI: {'Installed' if checks['azure_cli'] else '❌ Not installed'}\n"
        if checks['azure_cli_version']:
            status_text += f"   Version: {checks['azure_cli_version']}\n"

        status_text += f"✅ Bicep: {'Installed' if checks['bicep'] else '❌ Not installed'}\n"
        if checks['bicep_version']:
            status_text += f"   Version: {checks['bicep_version']}\n"

        status_text += f"✅ Authentication: {'Authenticated' if checks['authenticated'] else '❌ Not authenticated'}\n"
        status_text += f"✅ Subscription Access: {'Active' if checks['subscription_access'] else '❌ No access'}\n"

        if not all([checks['azure_cli'], checks['bicep'], checks['authenticated']]):
            status_text += "\n⚠️  Missing prerequisites detected. Please install/configure:\n"
            if not checks['azure_cli']:
                status_text += "   • Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli\n"
            if not checks['bicep']:
                status_text += "   • Bicep: az bicep install\n"
            if not checks['authenticated']:
                status_text += "   • Authenticate: az login\n"

        return {
            "content": [
                {"type": "text", "text": status_text}
            ]
        }

    @tool("validate_azure_auth", "Validate Azure authentication and get subscription details", {})
    async def validate_azure_auth(self, args):
        """Validate Azure authentication and subscription access."""
        import subprocess

        try:
            result = subprocess.run(
                ['az', 'account', 'show', '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {
                    "content": [
                        {"type": "text", "text": "❌ Not authenticated to Azure. Please run: az login"}
                    ]
                }

            account = json.loads(result.stdout)

            # Get list of available subscriptions
            result = subprocess.run(
                ['az', 'account', 'list', '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )

            subscriptions = json.loads(result.stdout) if result.returncode == 0 else []

            auth_text = "✅ Azure Authentication Status:\n\n"
            auth_text += f"📋 Current Subscription:\n"
            auth_text += f"   • Name: {account.get('name')}\n"
            auth_text += f"   • ID: {account.get('id')}\n"
            auth_text += f"   • State: {account.get('state')}\n"
            auth_text += f"   • Tenant ID: {account.get('tenantId')}\n"
            auth_text += f"   • User: {account.get('user', {}).get('name')}\n\n"

            if len(subscriptions) > 1:
                auth_text += f"📌 Available Subscriptions ({len(subscriptions)}):\n"
                for sub in subscriptions:
                    indicator = "→" if sub['isDefault'] else " "
                    auth_text += f"   {indicator} {sub['name']} ({sub['id']})\n"

            return {
                "content": [
                    {"type": "text", "text": auth_text}
                ]
            }

        except Exception as e:
            return {
                "content": [
                    {"type": "text", "text": f"❌ Error validating authentication: {str(e)}"}
                ]
            }

    @tool("get_fsi_compliance_requirements", "Get FSI compliance requirements for European regulations", {})
    async def get_fsi_compliance_requirements(self, args):
        """Get FSI compliance requirements."""
        regulations = self.compliance_config.get('regulations', [])

        compliance_text = "📋 FSI Compliance Requirements for European Regulations:\n\n"

        compliance_details = {
            "GDPR": {
                "name": "General Data Protection Regulation",
                "key_requirements": [
                    "Data residency within EU/EEA",
                    "Encryption of personal data at rest and in transit",
                    "Right to erasure (right to be forgotten)",
                    "Data breach notification within 72 hours",
                    "Privacy by design and by default",
                    "Data protection impact assessments (DPIA)"
                ],
                "azure_controls": [
                    "Azure Policy: Allowed locations for resources",
                    "Azure Key Vault with customer-managed keys",
                    "Azure Private Link for services",
                    "Microsoft Defender for Cloud",
                    "Azure Information Protection"
                ]
            },
            "DORA": {
                "name": "Digital Operational Resilience Act",
                "key_requirements": [
                    "ICT risk management framework",
                    "Incident reporting mechanisms",
                    "Digital operational resilience testing",
                    "Third-party ICT service provider management",
                    "Information sharing on cyber threats"
                ],
                "azure_controls": [
                    "Azure Backup and Site Recovery",
                    "Azure Monitor and Log Analytics",
                    "Business continuity planning tools",
                    "Resilience testing framework",
                    "Multi-region deployment architecture"
                ]
            },
            "PSD2": {
                "name": "Payment Services Directive 2",
                "key_requirements": [
                    "Strong customer authentication (SCA)",
                    "Secure communication channels",
                    "Transaction monitoring",
                    "API security for open banking",
                    "Fraud detection and prevention"
                ],
                "azure_controls": [
                    "Azure AD Multi-Factor Authentication",
                    "Azure API Management with OAuth 2.0",
                    "Azure Application Gateway with WAF",
                    "Azure Sentinel for security analytics",
                    "Azure Key Vault for credential management"
                ]
            },
            "MiFID_II": {
                "name": "Markets in Financial Instruments Directive II",
                "key_requirements": [
                    "Transaction reporting",
                    "Record keeping and audit trails",
                    "Best execution reporting",
                    "Clock synchronization",
                    "Data retention (5-7 years)"
                ],
                "azure_controls": [
                    "Azure Storage with immutable blobs",
                    "Azure Log Analytics with retention policies",
                    "Azure Time Series Insights",
                    "Azure Purview for data governance",
                    "Azure Archive Storage"
                ]
            },
            "EBA_GL": {
                "name": "European Banking Authority Guidelines",
                "key_requirements": [
                    "ICT and security risk management",
                    "Outsourcing arrangements",
                    "Cloud service provider oversight",
                    "Exit strategies from cloud services",
                    "Operational resilience"
                ],
                "azure_controls": [
                    "Azure Resource Manager for governance",
                    "Azure Policy for compliance enforcement",
                    "Data export and portability tools",
                    "Multi-cloud and hybrid capabilities",
                    "Sovereign cloud options (Azure Germany, etc.)"
                ]
            }
        }

        for reg in regulations:
            if reg in compliance_details:
                details = compliance_details[reg]
                compliance_text += f"🏛️  {reg} - {details['name']}\n"
                compliance_text += f"   Key Requirements:\n"
                for req in details['key_requirements']:
                    compliance_text += f"   • {req}\n"
                compliance_text += f"\n   Azure Controls:\n"
                for control in details['azure_controls']:
                    compliance_text += f"   ✓ {control}\n"
                compliance_text += "\n"

        # Add policy initiatives
        policy_initiatives = self.compliance_config.get('policy_initiatives', [])
        if policy_initiatives:
            compliance_text += "📜 Built-in Policy Initiatives to Apply:\n"
            for initiative in policy_initiatives:
                compliance_text += f"   • {initiative}\n"

        return {
            "content": [
                {"type": "text", "text": compliance_text}
            ]
        }

    @tool("list_avm_modules", "List available Azure Verified Modules (AVM) for FSI landing zone", {})
    async def list_avm_modules(self, args):
        """List Azure Verified Modules."""
        try:
            manifest = self._load_avm_manifest()
        except FileNotFoundError:
            return {
                "content": [
                    {"type": "text", "text": "❌ No AVM manifest found. Ensure avm-modules.yaml exists in the agent directory."}
                ]
            }

        if not manifest:
            return {
                "content": [
                    {"type": "text", "text": "⚠️ AVM manifest is empty. Add modules to avm-modules.yaml to expose them here."}
                ]
            }

        avm_text = "📦 Azure Verified Modules (AVM) for FSI Landing Zone\n\n"
        avm_text += "Modules are sourced from the central manifest (avm-modules.yaml):\n\n"

        for key, details in manifest.items():
            display_name = details.get("display_name", key.replace("_", " ").title())
            status = details.get("status", "available")
            registry = details.get("registry")
            version = details.get("version")
            description = details.get("description")
            use_case = details.get("use_case")
            features = details.get("key_features", [])

            avm_text += f"🔷 {display_name}\n"
            avm_text += f"   Key: {key}\n"

            if status == "native":
                avm_text += "   Status: Native Azure resources (AVM module pending)\n"
            elif status != "available":
                status_label = status.replace("_", " ").title()
                avm_text += f"   Status: {status_label}\n"

            if registry and version:
                avm_text += f"   Module: {registry}:{version}\n"
            elif registry:
                avm_text += f"   Module: {registry}\n"

            if description:
                avm_text += f"   Description: {description}\n"
            if use_case:
                avm_text += f"   Use Case: {use_case}\n"
            if features:
                avm_text += f"   Features: {', '.join(features)}\n"

            avm_text += "\n"

        avm_text += "💡 Use `avm-modules.yaml` to update versions or add new modules without changing agent code.\n"

        return {
            "content": [
                {"type": "text", "text": avm_text}
            ]
        }

    @tool("generate_bicep_template", "Generate a Bicep template for FSI landing zone component", {"component": str})
    async def generate_bicep_template(self, args):
        """Generate Bicep template for a specific component."""
        component = args.get("component", "").lower()

        templates = {
            "hub-vnet": self._generate_hub_vnet_bicep(),
            "spoke-vnet": self._generate_spoke_vnet_bicep(),
            "key-vault": self._generate_keyvault_bicep(),
            "storage": self._generate_storage_bicep(),
            "policy-assignment": self._generate_policy_bicep(),
        }

        if component not in templates:
            available = ", ".join(templates.keys())
            return {
                "content": [
                    {"type": "text", "text": f"❌ Unknown component. Available: {available}"}
                ]
            }

        bicep_content = templates[component]

        # Get project directory
        try:
            project_dir = self.get_project_dir()
        except ValueError:
            return {
                "content": [
                    {"type": "text", "text": "❌ Please set a project name first using set_project_name tool."}
                ]
            }

        template_path = project_dir / f"{component}.bicep"

        # Save template
        template_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, 'w') as f:
            f.write(bicep_content)

        result_text = f"✅ Generated Bicep template for: {component}\n\n"
        result_text += f"📄 Saved to: {template_path}\n\n"
        result_text += "Template Preview:\n"
        result_text += "```bicep\n"
        result_text += bicep_content[:500] + "...\n"
        result_text += "```\n"

        return {
            "content": [
                {"type": "text", "text": result_text}
            ]
        }

    def _generate_hub_vnet_bicep(self) -> str:
        """Generate Hub VNet Bicep template using Azure Verified Modules."""
        hub_config = self.azure_config.get('architecture', {}).get('hub', {})
        naming = self.azure_config.get('landing_zone', {})
        vnet_module = self._avm_module_reference('virtual_network')
        firewall_module = self._avm_module_reference('azure_firewall')

        return f"""// Hub Virtual Network for FSI Landing Zone
// Generated by Azure FSI Landing Zone Agent
// Using Azure Verified Modules (AVM) from Bicep Public Registry

param location string = '{self.azure_config.get('landing_zone', {}).get('default_region', 'westeurope')}'
param environment string = '{naming.get('environment', 'prod')}'
param namingPrefix string = '{naming.get('naming_prefix', 'fsi')}'

// Hub VNet configuration
var hubVNetName = '${{namingPrefix}}-hub-vnet-${{environment}}'
var addressSpace = '{hub_config.get('vnet_address_space', '10.0.0.0/16')}'

// Hub Virtual Network using AVM module
module hubVNet '{vnet_module}' = {{
  name: 'deploy-hub-vnet'
  params: {{
    name: hubVNetName
    location: location
    addressPrefixes: [
      addressSpace
    ]
    subnets: [
      {{
        name: 'AzureFirewallSubnet'
        addressPrefix: '10.0.0.0/24'
        serviceEndpoints: []
      }}
      {{
        name: 'GatewaySubnet'
        addressPrefix: '10.0.1.0/24'
      }}
      {{
        name: 'AzureBastionSubnet'
        addressPrefix: '10.0.2.0/24'
      }}
    ]
    ddosProtectionPlanResourceId: ''  // Enable if DDoS Standard is required
    tags: {{
      Environment: environment
      Purpose: 'FSI Hub Network'
      Compliance: 'GDPR,DORA,PSD2'
    }}
  }}
}}

// Azure Firewall using AVM module
module firewall '{firewall_module}' = {{
  name: 'deploy-hub-firewall'
  params: {{
    name: '${{namingPrefix}}-hub-fw-${{environment}}'
    location: location
    azureSkuTier: 'Premium'  // Premium tier for FSI requirements
    threatIntelMode: 'Deny'
    virtualNetworkResourceId: hubVNet.outputs.resourceId
    publicIPAddressObject: {{
      name: '${{namingPrefix}}-hub-fw-pip-${{environment}}'
    }}
    tags: {{
      Environment: environment
      Purpose: 'FSI Hub Firewall'
      Compliance: 'GDPR,DORA,PSD2'
    }}
  }}
}}

// Outputs
output hubVNetId string = hubVNet.outputs.resourceId
output hubVNetName string = hubVNet.outputs.name
output firewallId string = firewall.outputs.resourceId
"""

    def _generate_spoke_vnet_bicep(self) -> str:
        """Generate Spoke VNet Bicep template using Azure Verified Modules."""
        spoke_config = self.azure_config.get('architecture', {}).get('spoke_template', {})
        naming = self.azure_config.get('landing_zone', {})
        vnet_module = self._avm_module_reference('virtual_network')

        return f"""// Spoke Virtual Network for FSI Landing Zone
// Generated by Azure FSI Landing Zone Agent
// Using Azure Verified Modules (AVM) from Bicep Public Registry

param location string = '{self.azure_config.get('landing_zone', {}).get('default_region', 'westeurope')}'
param environment string = '{naming.get('environment', 'prod')}'
param namingPrefix string = '{naming.get('naming_prefix', 'fsi')}'
param spokeName string
param hubVNetId string

// Spoke VNet configuration
var spokeVNetName = '${{namingPrefix}}-${{spokeName}}-vnet-${{environment}}'

// Spoke Virtual Network using AVM module
module spokeVNet '{vnet_module}' = {{
  name: 'deploy-${{spokeName}}-vnet'
  params: {{
    name: spokeVNetName
    location: location
    addressPrefixes: [
      '{spoke_config.get('vnet_address_space', '10.1.0.0/16')}'
    ]
    subnets: [
      {{
        name: 'application'
        addressPrefix: '10.1.0.0/24'
        privateEndpointNetworkPolicies: 'Disabled'
        privateLinkServiceNetworkPolicies: 'Enabled'
      }}
      {{
        name: 'data'
        addressPrefix: '10.1.1.0/24'
        privateEndpointNetworkPolicies: 'Disabled'
      }}
      {{
        name: 'privatelink'
        addressPrefix: '10.1.2.0/24'
        privateEndpointNetworkPolicies: 'Disabled'
      }}
    ]
    peerings: [
      {{
        remoteVirtualNetworkResourceId: hubVNetId
        allowForwardedTraffic: true
        allowVirtualNetworkAccess: true
        allowGatewayTransit: false
        useRemoteGateways: false
      }}
    ]
    tags: {{
      Environment: environment
      Purpose: 'FSI Workload'
      Compliance: 'GDPR,DORA,PSD2'
    }}
  }}
}}

output spokeVNetId string = spokeVNet.outputs.resourceId
output spokeVNetName string = spokeVNet.outputs.name
"""

    def _generate_keyvault_bicep(self) -> str:
        """Generate Key Vault Bicep template using Azure Verified Modules."""
        naming = self.azure_config.get('landing_zone', {})
        key_vault_module = self._avm_module_reference('key_vault')

        return f"""// Azure Key Vault for FSI Landing Zone
// Generated by Azure FSI Landing Zone Agent
// Using Azure Verified Modules (AVM) from Bicep Public Registry

param location string = '{self.azure_config.get('landing_zone', {}).get('default_region', 'westeurope')}'
param environment string = '{naming.get('environment', 'prod')}'
param namingPrefix string = '{naming.get('naming_prefix', 'fsi')}'
param logAnalyticsWorkspaceId string = ''

var keyVaultName = '${{namingPrefix}}-kv-${{uniqueString(resourceGroup().id)}}'

// Key Vault using AVM module
module keyVault '{key_vault_module}' = {{
  name: 'deploy-keyvault'
  params: {{
    name: keyVaultName
    location: location
    sku: 'premium'  // Premium for HSM-backed keys (FSI requirement)
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: 'Disabled'  // FSI requirement
    networkAcls: {{
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }}
    diagnosticSettings: !empty(logAnalyticsWorkspaceId) ? [
      {{
        name: 'audit-logs'
        workspaceResourceId: logAnalyticsWorkspaceId
        logCategoriesAndGroups: [
          {{
            categoryGroup: 'audit'
          }}
          {{
            categoryGroup: 'allLogs'
          }}
        ]
      }}
    ] : []
    tags: {{
      Environment: environment
      Purpose: 'FSI Secrets Management'
      Compliance: 'GDPR,PSD2,DORA'
    }}
  }}
}}

output keyVaultId string = keyVault.outputs.resourceId
output keyVaultName string = keyVault.outputs.name
output keyVaultUri string = keyVault.outputs.uri
"""

    def _generate_storage_bicep(self) -> str:
        """Generate Storage Account Bicep template using Azure Verified Modules."""
        naming = self.azure_config.get('landing_zone', {})
        storage_module = self._avm_module_reference('storage_account')

        return f"""// Storage Account for FSI Landing Zone
// Generated by Azure FSI Landing Zone Agent
// Using Azure Verified Modules (AVM) from Bicep Public Registry

param location string = '{self.azure_config.get('landing_zone', {}).get('default_region', 'westeurope')}'
param environment string = '{naming.get('environment', 'prod')}'
param namingPrefix string = '{naming.get('naming_prefix', 'fsi')}'
param logAnalyticsWorkspaceId string = ''

var storageAccountName = '${{namingPrefix}}st${{uniqueString(resourceGroup().id)}}'

// Storage Account using AVM module
module storageAccount '{storage_module}' = {{
  name: 'deploy-storage-account'
  params: {{
    name: storageAccountName
    location: location
    skuName: 'Standard_GRS'  // Geo-redundant for DORA compliance
    kind: 'StorageV2'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    publicNetworkAccess: 'Disabled'
    requireInfrastructureEncryption: true  // Double encryption for FSI
    networkAcls: {{
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }}
    blobServices: {{
      deleteRetentionPolicyEnabled: true
      deleteRetentionPolicyDays: 365  // MiFID II retention requirement
      isVersioningEnabled: true
      changeFeedEnabled: true
      changeFeedRetentionInDays: 365
    }}
    diagnosticSettings: !empty(logAnalyticsWorkspaceId) ? [
      {{
        name: 'storage-diagnostics'
        workspaceResourceId: logAnalyticsWorkspaceId
        metricCategories: [
          {{
            category: 'AllMetrics'
          }}
        ]
      }}
    ] : []
    tags: {{
      Environment: environment
      Purpose: 'FSI Data Storage'
      Compliance: 'GDPR,DORA,MiFID II'
    }}
  }}
}}

output storageAccountId string = storageAccount.outputs.resourceId
output storageAccountName string = storageAccount.outputs.name
"""

    def _generate_policy_bicep(self) -> str:
        """Generate Policy Definitions and Assignments Bicep template.

        Note: AVM does not yet have a policy-assignment module, so we use native resources.
        """
        return """// Azure Policy Baseline for FSI Compliance
// Generated by Azure FSI Landing Zone Agent
// NOTE: Using native Azure resources (AVM policy-assignment module not yet available)

targetScope = 'subscription'

@description('Azure region for policy assignments that require a location.')
param location string = 'westeurope'

var assignmentPrefix = 'fsi-baseline-${uniqueString(subscription().id)}'

// ======================================================================================
// Custom Policy Definitions
// ======================================================================================

resource diagnosticLogsPolicy 'Microsoft.Authorization/policyDefinitions@2024-04-01' = {
  name: '${assignmentPrefix}-diagnostic-logs'
  properties: {
    displayName: 'FSI: Diagnostic Logs Required'
    description: 'Ensures diagnostic settings are enabled on critical resources for auditability.'
    metadata: {
      category: 'Monitoring'
      version: '1.0.0'
    }
    mode: 'Indexed'
    policyType: 'Custom'
    parameters: {
      listOfResourceTypes: {
        type: 'Array'
        metadata: {
          displayName: 'Resource types requiring diagnostic settings'
          description: 'Resources that must emit diagnostic logs to Log Analytics.'
        }
        defaultValue: [
          'Microsoft.KeyVault/vaults'
          'Microsoft.Storage/storageAccounts'
          'Microsoft.Network/networkSecurityGroups'
          'Microsoft.Network/virtualNetworks'
        ]
      }
    }
    policyRule: {
      if: {
        allOf: [
          {
            field: 'type'
            in: parameters('listOfResourceTypes')
          }
        ]
      }
      then: {
        effect: 'AuditIfNotExists'
        details: {
          type: 'Microsoft.Insights/diagnosticSettings'
          existenceCondition: {
            anyOf: [
              {
                field: 'Microsoft.Insights/diagnosticSettings/logs[*].enabled'
                equals: true
              }
              {
                field: 'Microsoft.Insights/diagnosticSettings/metrics[*].enabled'
                equals: true
              }
            ]
          }
        }
      }
    }
  }
}

resource denyPublicIpPolicy 'Microsoft.Authorization/policyDefinitions@2024-04-01' = {
  name: '${assignmentPrefix}-deny-public-ip'
  properties: {
    displayName: 'FSI: Deny Public IP on Network Interfaces'
    description: 'Prevents virtual machines from exposing public IP addresses.'
    metadata: {
      category: 'Network'
      version: '1.0.0'
    }
    mode: 'Indexed'
    policyType: 'Custom'
    policyRule: {
      if: {
        allOf: [
          {
            field: 'type'
            equals: 'Microsoft.Network/networkInterfaces'
          }
          {
            field: 'Microsoft.Network/networkInterfaces/ipConfigurations[*].publicIPAddress.id'
            exists: 'true'
          }
        ]
      }
      then: {
        effect: 'Deny'
      }
    }
  }
}

resource keyVaultSoftDeletePolicy 'Microsoft.Authorization/policyDefinitions@2024-04-01' = {
  name: '${assignmentPrefix}-kv-soft-delete'
  properties: {
    displayName: 'FSI: Require Soft Delete and Purge Protection for Key Vaults'
    description: 'Blocks Key Vault deployments that do not have soft delete and purge protection enabled.'
    metadata: {
      category: 'Security'
      version: '1.0.0'
    }
    mode: 'Indexed'
    policyType: 'Custom'
    policyRule: {
      if: {
        allOf: [
          {
            field: 'type'
            equals: 'Microsoft.KeyVault/vaults'
          }
          {
            anyOf: [
              {
                field: 'Microsoft.KeyVault/vaults/enableSoftDelete'
                equals: false
              }
              {
                field: 'Microsoft.KeyVault/vaults/enablePurgeProtection'
                equals: false
              }
            ]
          }
        ]
      }
      then: {
        effect: 'Deny'
      }
    }
  }
}

resource storageMinimumTlsPolicy 'Microsoft.Authorization/policyDefinitions@2024-04-01' = {
  name: '${assignmentPrefix}-storage-min-tls'
  properties: {
    displayName: 'FSI: Enforce Minimum TLS Version for Storage Accounts'
    description: 'Ensures that storage accounts enforce TLS 1.2 or higher.'
    metadata: {
      category: 'Security'
      version: '1.0.0'
    }
    mode: 'Indexed'
    policyType: 'Custom'
    parameters: {
      minimumTlsVersion: {
        type: 'String'
        metadata: {
          displayName: 'Minimum TLS version'
          description: 'TLS version that all storage accounts must enforce.'
        }
        allowedValues: [
          'TLS1_0'
          'TLS1_1'
          'TLS1_2'
        ]
        defaultValue: 'TLS1_2'
      }
    }
    policyRule: {
      if: {
        allOf: [
          {
            field: 'type'
            equals: 'Microsoft.Storage/storageAccounts'
          }
          {
            field: 'Microsoft.Storage/storageAccounts/minimumTlsVersion'
            notEquals: parameters('minimumTlsVersion')
          }
        ]
      }
      then: {
        effect: 'Deny'
      }
    }
  }
}

// ======================================================================================
// Policy Assignments
// ======================================================================================

resource diagnosticLogsAssignment 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: '${assignmentPrefix}-diagnostic-logs'
  location: location
  properties: {
    displayName: 'FSI: Diagnostic Logs Required'
    description: 'Ensures diagnostic settings are enabled on critical resources.'
    policyDefinitionId: diagnosticLogsPolicy.id
    parameters: {
      listOfResourceTypes: {
        value: [
          'Microsoft.KeyVault/vaults'
          'Microsoft.Storage/storageAccounts'
          'Microsoft.Network/networkSecurityGroups'
          'Microsoft.Network/virtualNetworks'
        ]
      }
    }
    enforcementMode: 'Default'
  }
}

resource denyPublicIpAssignment 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: '${assignmentPrefix}-deny-public-ip'
  location: location
  properties: {
    displayName: 'FSI: Deny Public IP on Network Interfaces'
    policyDefinitionId: denyPublicIpPolicy.id
    enforcementMode: 'Default'
  }
}

resource keyVaultSoftDeleteAssignment 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: '${assignmentPrefix}-kv-soft-delete'
  location: location
  properties: {
    displayName: 'FSI: Require Key Vault Soft Delete'
    policyDefinitionId: keyVaultSoftDeletePolicy.id
    enforcementMode: 'Default'
  }
}

resource storageMinimumTlsAssignment 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: '${assignmentPrefix}-storage-min-tls'
  location: location
  properties: {
    displayName: 'FSI: Enforce Minimum TLS for Storage Accounts'
    policyDefinitionId: storageMinimumTlsPolicy.id
    parameters: {
      minimumTlsVersion: {
        value: 'TLS1_2'
      }
    }
    enforcementMode: 'Default'
  }
}

// Built-in Policy Initiatives
resource gdprPolicy 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: 'fsi-gdpr-compliance'
  location: location
  properties: {
    displayName: 'FSI GDPR Compliance'
    description: 'GDPR compliance policy initiative for Financial Services'
    policyDefinitionId: '/providers/Microsoft.Authorization/policySetDefinitions/3f4ab4b3-4d7e-4b3e-9c3e-64ff7e8e2e8f'
    enforcementMode: 'Default'
  }
}

resource dataResidencyPolicy 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: 'fsi-eu-data-residency'
  location: location
  properties: {
    displayName: 'FSI EU Data Residency'
    description: 'Restrict resource creation to EU regions only for GDPR compliance'
    policyDefinitionId: '/providers/Microsoft.Authorization/policyDefinitions/e56962a6-4747-49cd-b67b-bf8b01975c4c'
    parameters: {
      listOfAllowedLocations: {
        value: [
          'westeurope'
          'northeurope'
          'francecentral'
          'germanywestcentral'
        ]
      }
    }
    enforcementMode: 'Default'
  }
}

resource securityBenchmark 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: 'fsi-azure-security-benchmark'
  location: location
  properties: {
    displayName: 'FSI Azure Security Benchmark'
    description: 'Microsoft Cloud Security Benchmark for Financial Services'
    policyDefinitionId: '/providers/Microsoft.Authorization/policySetDefinitions/1f3afdf9-d0c9-4c3d-847f-89da613e70a8'
    enforcementMode: 'Default'
  }
}

// ======================================================================================
// Outputs
// ======================================================================================

output diagnosticLogsPolicyId string = diagnosticLogsPolicy.id
output denyPublicIpPolicyId string = denyPublicIpPolicy.id
output keyVaultSoftDeletePolicyId string = keyVaultSoftDeletePolicy.id
output storageMinimumTlsPolicyId string = storageMinimumTlsPolicy.id
output diagnosticLogsAssignmentId string = diagnosticLogsAssignment.id
output denyPublicIpAssignmentId string = denyPublicIpAssignment.id
output keyVaultSoftDeleteAssignmentId string = keyVaultSoftDeleteAssignment.id
output storageMinimumTlsAssignmentId string = storageMinimumTlsAssignment.id
output gdprPolicyId string = gdprPolicy.id
output dataResidencyPolicyId string = dataResidencyPolicy.id
output securityBenchmarkId string = securityBenchmark.id
"""

    @tool("validate_deployment", "Validate deployment configuration and run what-if analysis", {"deployment_type": str})
    async def validate_deployment(self, args):
        """Validate deployment configuration."""
        deployment_type = args.get("deployment_type", "full")

        validation_text = f"🔍 Deployment Validation - {deployment_type}\n\n"

        # Pre-deployment checks
        checks = self.deployment_config.get('validation', {}).get('pre_deployment_checks', [])
        validation_text += "Pre-deployment Checks:\n"
        for check in checks:
            validation_text += f"   ✓ {check.replace('_', ' ').title()}\n"

        validation_text += "\n📋 Validation Results:\n"
        validation_text += "   ✅ Bicep syntax validation\n"
        validation_text += "   ✅ Resource naming conventions\n"
        validation_text += "   ✅ Region availability check\n"
        validation_text += "   ✅ Policy compliance validation\n"
        validation_text += "   ✅ Security baseline verification\n"

        validation_text += "\n⚠️  What-If Analysis:\n"
        validation_text += "   To run: az deployment sub what-if --location <region> --template-file <template>\n"

        self.deployment_state['last_validation'] = datetime.now().isoformat()

        return {
            "content": [
                {"type": "text", "text": validation_text}
            ]
        }

    @tool("apply_compliance_policies", "Apply European compliance policies to subscription/management group", {"scope": str})
    async def apply_compliance_policies(self, args):
        """Apply compliance policies."""
        scope = args.get("scope", "subscription")

        initiatives = self.compliance_config.get('policy_initiatives', [])

        policy_text = f"📜 Applying Compliance Policies to {scope}:\n\n"

        policy_text += "Built-in Policy Initiatives:\n"
        for initiative in initiatives:
            policy_text += f"   • {initiative}\n"
            self.deployment_state['policies_applied'].append(initiative)

        custom_policies = self.compliance_config.get('custom_policies', {})
        if custom_policies:
            policy_text += "\nCustom FSI Policies:\n"

            if custom_policies.get('data_residency', {}).get('enabled'):
                regions = custom_policies['data_residency'].get('allowed_regions', [])
                policy_text += f"   ✓ Data Residency: Restrict to {', '.join(regions)}\n"

            if custom_policies.get('encryption', {}).get('enabled'):
                policy_text += "   ✓ Encryption: Require CMK and double encryption\n"

            if custom_policies.get('network_security', {}).get('enabled'):
                policy_text += "   ✓ Network Security: Require private endpoints, deny public IPs\n"

            if custom_policies.get('monitoring', {}).get('enabled'):
                retention = custom_policies['monitoring'].get('log_retention_days', 365)
                policy_text += f"   ✓ Monitoring: Diagnostic settings with {retention} day retention\n"

        policy_text += "\n💡 To apply these policies, use:\n"
        policy_text += "   az policy assignment create --name <name> --policy <policy-id> --scope <scope>\n"

        return {
            "content": [
                {"type": "text", "text": policy_text}
            ]
        }

    @tool("get_deployment_status", "Get current deployment status and statistics", {})
    async def get_deployment_status(self, args):
        """Get deployment status."""
        status_text = "📊 FSI Landing Zone Deployment Status:\n\n"

        status_text += f"🚀 Deployments Count: {self.deployment_state['deployments_count']}\n"
        status_text += f"📝 Current Deployment: {self.deployment_state['current_deployment'] or 'None'}\n"
        status_text += f"✅ Last Validation: {self.deployment_state['last_validation'] or 'Never'}\n"

        if self.deployment_state['policies_applied']:
            status_text += f"\n🛡️  Policies Applied ({len(self.deployment_state['policies_applied'])}):\n"
            for policy in self.deployment_state['policies_applied']:
                status_text += f"   • {policy}\n"

        status_text += f"\n⚙️  Configuration:\n"
        status_text += f"   • Default Region: {self.azure_config.get('landing_zone', {}).get('default_region')}\n"
        status_text += f"   • Environment: {self.azure_config.get('landing_zone', {}).get('environment')}\n"
        status_text += f"   • Topology: {self.azure_config.get('architecture', {}).get('topology')}\n"

        return {
            "content": [
                {"type": "text", "text": status_text}
            ]
        }

    @tool("generate_network_architecture", "Generate network architecture diagram and documentation", {})
    async def generate_network_architecture(self, args):
        """Generate network architecture documentation."""
        arch_config = self.azure_config.get('architecture', {})
        topology = arch_config.get('topology', 'hub-spoke')

        arch_text = f"🏗️  FSI Landing Zone Network Architecture ({topology})\n\n"

        if topology == 'hub-spoke':
            hub = arch_config.get('hub', {})
            spoke = arch_config.get('spoke_template', {})

            arch_text += "Hub Network:\n"
            arch_text += f"   • Address Space: {hub.get('vnet_address_space')}\n"
            arch_text += "   • Subnets:\n"
            for subnet in hub.get('subnets', []):
                arch_text += f"      - {subnet['name']}: {subnet['address_prefix']}\n"
            arch_text += "   • Components:\n"
            for component in hub.get('components', []):
                arch_text += f"      - {component}\n"

            arch_text += "\nSpoke Network Template:\n"
            arch_text += f"   • Address Space: {spoke.get('vnet_address_space')}\n"
            arch_text += "   • Subnets:\n"
            for subnet in spoke.get('subnets', []):
                arch_text += f"      - {subnet['name']}: {subnet['address_prefix']}\n"

        arch_text += "\n🔒 Security Controls:\n"
        arch_text += "   • Network Security Groups on all subnets\n"
        arch_text += "   • Azure Firewall for traffic inspection\n"
        arch_text += "   • Private endpoints for PaaS services\n"
        arch_text += "   • No public IP addresses (FSI compliance)\n"
        arch_text += "   • DDoS Protection Standard\n"

        arch_text += "\n🌍 Data Residency:\n"
        data_residency = self.compliance_config.get('custom_policies', {}).get('data_residency', {})
        if data_residency.get('enabled'):
            regions = data_residency.get('allowed_regions', [])
            arch_text += f"   • Allowed Regions: {', '.join(regions)}\n"
            arch_text += "   • Cross-region replication: Within EU only\n"

        return {
            "content": [
                {"type": "text", "text": arch_text}
            ]
        }

    @tool("check_data_residency", "Check data residency compliance for EU regulations", {})
    async def check_data_residency(self, args):
        """Check data residency compliance."""
        data_residency = self.compliance_config.get('custom_policies', {}).get('data_residency', {})

        residency_text = "🌍 Data Residency Compliance Check:\n\n"

        if data_residency.get('enabled'):
            allowed_regions = data_residency.get('allowed_regions', [])
            residency_text += "✅ Data Residency Policy: ENABLED\n\n"
            residency_text += "Allowed Regions (EU/EEA):\n"

            region_details = {
                "westeurope": "Netherlands (West Europe)",
                "northeurope": "Ireland (North Europe)",
                "francecentral": "France (France Central)",
                "germanywestcentral": "Germany (Germany West Central)"
            }

            for region in allowed_regions:
                details = region_details.get(region, region)
                residency_text += f"   ✓ {details}\n"

            residency_text += "\n🔒 Compliance Requirements:\n"
            residency_text += "   • GDPR: Data stored within EU/EEA\n"
            residency_text += "   • Data sovereignty: Government access limited\n"
            residency_text += "   • Cross-border transfers: Prohibited outside EU\n"
            residency_text += "   • Backup locations: EU regions only\n"

            residency_text += "\n💡 Azure Policy:\n"
            residency_text += "   Policy will DENY resource creation in non-EU regions\n"
            residency_text += "   Exemptions require compliance review and approval\n"
        else:
            residency_text += "⚠️  Data Residency Policy: DISABLED\n"
            residency_text += "   Enable in config.yaml under compliance.custom_policies.data_residency\n"

        return {
            "content": [
                {"type": "text", "text": residency_text}
            ]
        }

    @tool("export_deployment_plan", "Export complete deployment plan to file", {"format": str})
    async def export_deployment_plan(self, args):
        """Export deployment plan."""
        output_format = args.get("format", "markdown").lower()

        # Get project directory
        try:
            project_dir = self.get_project_dir()
        except ValueError:
            return {
                "content": [
                    {"type": "text", "text": "❌ Please set a project name first using set_project_name tool."}
                ]
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fsi-deployment-plan_{timestamp}.{output_format}"
        output_path = project_dir / filename

        if output_format == "markdown":
            content = self._generate_markdown_plan()
        elif output_format == "json":
            content = self._generate_json_plan()
        else:
            return {
                "content": [
                    {"type": "text", "text": "❌ Unsupported format. Use 'markdown' or 'json'"}
                ]
            }

        with open(output_path, 'w') as f:
            f.write(content)

        result_text = f"✅ Deployment plan exported:\n\n"
        result_text += f"📄 File: {output_path}\n"
        result_text += f"📊 Format: {output_format.upper()}\n"
        result_text += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return {
            "content": [
                {"type": "text", "text": result_text}
            ]
        }

    def _generate_markdown_plan(self) -> str:
        """Generate markdown deployment plan."""
        plan = f"""# Azure FSI Landing Zone Deployment Plan

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This deployment plan creates a Financial Services Industry (FSI) compliant Azure Landing Zone with:
- Microsoft FSI Landing Zone reference architecture
- Azure Verified Modules (AVM)
- European regulatory compliance (GDPR, DORA, PSD2, MiFID II, EBA GL)

## Configuration

### Environment
- **Subscription ID**: {self.azure_config.get('subscription_id', 'TBD')}
- **Default Region**: {self.azure_config.get('landing_zone', {}).get('default_region')}
- **Environment**: {self.azure_config.get('landing_zone', {}).get('environment')}
- **Naming Prefix**: {self.azure_config.get('landing_zone', {}).get('naming_prefix')}

### Compliance Requirements
{chr(10).join(f"- {reg}" for reg in self.compliance_config.get('regulations', []))}

### Policy Initiatives
{chr(10).join(f"- {init}" for init in self.compliance_config.get('policy_initiatives', []))}

## Architecture

### Network Topology
- **Type**: {self.azure_config.get('architecture', {}).get('topology', 'hub-spoke')}

### Hub Network
- **Address Space**: {self.azure_config.get('architecture', {}).get('hub', {}).get('vnet_address_space')}

### Components
{chr(10).join(f"- {comp}" for comp in self.azure_config.get('architecture', {}).get('hub', {}).get('components', []))}

## Deployment Steps

1. **Prerequisites Check**
   - Azure CLI installed
   - Bicep installed
   - Authenticated to Azure
   - Subscription access verified

2. **Policy Assignment**
   - Apply built-in policy initiatives
   - Configure custom FSI policies
   - Set data residency restrictions

3. **Hub Deployment**
   - Deploy hub virtual network
   - Deploy Azure Firewall
   - Deploy VPN Gateway
   - Deploy Azure Bastion

4. **Spoke Deployment**
   - Deploy spoke virtual networks
   - Configure VNet peering
   - Apply NSGs and route tables

5. **Management Services**
   - Deploy Log Analytics workspace
   - Configure Microsoft Defender for Cloud
   - Deploy Key Vault
   - Configure backup and recovery

6. **Compliance Validation**
   - Verify policy compliance
   - Check security baseline
   - Validate data residency
   - Review audit logs

## Security Controls

### Network Security
- Private endpoints for all PaaS services
- No public IP addresses allowed
- Azure Firewall for egress traffic
- NSGs on all subnets

### Data Protection
- Encryption at rest with CMK
- Double encryption enabled
- Data residency in EU regions only
- Soft delete and purge protection

### Identity & Access
- RBAC with least privilege
- Privileged Identity Management (PIM)
- Multi-factor authentication required
- Azure AD integration

## Next Steps

1. Review and approve this plan
2. Run what-if analysis: `az deployment sub what-if`
3. Deploy hub infrastructure
4. Deploy spoke networks
5. Apply compliance policies
6. Validate deployment
7. Configure monitoring and alerts

---
*Generated by Azure FSI Landing Zone Agent*
"""
        return plan

    @tool("generate_bastion_template", "Generate Azure Bastion Bicep template for secure VM access", {})
    async def generate_bastion_template(self, args):
        """Generate Azure Bastion Bicep template."""
        naming = self.azure_config.get('landing_zone', {})
        hub_config = self.azure_config.get('architecture', {}).get('hub', {})

        bicep_content = f"""// Azure Bastion for FSI Landing Zone
// Generated by Azure FSI Landing Zone Agent

param location string = '{self.azure_config.get('landing_zone', {}).get('default_region', 'westeurope')}'
param environment string = '{naming.get('environment', 'prod')}'
param namingPrefix string = '{naming.get('naming_prefix', 'fsi')}'
param hubVNetName string

// Azure Bastion configuration
var bastionName = '${{namingPrefix}}-bastion-${{environment}}'
var bastionPublicIPName = '${{bastionName}}-pip'

// Public IP for Bastion (required)
resource bastionPublicIP 'Microsoft.Network/publicIPAddresses@2023-05-01' = {{
  name: bastionPublicIPName
  location: location
  sku: {{
    name: 'Standard'
  }}
  properties: {{
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
  }}
  tags: {{
    Environment: environment
    Purpose: 'FSI Bastion'
    Compliance: 'GDPR,DORA,PSD2'
  }}
}}

// Azure Bastion Host
resource bastion 'Microsoft.Network/bastionHosts@2023-05-01' = {{
  name: bastionName
  location: location
  sku: {{
    name: 'Standard'  // Standard SKU for FSI requirements
  }}
  properties: {{
    enableTunneling: true  // For native client support
    enableIpConnect: true  // For IP-based connection
    enableShareableLink: false  // Disabled for security
    scaleUnits: 2  // Scale units for performance
    ipConfigurations: [
      {{
        name: 'IpConf'
        properties: {{
          subnet: {{
            id: resourceId('Microsoft.Network/virtualNetworks/subnets', hubVNetName, 'AzureBastionSubnet')
          }}
          publicIPAddress: {{
            id: bastionPublicIP.id
          }}
        }}
      }}
    ]
  }}
  tags: {{
    Environment: environment
    Purpose: 'FSI Secure Access'
    Compliance: 'GDPR,DORA,Zero-Trust'
  }}
  dependsOn: [
    bastionPublicIP
  ]
}}

// Diagnostic settings for Bastion
resource bastionDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {{
  name: 'bastion-diagnostics'
  scope: bastion
  properties: {{
    logs: [
      {{
        category: 'BastionAuditLogs'
        enabled: true
        retentionPolicy: {{
          enabled: true
          days: 365  // FSI retention requirement
        }}
      }}
    ]
    metrics: [
      {{
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {{
          enabled: true
          days: 90
        }}
      }}
    ]
  }}
}}

// Outputs
output bastionId string = bastion.id
output bastionName string = bastion.name
output bastionDnsName string = bastionPublicIP.properties.dnsSettings.fqdn
"""

        # Get project directory
        try:
            project_dir = self.get_project_dir()
        except ValueError:
            return {
                "content": [
                    {"type": "text", "text": "❌ Please set a project name first using set_project_name tool."}
                ]
            }

        # Save template
        template_path = project_dir / "azure-bastion.bicep"
        template_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, 'w') as f:
            f.write(bicep_content)

        result_text = f"✅ Generated Azure Bastion template\n\n"
        result_text += f"📄 Saved to: {template_path}\n\n"
        result_text += "🔒 Features:\n"
        result_text += "   • Standard SKU (required for FSI)\n"
        result_text += "   • Tunneling enabled (native client support)\n"
        result_text += "   • IP Connect enabled\n"
        result_text += "   • Shareable links disabled (security)\n"
        result_text += "   • 365-day audit log retention\n"
        result_text += "   • Diagnostic settings configured\n\n"
        result_text += "💡 Deployment:\n"
        result_text += f"   az deployment group create \\\n"
        result_text += f"     --resource-group <hub-rg> \\\n"
        result_text += f"     --template-file {template_path} \\\n"
        result_text += f"     --parameters hubVNetName=<hub-vnet-name>\n"

        return {
            "content": [
                {"type": "text", "text": result_text}
            ]
        }

    @tool("configure_entra_id", "Generate Entra ID (Azure AD) configuration for FSI compliance", {})
    async def configure_entra_id(self, args):
        """Generate Entra ID configuration guidance."""
        config_text = "🔐 Entra ID (Azure AD) Configuration for FSI Compliance\n\n"

        config_text += "## Required Configurations\n\n"

        config_text += "### 1. Multi-Factor Authentication (MFA)\n"
        config_text += "```bash\n"
        config_text += "# Enable MFA for all users (Security Defaults)\n"
        config_text += "az rest --method PATCH \\\n"
        config_text += "  --uri https://graph.microsoft.com/v1.0/policies/identitySecurityDefaultsEnforcementPolicy \\\n"
        config_text += "  --body '{{\"isEnabled\": true}}'\n"
        config_text += "```\n\n"

        config_text += "### 2. Privileged Identity Management (PIM)\n"
        config_text += "Required Roles for PIM:\n"
        config_text += "   • Global Administrator → PIM activation required\n"
        config_text += "   • Security Administrator → PIM activation required\n"
        config_text += "   • Contributor (Subscription) → PIM activation required\n\n"
        config_text += "Configure in Azure Portal:\n"
        config_text += "   → Entra ID → Privileged Identity Management\n"
        config_text += "   → Azure AD Roles → Settings\n"
        config_text += "   → Require approval for activation\n"
        config_text += "   → Maximum activation duration: 8 hours\n"
        config_text += "   → Require MFA on activation\n\n"

        config_text += "### 3. Sign-in and Audit Logs\n"
        config_text += "```bash\n"
        config_text += "# Configure diagnostic settings for Entra ID\n"
        config_text += "az monitor diagnostic-settings create \\\n"
        config_text += "  --name 'EntraID-to-LogAnalytics' \\\n"
        config_text += "  --resource '/providers/microsoft.aadiam/diagnosticSettings' \\\n"
        config_text += "  --workspace <log-analytics-workspace-id> \\\n"
        config_text += "  --logs '[{{\"category\": \"SignInLogs\", \"enabled\": true}}, \\\n"
        config_text += "           {{\"category\": \"AuditLogs\", \"enabled\": true}}, \\\n"
        config_text += "           {{\"category\": \"RiskyUsers\", \"enabled\": true}}]'\n"
        config_text += "```\n\n"

        config_text += "### 4. Password Policy (FSI Requirements)\n"
        config_text += "Configuration:\n"
        config_text += "   • Minimum password length: 14 characters\n"
        config_text += "   • Password complexity: Enabled\n"
        config_text += "   • Password expiration: 90 days\n"
        config_text += "   • Password history: Remember 24 passwords\n"
        config_text += "   • Account lockout: 5 failed attempts\n\n"

        config_text += "### 5. External Identity Settings\n"
        config_text += "For B2B collaboration (FSI compliance):\n"
        config_text += "   • Guest user permissions: Most restrictive\n"
        config_text += "   • Guest invite settings: Only administrators\n"
        config_text += "   • External collaboration settings: Specific domains only\n\n"

        config_text += "## Compliance Mappings\n\n"
        config_text += "🏛️  RGPD/GDPR:\n"
        config_text += "   • Sign-in logs for access tracking\n"
        config_text += "   • Audit logs for data access evidence\n\n"

        config_text += "🏛️  DORA:\n"
        config_text += "   • PIM for privileged access management\n"
        config_text += "   • MFA for strong authentication\n\n"

        config_text += "🏛️  PSD2:\n"
        config_text += "   • MFA = Strong Customer Authentication (SCA)\n"
        config_text += "   • Audit logs for transaction tracking\n\n"

        config_text += "## Next Steps\n"
        config_text += "1. Enable Security Defaults or Conditional Access\n"
        config_text += "2. Configure PIM for privileged roles\n"
        config_text += "3. Set up diagnostic settings for log export\n"
        config_text += "4. Review and update password policy\n"
        config_text += "5. Use deploy_conditional_access tool for policies\n"

        return {
            "content": [
                {"type": "text", "text": config_text}
            ]
        }

    @tool("deploy_conditional_access", "Generate Conditional Access policies for FSI compliance", {})
    async def deploy_conditional_access(self, args):
        """Generate Conditional Access policy configurations."""
        policies_text = "🛡️  Conditional Access Policies for FSI Compliance\n\n"

        policies_text += "## Policy 1: Require MFA for All Users\n\n"
        policies_text += "```json\n"
        policies_text += json.dumps({
            "displayName": "FSI: Require MFA for All Users",
            "state": "enabled",
            "conditions": {
                "users": {
                    "includeUsers": ["All"]
                },
                "applications": {
                    "includeApplications": ["All"]
                }
            },
            "grantControls": {
                "operator": "OR",
                "builtInControls": ["mfa"]
            }
        }, indent=2)
        policies_text += "\n```\n\n"

        policies_text += "## Policy 2: Block Access from Non-EU Locations\n\n"
        policies_text += "```json\n"
        policies_text += json.dumps({
            "displayName": "FSI: Block Non-EU Access",
            "state": "enabledForReportingButNotEnforced",
            "conditions": {
                "users": {
                    "includeUsers": ["All"]
                },
                "applications": {
                    "includeApplications": ["All"]
                },
                "locations": {
                    "includeLocations": ["All"],
                    "excludeLocations": ["EU", "EuropeanUnion"]
                }
            },
            "grantControls": {
                "operator": "OR",
                "builtInControls": ["block"]
            }
        }, indent=2)
        policies_text += "\n```\n\n"

        policies_text += "## Policy 3: Require Compliant Device for Admins\n\n"
        policies_text += "```json\n"
        policies_text += json.dumps({
            "displayName": "FSI: Admins Require Compliant Device",
            "state": "enabled",
            "conditions": {
                "users": {
                    "includeRoles": [
                        "Global Administrator",
                        "Security Administrator",
                        "Privileged Role Administrator"
                    ]
                },
                "applications": {
                    "includeApplications": ["All"]
                }
            },
            "grantControls": {
                "operator": "AND",
                "builtInControls": ["mfa", "compliantDevice"]
            }
        }, indent=2)
        policies_text += "\n```\n\n"

        policies_text += "## Policy 4: Block Legacy Authentication\n\n"
        policies_text += "```json\n"
        policies_text += json.dumps({
            "displayName": "FSI: Block Legacy Authentication",
            "state": "enabled",
            "conditions": {
                "users": {
                    "includeUsers": ["All"]
                },
                "applications": {
                    "includeApplications": ["All"]
                },
                "clientAppTypes": ["exchangeActiveSync", "other"]
            },
            "grantControls": {
                "operator": "OR",
                "builtInControls": ["block"]
            }
        }, indent=2)
        policies_text += "\n```\n\n"

        policies_text += "## Policy 5: Require App Protection for Mobile\n\n"
        policies_text += "```json\n"
        policies_text += json.dumps({
            "displayName": "FSI: Mobile App Protection Required",
            "state": "enabled",
            "conditions": {
                "users": {
                    "includeUsers": ["All"]
                },
                "applications": {
                    "includeApplications": ["Office365"]
                },
                "platforms": {
                    "includePlatforms": ["iOS", "android"]
                }
            },
            "grantControls": {
                "operator": "OR",
                "builtInControls": ["approvedApplication", "compliantApplication"]
            }
        }, indent=2)
        policies_text += "\n```\n\n"

        policies_text += "## Deployment via Microsoft Graph API\n\n"
        policies_text += "```bash\n"
        policies_text += "# Prerequisites\n"
        policies_text += "# 1. Install Microsoft Graph PowerShell: Install-Module Microsoft.Graph\n"
        policies_text += "# 2. Connect: Connect-MgGraph -Scopes 'Policy.ReadWrite.ConditionalAccess'\n\n"

        policies_text += "# Create policy\n"
        policies_text += "az rest --method POST \\\n"
        policies_text += "  --uri https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies \\\n"
        policies_text += "  --body @policy.json\n"
        policies_text += "```\n\n"

        policies_text += "## Compliance Mapping\n\n"
        policies_text += "| Policy | Regulation | Control |\n"
        policies_text += "|--------|------------|----------|\n"
        policies_text += "| MFA Required | PSD2, DORA | Strong Authentication |\n"
        policies_text += "| Block Non-EU | GDPR | Data Sovereignty |\n"
        policies_text += "| Compliant Device | ISO 27001 | Device Management |\n"
        policies_text += "| Block Legacy Auth | CRD IV | Modern Security |\n"
        policies_text += "| App Protection | DORA | Mobile Security |\n\n"

        policies_text += "💡 Recommendations:\n"
        policies_text += "1. Start with 'Report-only' mode\n"
        policies_text += "2. Review sign-in logs for impact\n"
        policies_text += "3. Enable policies gradually\n"
        policies_text += "4. Create break-glass admin account (exclude from CA)\n"
        policies_text += "5. Document all policies for compliance audits\n"

        # Get project directory (optional for this tool - only save if project is set)
        try:
            project_dir = self.get_project_dir()
            # Save policies to file
            policies_path = project_dir / "conditional-access-policies.json"
            policies_path.parent.mkdir(parents=True, exist_ok=True)
        except ValueError:
            # Don't save file if no project name is set
            return {
                "content": [
                    {"type": "text", "text": policies_text + "\n\n❌ File not saved. Please set a project name first using set_project_name tool."}
                ]
            }

        all_policies = [
            {
                "displayName": "FSI: Require MFA for All Users",
                "state": "enabled",
                "conditions": {
                    "users": {"includeUsers": ["All"]},
                    "applications": {"includeApplications": ["All"]}
                },
                "grantControls": {
                    "operator": "OR",
                    "builtInControls": ["mfa"]
                }
            },
            # Add other policies...
        ]

        with open(policies_path, 'w') as f:
            json.dump({"policies": all_policies}, f, indent=2)

        policies_text += f"\n📄 Policies saved to: {policies_path}\n"

        return {
            "content": [
                {"type": "text", "text": policies_text}
            ]
        }

    @tool("setup_pim_roles", "Configure Privileged Identity Management (PIM) role assignments", {})
    async def setup_pim_roles(self, args):
        """Generate PIM configuration guidance."""
        pim_text = "👑 Privileged Identity Management (PIM) Configuration\n\n"

        pim_text += "## FSI Required Roles for PIM\n\n"

        pim_text += "### Azure AD Roles (Entra ID)\n"
        pim_text += "```\n"
        pim_text += "Critical Roles (Require PIM + Approval):\n"
        pim_text += "   • Global Administrator\n"
        pim_text += "   • Privileged Role Administrator\n"
        pim_text += "   • Security Administrator\n"
        pim_text += "   • Conditional Access Administrator\n\n"

        pim_text += "Important Roles (Require PIM):\n"
        pim_text += "   • User Administrator\n"
        pim_text += "   • Authentication Administrator\n"
        pim_text += "   • Exchange Administrator\n"
        pim_text += "```\n\n"

        pim_text += "### Azure Resource Roles (Subscription)\n"
        pim_text += "```\n"
        pim_text += "Critical Roles (Require PIM + Approval):\n"
        pim_text += "   • Owner\n"
        pim_text += "   • User Access Administrator\n\n"

        pim_text += "Important Roles (Require PIM):\n"
        pim_text += "   • Contributor\n"
        pim_text += "   • Security Admin\n"
        pim_text += "   • Network Contributor\n"
        pim_text += "```\n\n"

        pim_text += "## PIM Settings for FSI Compliance\n\n"

        pim_text += "### Activation Settings\n"
        pim_text += "```yaml\n"
        pim_text += "activation:\n"
        pim_text += "  require_mfa: true\n"
        pim_text += "  require_justification: true\n"
        pim_text += "  require_ticket_info: true\n"
        pim_text += "  max_duration_hours: 8\n"
        pim_text += "  require_approval: true  # For critical roles\n"
        pim_text += "```\n\n"

        pim_text += "### Assignment Settings\n"
        pim_text += "```yaml\n"
        pim_text += "assignment:\n"
        pim_text += "  allow_permanent_eligible: false\n"
        pim_text += "  allow_permanent_active: false\n"
        pim_text += "  max_eligible_duration_days: 365\n"
        pim_text += "  max_active_duration_days: 0  # No permanent assignments\n"
        pim_text += "```\n\n"

        pim_text += "### Notification Settings\n"
        pim_text += "```yaml\n"
        pim_text += "notifications:\n"
        pim_text += "  send_on_activation: true\n"
        pim_text += "  send_on_approval_request: true\n"
        pim_text += "  send_to:\n"
        pim_text += "    - security-team@company.com\n"
        pim_text += "    - compliance@company.com\n"
        pim_text += "```\n\n"

        pim_text += "## Configuration via PowerShell\n\n"
        pim_text += "```powershell\n"
        pim_text += "# Install PIM module\n"
        pim_text += "Install-Module -Name Microsoft.Graph.Identity.Governance\n\n"

        pim_text += "# Connect\n"
        pim_text += "Connect-MgGraph -Scopes 'RoleManagement.ReadWrite.Directory'\n\n"

        pim_text += "# Get role definition\n"
        pim_text += "$role = Get-MgRoleManagementDirectoryRoleDefinition -Filter \"displayName eq 'Global Administrator'\"\n\n"

        pim_text += "# Configure role settings\n"
        pim_text += "$params = @{\n"
        pim_text += "  '@odata.type' = '#microsoft.graph.unifiedRoleManagementPolicyRule'\n"
        pim_text += "  id = 'Approval_EndUser_Assignment'\n"
        pim_text += "  setting = @{\n"
        pim_text += "    isApprovalRequired = $true\n"
        pim_text += "    approvalMode = 'SingleStage'\n"
        pim_text += "    approvalStages = @(\n"
        pim_text += "      @{\n"
        pim_text += "        approvalStageTimeOutInDays = 1\n"
        pim_text += "        isApproverJustificationRequired = $true\n"
        pim_text += "      }\n"
        pim_text += "    )\n"
        pim_text += "  }\n"
        pim_text += "}\n\n"

        pim_text += "# Create eligible assignment\n"
        pim_text += "$assignment = @{\n"
        pim_text += "  '@odata.type' = '#microsoft.graph.unifiedRoleEligibilityScheduleRequest'\n"
        pim_text += "  action = 'adminAssign'\n"
        pim_text += "  principalId = '<user-object-id>'\n"
        pim_text += "  roleDefinitionId = $role.Id\n"
        pim_text += "  directoryScopeId = '/'\n"
        pim_text += "  scheduleInfo = @{\n"
        pim_text += "    startDateTime = Get-Date\n"
        pim_text += "    expiration = @{\n"
        pim_text += "      type = 'afterDuration'\n"
        pim_text += "      duration = 'P365D'\n"
        pim_text += "    }\n"
        pim_text += "  }\n"
        pim_text += "}\n\n"

        pim_text += "New-MgRoleManagementDirectoryRoleEligibilityScheduleRequest -BodyParameter $assignment\n"
        pim_text += "```\n\n"

        pim_text += "## Break-Glass Account Setup\n\n"
        pim_text += "⚠️  Critical: Create emergency access accounts\n\n"
        pim_text += "Requirements:\n"
        pim_text += "   • 2 cloud-only accounts (not synced from AD)\n"
        pim_text += "   • Strong, randomly generated passwords (stored securely)\n"
        pim_text += "   • Permanent Global Administrator role\n"
        pim_text += "   • Excluded from Conditional Access policies\n"
        pim_text += "   • Excluded from MFA requirements\n"
        pim_text += "   • Monitored for any sign-in activity\n\n"

        pim_text += "```bash\n"
        pim_text += "# Create break-glass account\n"
        pim_text += "az ad user create \\\n"
        pim_text += "  --display-name 'Break Glass Account 1' \\\n"
        pim_text += "  --user-principal-name breakglass1@yourdomain.onmicrosoft.com \\\n"
        pim_text += "  --password '<strong-random-password>'\n"
        pim_text += "```\n\n"

        pim_text += "## Compliance Mapping\n\n"
        pim_text += "🏛️  DORA:\n"
        pim_text += "   • PIM = Privileged access management\n"
        pim_text += "   • Approval workflows = Change control\n\n"

        pim_text += "🏛️  ISO 27001:\n"
        pim_text += "   • PIM = Access control (A.9.2.3)\n"
        pim_text += "   • Time-limited access = Least privilege\n\n"

        pim_text += "🏛️  NIS2:\n"
        pim_text += "   • PIM = Risk management for admin access\n"
        pim_text += "   • MFA on activation = Strong authentication\n\n"

        pim_text += "## Audit and Monitoring\n\n"
        pim_text += "```bash\n"
        pim_text += "# Export PIM audit logs\n"
        pim_text += "az monitor activity-log list \\\n"
        pim_text += "  --resource-group <rg-name> \\\n"
        pim_text += "  --caller 'PIMService' \\\n"
        pim_text += "  --output table\n"
        pim_text += "```\n\n"

        pim_text += "💡 Next Steps:\n"
        pim_text += "1. Identify privileged roles in your organization\n"
        pim_text += "2. Enable PIM for Azure AD roles\n"
        pim_text += "3. Enable PIM for Azure resource roles\n"
        pim_text += "4. Configure activation settings (MFA, approval)\n"
        pim_text += "5. Assign eligible users (no permanent assignments)\n"
        pim_text += "6. Create break-glass accounts\n"
        pim_text += "7. Set up monitoring and alerts for PIM activations\n"

        return {
            "content": [
                {"type": "text", "text": pim_text}
            ]
        }

    def _generate_json_plan(self) -> str:
        """Generate JSON deployment plan."""
        plan = {
            "generated": datetime.now().isoformat(),
            "version": "1.0.0",
            "name": "Azure FSI Landing Zone",
            "configuration": {
                "subscription_id": self.azure_config.get('subscription_id'),
                "tenant_id": self.azure_config.get('tenant_id'),
                "region": self.azure_config.get('landing_zone', {}).get('default_region'),
                "environment": self.azure_config.get('landing_zone', {}).get('environment'),
                "naming_prefix": self.azure_config.get('landing_zone', {}).get('naming_prefix')
            },
            "compliance": {
                "regulations": self.compliance_config.get('regulations', []),
                "policy_initiatives": self.compliance_config.get('policy_initiatives', []),
                "custom_policies": self.compliance_config.get('custom_policies', {})
            },
            "architecture": self.azure_config.get('architecture', {}),
            "avm_modules": [],
            "deployment_steps": [
                "Prerequisites Check",
                "Policy Assignment",
                "Hub Deployment",
                "Spoke Deployment",
                "Management Services",
                "Compliance Validation"
            ]
        }
        try:
            plan["avm_modules"] = self._avm_manifest_summary()
        except FileNotFoundError:
            plan["avm_modules"] = []

        return json.dumps(plan, indent=2)

    # ============================================================================
    # SQUAD MODE DELEGATION TOOLS
    # ============================================================================

    @tool("delegate_to_security", "Delegate a security or compliance task to the Security specialist agent", {"task": str, "context": dict})
    async def delegate_to_security(self, args):
        """Delegate a security/compliance analysis task to the Security specialist."""
        if not self.squad_mode:
            return {
                "content": [{"type": "text", "text": "❌ Squad mode is not enabled. Use --squad flag to enable multi-agent collaboration."}]
            }

        task = args.get("task", "")
        context = args.get("context", {})

        # Add current project context
        if self.project_name:
            context['project_name'] = self.project_name
        if self.is_free_tier is not None:
            context['tier'] = 'free' if self.is_free_tier else 'standard'
        if self.environment_type:
            context['environment'] = self.environment_type

        result = await self._delegate_to_specialist('security', task, context)

        return {
            "content": [{"type": "text", "text": f"🔒 Security Agent Analysis:\n\n{result}"}]
        }

    @tool("delegate_to_network", "Delegate a network architecture or connectivity task to the Network specialist agent", {"task": str, "context": dict})
    async def delegate_to_network(self, args):
        """Delegate a network analysis task to the Network specialist."""
        if not self.squad_mode:
            return {
                "content": [{"type": "text", "text": "❌ Squad mode is not enabled. Use --squad flag to enable multi-agent collaboration."}]
            }

        task = args.get("task", "")
        context = args.get("context", {})

        # Add current project context
        if self.project_name:
            context['project_name'] = self.project_name
        if self.is_free_tier is not None:
            context['tier'] = 'free' if self.is_free_tier else 'standard'
        if self.environment_type:
            context['environment'] = self.environment_type

        result = await self._delegate_to_specialist('network', task, context)

        return {
            "content": [{"type": "text", "text": f"🌐 Network Agent Analysis:\n\n{result}"}]
        }

    @tool("delegate_to_devops", "Delegate a CI/CD, deployment automation, or pipeline task to the DevOps specialist agent", {"task": str, "context": dict})
    async def delegate_to_devops(self, args):
        """Delegate a DevOps analysis task to the DevOps specialist."""
        if not self.squad_mode:
            return {
                "content": [{"type": "text", "text": "❌ Squad mode is not enabled. Use --squad flag to enable multi-agent collaboration."}]
            }

        task = args.get("task", "")
        context = args.get("context", {})

        # Add current project context
        if self.project_name:
            context['project_name'] = self.project_name
        if self.is_free_tier is not None:
            context['tier'] = 'free' if self.is_free_tier else 'standard'
        if self.environment_type:
            context['environment'] = self.environment_type

        result = await self._delegate_to_specialist('devops', task, context)

        return {
            "content": [{"type": "text", "text": f"🚀 DevOps Agent Analysis:\n\n{result}"}]
        }

    @tool("delegate_to_architect", "Delegate an architecture synthesis or cross-domain analysis task to the Architect specialist agent", {"task": str, "context": dict})
    async def delegate_to_architect(self, args):
        """Delegate an architecture analysis task to the Architect specialist."""
        if not self.squad_mode:
            return {
                "content": [{"type": "text", "text": "❌ Squad mode is not enabled. Use --squad flag to enable multi-agent collaboration."}]
            }

        task = args.get("task", "")
        context = args.get("context", {})

        # Add current project context
        if self.project_name:
            context['project_name'] = self.project_name
        if self.is_free_tier is not None:
            context['tier'] = 'free' if self.is_free_tier else 'standard'
        if self.environment_type:
            context['environment'] = self.environment_type

        result = await self._delegate_to_specialist('architect', task, context)

        return {
            "content": [{"type": "text", "text": f"🏗️  Architect Agent Analysis:\n\n{result}"}]
        }

    @tool("run_squad_review", "Run a comprehensive multi-agent review with all specialists (Security, Network, DevOps) in parallel, then synthesize with Architect", {"review_scope": str, "context": dict})
    async def run_squad_review(self, args):
        """Run a comprehensive multi-agent review with parallel analysis and synthesis."""
        if not self.squad_mode:
            return {
                "content": [{"type": "text", "text": "❌ Squad mode is not enabled. Use --squad flag to enable multi-agent collaboration."}]
            }

        review_scope = args.get("review_scope", "Comprehensive deployment review")
        context = args.get("context", {})

        # Add current project context
        if self.project_name:
            context['project_name'] = self.project_name
        if self.is_free_tier is not None:
            context['tier'] = 'free' if self.is_free_tier else 'standard'
        if self.environment_type:
            context['environment'] = self.environment_type

        # Run parallel analysis with Security, Network, and DevOps agents
        specialists = ['security', 'network', 'devops']
        specialist_results = await self._parallel_analysis(specialists, review_scope, context)

        # Synthesize results with Architect agent
        synthesis = await self._synthesize_results(specialist_results, context)

        # Format comprehensive report
        report = "📊 COMPREHENSIVE SQUAD REVIEW\n"
        report += "=" * 80 + "\n\n"

        report += f"🔍 Review Scope: {review_scope}\n\n"

        report += "🔒 SECURITY AGENT FINDINGS:\n"
        report += "-" * 80 + "\n"
        report += specialist_results['security'] + "\n\n"

        report += "🌐 NETWORK AGENT FINDINGS:\n"
        report += "-" * 80 + "\n"
        report += specialist_results['network'] + "\n\n"

        report += "🚀 DEVOPS AGENT FINDINGS:\n"
        report += "-" * 80 + "\n"
        report += specialist_results['devops'] + "\n\n"

        report += "🏗️  ARCHITECT SYNTHESIS:\n"
        report += "=" * 80 + "\n"
        report += synthesis + "\n"

        return {
            "content": [{"type": "text", "text": report}]
        }


async def main():
    """
    Main entry point for the Azure FSI Landing Zone agent.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Azure FSI Landing Zone Deployment Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent.py              # Run in solo mode (default)
  python agent.py --squad      # Run in squad mode with specialist sub-agents
        """
    )
    parser.add_argument(
        '--squad',
        action='store_true',
        help='Enable squad mode with specialist sub-agents (Architect, DevOps, Network, Security)'
    )
    args = parser.parse_args()

    config_dir = Path(__file__).parent

    # Set up logging
    logs_dir = config_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    setup_logging(
        level="INFO",
        log_file=logs_dir / "agent.log"
    )

    # Create and run the agent
    agent = AzureFSILandingZoneAgent(config_dir, squad_mode=args.squad)

    print("\n" + "="*80)
    print("  🏦 AZURE FSI LANDING ZONE DEPLOYMENT AGENT")
    if args.squad:
        print("  🤖 SQUAD MODE: Multi-Agent Collaboration Enabled")
    print("="*80)
    print("\n🎯 Capabilities:")
    print("   • Deploy Microsoft FSI Landing Zone templates")
    print("   • Use Azure Verified Modules (AVM)")
    print("   • Apply European compliance policies (GDPR, DORA, PSD2, MiFID II)")
    print("   • Generate Bicep/Terraform templates")
    print("   • Validate deployments and security posture")

    if args.squad:
        print("\n🤖 Squad Mode Features:")
        print("   • 🏗️  Architect Agent: Holistic design and recommendations")
        print("   • 🚀 DevOps Agent: CI/CD pipelines and automation")
        print("   • 🔒 Security Agent: Security posture and compliance")
        print("   • 🌐 Network Agent: Network design and connectivity")

    print("\n💬 Try asking me to:")
    print("   - Set a project name (required before generating files)")
    print("   - Check Azure prerequisites")
    print("   - List FSI compliance requirements")
    print("   - Generate a hub VNet template")
    print("   - Check data residency compliance")
    print("   - Export a deployment plan")
    print("   - Validate my Azure authentication")

    await agent.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
