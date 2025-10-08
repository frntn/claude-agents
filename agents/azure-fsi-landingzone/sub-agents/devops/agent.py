"""
DevOps / IaC specialist agent for Azure FSI Landing Zone squad mode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..base import BaseSpecialistAgent, SpecialistMetadata


class DevOpsSpecialistAgent(BaseSpecialistAgent):
    """DevOps engineer focusing on automation, CI/CD, and infrastructure pipelines."""

    def __init__(self, config_dir: Path):
        super().__init__(
            config_dir,
            SpecialistMetadata(
                icon="🚀",
                role_name="DevOps / IaC Engineer",
                certification="Azure DevOps Engineer Expert (AZ-400)",
                focus_areas=[
                    "Infrastructure-as-code pipelines (Bicep, Terraform, GitHub Actions/Azure DevOps)",
                    "Environment promotion strategy with approvals and testing gates",
                    "Artifact management (Bicep registry, template versioning, compliance attestation)",
                    "Deployment validation (what-if, linting, automated quality checks)",
                ],
            ),
        )

    def _role_specific_guidance(self, task: str, context: Dict[str, object]) -> List[str]:
        recommendations: List[str] = []

        if task:
            recommendations.append(f"• Requested focus: {task}")

        environment = context.get("environment")
        tier = context.get("tier")

        recommendations.append("• Ensure run_bicep_linter is part of the CI pipeline before deployments.")
        recommendations.append("• Automate `az deployment sub what-if` for each ring to prevent drift.")

        if environment in {"prod"}:
            recommendations.append("• Require manual approvals and change control for production deployments.")
        else:
            recommendations.append("• Enable ephemeral environments for dev/test with automatic cleanup policies.")

        if tier == "free":
            recommendations.append("• Use GitHub Actions with consumption runners to stay within free tier quotas.")

        project_path = context.get("project_path")
        if project_path:
            recommendations.append(f"• Validate generated artifacts in `{project_path}` are version-controlled and signed off.")

        recommendations.append("• Maintain release notes and deployment dashboards for audit tracking (DORA compliance).")

        return recommendations
