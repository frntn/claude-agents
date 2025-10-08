"""
Cloud PMO / project governance specialist for Azure FSI Landing Zone squad mode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..base import BaseSpecialistAgent, SpecialistMetadata


class CloudPmoSpecialistAgent(BaseSpecialistAgent):
    """Project governance specialist ensuring coordination and delivery cadence."""

    def __init__(self, config_dir: Path):
        super().__init__(
            config_dir,
            SpecialistMetadata(
                icon="🧭",
                role_name="Cloud PMO / Project Manager",
                certification="Microsoft Certified: Security, Compliance, and Identity Fundamentals (SC-900)",
                focus_areas=[
                    "Program governance, RACI, and cadence for landing zone rollout",
                    "Risk management and dependency tracking across specialist teams",
                    "Stakeholder communication (executive updates, compliance audits)",
                    "Adoption readiness: training, change management, and support models",
                ],
            ),
        )

    def _role_specific_guidance(self, task: str, context: Dict[str, object]) -> List[str]:
        recommendations: List[str] = []

        if task:
            recommendations.append(f"• Requested focus: {task}")

        environment = context.get("environment", "unspecified")
        ring = context.get("ring")

        recommendations.append("• Maintain a delivery roadmap with milestones for each ring and specialist owner.")
        if ring:
            recommendations.append(f"• Track dependency closure for {ring} before moving to downstream rings.")
        else:
            recommendations.append("• Ensure gating criteria (documentation, sign-offs) between rings are defined.")

        recommendations.append("• Schedule squad syncs covering architecture, security, network, DevOps, and FinOps updates.")
        recommendations.append("• Keep compliance stakeholders informed with consolidated status dashboards.")

        if environment == "prod":
            recommendations.append("• Align go-live with change advisory board (CAB) processes and incident response rehearsals.")

        recommendations.append("• Capture lessons learned and feed into continuous improvement backlog.")

        return recommendations
