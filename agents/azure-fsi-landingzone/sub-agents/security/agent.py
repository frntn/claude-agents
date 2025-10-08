"""
Security specialist agent for Azure FSI Landing Zone squad mode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..base import BaseSpecialistAgent, SpecialistMetadata


class SecuritySpecialistAgent(BaseSpecialistAgent):
    """Security engineer covering guardrails, compliance, and IAM."""

    def __init__(self, config_dir: Path):
        super().__init__(
            config_dir,
            SpecialistMetadata(
                icon="🔒",
                role_name="Security & IAM Engineer",
                certification="Azure Security Engineer Associate (AZ-500)",
                focus_areas=[
                    "Guardrail policies (Azure Policy, custom initiatives)",
                    "Identity governance (PIM, conditional access, MFA enforcement)",
                    "Threat protection (Defender for Cloud, Sentinel integration)",
                    "Compliance evidence for GDPR, DORA, PSD2, ISO 27001",
                ],
            ),
        )

    def _role_specific_guidance(self, task: str, context: Dict[str, object]) -> List[str]:
        recommendations: List[str] = []

        if task:
            recommendations.append(f"• Requested focus: {task}")

        environment = context.get("environment", "unspecified")
        ring = context.get("ring")

        recommendations.append("• Validate Azure Policy assignments cover data residency, encryption, and logging.")
        recommendations.append("• Ensure PIM roles are enabled with approval workflows and MFA for privileged access.")

        if environment in {"prod", "staging"}:
            recommendations.append("• Confirm Defender for Cloud is running in Standard tier across all subscriptions.")
            recommendations.append("• Review incident response playbooks and SOC escalation paths.")
        else:
            recommendations.append("• Apply reduced retention/monitoring for non-production while keeping auditability.")

        if ring == "ring0_foundation":
            recommendations.append("• Re-check baseline guardrails (Key Vault, Azure Firewall, Bastion) for CIS benchmark alignment.")

        recommendations.append("• Provide compliance evidence matrix linking deployed controls to regulatory requirements.")

        return recommendations
