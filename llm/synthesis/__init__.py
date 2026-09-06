"""
Provider-neutral grounded-answer synthesis.

v0.8 allows the grounding pipeline to use the same configured model
provider as the Google ADK agents.
"""

from llm.synthesis.factory import get_synthesis_client

__all__ = ["get_synthesis_client"]
