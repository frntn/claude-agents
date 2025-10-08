"""
Network specialist agent for Azure FSI Landing Zone squad mode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..base import BaseSpecialistAgent, SpecialistMetadata


class NetworkSpecialistAgent(BaseSpecialistAgent):
    """Network engineer focusing on connectivity and hybrid design."""

    def __init__(self, config_dir: Path):
        super().__init__(
            config_dir,
            SpecialistMetadata(
                icon="🌐",
                role_name="Hybrid Network Engineer",
                certification="Azure Network Engineer Associate (AZ-700)",
                focus_areas=[
                    "Hub-spoke and mesh connectivity patterns",
                    "Hybrid connectivity (VPN, ExpressRoute) and redundancy",
                    "Network segmentation (subnets, NSGs, Azure Firewall policies)",
                    "Performance and latency considerations for regulated workloads",
                ],
            ),
        )

    def _role_specific_guidance(self, task: str, context: Dict[str, object]) -> List[str]:
        recommendations: List[str] = []

        if task:
            recommendations.append(f"• Requested focus: {task}")

        tier = context.get("tier")
        environment = context.get("environment")

        if tier == "free":
            recommendations.append("• Confirm usage of VPN with SKU-compatible to Free Tier and avoid cost-heavy ExpressRoute.")
        else:
            recommendations.append("• Validate dual connectivity (VPN + ExpressRoute) for resiliency and compliance zones.")

        if environment in {"prod", "staging"}:
            recommendations.append("• Ensure Azure Firewall Premium policies cover TLS inspection and egress filtering.")
            recommendations.append("• Validate DNS forwarding and private endpoints for sensitive services.")
        else:
            recommendations.append("• Optimize non-production spokes to minimal subnets and disable unused gateways.")

        ring = context.get("ring")
        if ring == "ring0_foundation":
            recommendations.append("• Reconcile hub network address spaces against downstream spokes to avoid overlap.")

        recommendations.append("• Document network dependencies for each ring to support orchestrated deployments.")

        return recommendations
