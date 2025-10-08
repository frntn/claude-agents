"""
Architect specialist agent for Azure FSI Landing Zone squad mode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..base import BaseSpecialistAgent, SpecialistMetadata


class ArchitectSpecialistAgent(BaseSpecialistAgent):
    """Cloud Architect Lead focusing on overall landing zone design."""

    def __init__(self, config_dir: Path):
        super().__init__(
            config_dir,
            SpecialistMetadata(
                icon="🏗️",
                role_name="Cloud Architect Lead",
                certification="Microsoft Certified: Azure Solutions Architect Expert",
                focus_areas=[
                    "Multi-subscription/multi-tenant landing zone architecture",
                    "Secure hub-spoke network topologies and region strategy",
                    "Regulatory alignment for European financial services",
                    "Integration of specialist outputs into a cohesive roadmap",
                ],
            ),
        )

    def _role_specific_guidance(self, task: str, context: Dict[str, object]) -> List[str]:
        recommendations: List[str] = []

        if task:
            recommendations.append(f"• Requested focus: {task}")

        environment = context.get("environment", "unspecified")
        tier = context.get("tier", "standard")
        ring = context.get("ring")

        recommendations.append(f"• Validate that the chosen deployment strategy fits the {environment} environment.")
        if tier == "free":
            recommendations.append("• Apply Free Tier guardrails (basic SKUs, consumption-based services, avoid Premium tiers).")
        else:
            recommendations.append("• Consider premium services (Azure Firewall Premium, P2 PIM) for production readiness.")

        if ring:
            recommendations.append(f"• Confirm dependencies for {ring} are satisfied and documentation is up to date.")
        else:
            recommendations.append("• Ensure ring sequencing (Ring 0 → Ring 1 → Ring 2) aligns with rollout timeline.")

        recommendations.append("• Consolidate specialist findings into an execution roadmap with milestones and owners.")
        recommendations.append("• Highlight any cross-domain risks (network/security/finops) and propose mitigation actions.")

        return recommendations
