"""
Model-neutral synthesis contract.
"""

from typing import Protocol, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class SynthesisClient(Protocol):
    """Generate a structured response from a grounded prompt."""

    async def generate(
        self,
        *,
        prompt: str,
        schema: type[SchemaT],
    ) -> SchemaT:
        ...
