"""
Validator specialist agent responsible for linting Bicep templates.

This agent runs locally without calling the Claude API – it simply inspects the
workspace for Bicep files, applies the lightweight lint fixes, and reports the
outcome back to the orchestrator.
"""

from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator, Dict, Optional

from claude_agent_sdk import AssistantMessage, TextBlock

from shared.utils.bicep_linter import lint_bicep_targets, format_lint_report
from shared.utils.logging import get_logger
from ..base import BaseSpecialistAgent


class ValidatorSpecialistAgent:
    """Minimal specialist that provides linting support in squad mode."""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        # Orchestrator directory is two levels up: .../azure-fsi-landingzone
        self.orchestrator_root = config_dir.parent.parent
        self.logger = get_logger(self.__class__.__name__)

    async def connect(self) -> None:  # noqa: D401 - interface compatibility
        """No-op connect for compatibility with other agents."""
        self.logger.debug("Validator specialist ready (no remote connection required)")

    async def disconnect(self) -> None:  # noqa: D401
        """No-op disconnect for compatibility."""
        self.logger.debug("Validator specialist cleanup complete")

    async def query(self, prompt: str) -> AsyncIterator[AssistantMessage]:
        """
        Respond to orchestrator requests.

        The orchestrator sends prompts in the form:

        ```
        Context:
        { ...json... }

        Task: <description>
        ```
        """
        context, task = BaseSpecialistAgent._extract_context(prompt)
        project_path = self._resolve_project_path(context)

        if not project_path:
            summary = (
                "❌ Validator could not locate a project directory.\n"
                "Please set a project name (set_project_name) before requesting lint checks."
            )
            yield AssistantMessage(
                content=[TextBlock(summary)],
                model="validator.local",
            )
            return

        results = lint_bicep_targets([project_path])
        report = format_lint_report(results)

        summary_lines = [
            "🧪 Validator Agent Lint Report",
            f"📁 Scope: {project_path}",
            f"📝 Task: {task}" if task else "📝 Task: Run Bicep linter",
            "",
            report,
        ]

        yield AssistantMessage(
            content=[TextBlock("\n".join(summary_lines))],
            model="validator.local",
        )

    # ------------------------------------------------------------------#
    # Helper methods
    # ------------------------------------------------------------------#

    def _resolve_project_path(self, context: Dict[str, object]) -> Optional[Path]:
        """Determine which directory should be linted."""
        path_value = context.get("project_path")
        if isinstance(path_value, str):
            candidate = Path(path_value).expanduser()
            if candidate.exists():
                return candidate

        project_name = context.get("project_name")
        if isinstance(project_name, str):
            candidate = (self.orchestrator_root / project_name).resolve()
            if candidate.exists():
                return candidate

        return None
