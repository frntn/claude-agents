"""
FinOps & governance specialist agent for Azure FSI Landing Zone squad mode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..base import BaseSpecialistAgent, SpecialistMetadata


class FinOpsSpecialistAgent(BaseSpecialistAgent):
    """Cloud governance specialist focusing on cost management and tagging."""

    def __init__(self, config_dir: Path):
        super().__init__(
            config_dir,
            SpecialistMetadata(
                icon="💰",
                role_name="Cloud Governance & FinOps Lead",
                certification="Azure Fundamentals (AZ-900) with Cost Management expertise",
                focus_areas=[
                    "Budgeting, forecasting, and real-time cost guardrails",
                    "Enterprise tagging/taxonomy enforcement for regulatory reporting",
                    "Chargeback/showback models aligned with business units and rings",
                    "Continuous optimization (reserved instances, savings plans, rightsizing)",
                ],
            ),
        )

    def _role_specific_guidance(self, task: str, context: Dict[str, object]) -> List[str]:
        recommendations: List[str] = []

        if task:
            recommendations.append(f"• Requested focus: {task}")

        tier = context.get("tier", "standard")
        environment = context.get("environment", "unspecified")

        recommendations.append("• Define budgets per ring and environment with alerting thresholds (50/75/90%).")
        recommendations.append("• Enforce tagging schema: costCenter, dataClassification, owner, environment, ring.")

        if tier == "free":
            recommendations.append("• Limit deployments to free-tier SKUs and configure automatic cleanup for idle resources.")
        else:
            recommendations.append("• Evaluate reserved capacity for long-running production workloads (SQL, App Service, VM).")

        if environment == "prod":
            recommendations.append("• Align cost reports with regulatory filings (stress testing, operational resilience).")
        else:
            recommendations.append("• Implement scheduling to shut down non-prod workloads outside business hours.")

        recommendations.append("• Provide quarterly optimization review integrating Security/Architect risk considerations.")

        return recommendations
