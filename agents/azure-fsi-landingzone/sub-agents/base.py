"""
Common helpers for Azure FSI Landing Zone specialist agents.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional, Tuple

from claude_agent_sdk import AssistantMessage, TextBlock

from shared.utils.logging import get_logger


@dataclass
class SpecialistMetadata:
    icon: str
    role_name: str
    certification: str
    focus_areas: List[str]
    model_name: str = "specialist.local"


class BaseSpecialistAgent:
    """Lightweight specialist agent that returns deterministic guidance."""

    def __init__(self, config_dir: Path, metadata: SpecialistMetadata):
        self.config_dir = config_dir
        self.metadata = metadata
        self.logger = get_logger(self.__class__.__name__)

    # ------------------------------------------------------------------#
    # Lifecycle (no-op for local specialists)
    # ------------------------------------------------------------------#
    async def connect(self) -> None:  # noqa: D401 - interface compatibility
        """Specialists are local; nothing to connect."""
        self.logger.debug("%s ready", self.metadata.role_name)

    async def disconnect(self) -> None:  # noqa: D401
        """Specialists are local; nothing to disconnect."""
        self.logger.debug("%s shutdown complete", self.metadata.role_name)

    # ------------------------------------------------------------------#
    async def query(self, prompt: str) -> AsyncIterator[AssistantMessage]:
        """Process orchestrator prompt and stream a single assistant message."""
        context, task = self._extract_context(prompt)
        analysis = self._generate_report(task, context)

        yield AssistantMessage(
            content=[TextBlock(analysis)],
            model=self.metadata.model_name,
        )

    # ------------------------------------------------------------------#
    def _generate_report(self, task: str, context: Dict[str, object]) -> str:
        """Build the default report layout shared by specialists."""
        lines = [
            f"{self.metadata.icon} {self.metadata.role_name} Analysis",
            f"Certification Focus: {self.metadata.certification}",
        ]

        context_section = self._format_context(context)
        if context_section:
            lines.append("")
            lines.append("Context Summary:")
            lines.extend(context_section)

        lines.append("")
        lines.append("Core Focus Areas:")
        for area in self.metadata.focus_areas:
            lines.append(f"• {area}")

        guidance = self._role_specific_guidance(task, context)
        if guidance:
            lines.append("")
            lines.append("Recommendations:")
            lines.extend(guidance)

        return "\n".join(lines)

    # ------------------------------------------------------------------#
    @staticmethod
    def _extract_context(prompt: str) -> Tuple[Dict[str, object], str]:
        """Parse context JSON and task description from orchestrator prompt."""
        if not prompt.startswith("Context:"):
            return {}, prompt.strip()

        try:
            context_part, task_part = prompt.split("\n\nTask:", maxsplit=1)
        except ValueError:
            return {}, prompt.strip()

        context_json = context_part.replace("Context:\n", "", 1).strip()
        try:
            context = json.loads(context_json) if context_json else {}
        except json.JSONDecodeError:
            context = {}

        task = task_part.strip()
        return context, task

    @staticmethod
    def _format_context(context: Dict[str, object]) -> List[str]:
        """Convert context dictionary into human-readable lines."""
        if not context:
            return []

        lines: List[str] = []
        mapping = {
            "project_name": "Project",
            "project_path": "Project Path",
            "tier": "Subscription Tier",
            "environment": "Environment",
            "ring": "Ring",
            "deployment_scope": "Deployment Scope",
        }

        for key, label in mapping.items():
            value = context.get(key)
            if value:
                lines.append(f"• {label}: {value}")

        extras = {k: v for k, v in context.items() if k not in mapping}
        if extras:
            lines.append(f"• Additional context: {json.dumps(extras, ensure_ascii=False)}")

        return lines

    # ------------------------------------------------------------------#
    def _role_specific_guidance(self, task: str, context: Dict[str, object]) -> List[str]:
        """Override in subclasses to provide tailored recommendations."""
        raise NotImplementedError
