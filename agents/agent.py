"""
ADK discovery entry point.

Run from the repository root with:

    adk run agents

or:

    adk web .
"""

from agents.workflows.healthcare_workflow import root_agent

__all__ = ["root_agent"]
