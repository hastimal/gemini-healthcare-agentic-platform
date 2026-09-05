from __future__ import annotations

from models.citations import Citation
from models.evidence import Evidence
from models.search import SourceType


class CitationBuilder:
    """
    Build citations deterministically from selected evidence.

    Gemini is intentionally NOT responsible for creating:

    - citation IDs
    - URLs
    - source names

    This prevents fabricated citations and gives us stable,
    traceable references for grounded answer generation.
    """

    def build(
        self,
        evidence_items: list[Evidence],
    ) -> list[Citation]:
        """
        Create one citation for every selected evidence item.

        Citation IDs are stable within the answer:

            C1
            C2
            C3
            ...

        Only evidence marked `selected=True` is exposed to the
        downstream answer generator.
        """

        selected = [evidence for evidence in evidence_items if evidence.selected]

        citations: list[Citation] = []

        for index, evidence in enumerate(
            selected,
            start=1,
        ):
            result = evidence.result

            citations.append(
                Citation(
                    citation_id=f"C{index}",
                    title=result.title,
                    url=result.url,
                    source_name=self._source_name(evidence),
                    claim_supported=(self._claim_supported(evidence)),
                )
            )

        return citations

    @staticmethod
    def _source_name(
        evidence: Evidence,
    ) -> str:
        """
        Return a human-readable source name.
        """

        source_names = {
            SourceType.PROVIDER: ("CMS NPPES / NPI Registry"),
            SourceType.PUBMED: "PubMed",
            SourceType.CMS: "CMS",
            SourceType.CLINICAL_TRIAL: ("ClinicalTrials.gov"),
            SourceType.FHIR: "FHIR",
            SourceType.WEB: "Web",
        }

        return source_names.get(
            evidence.result.source_type,
            evidence.result.source_type.value,
        )

    @staticmethod
    def _claim_supported(
        evidence: Evidence,
    ) -> str:
        """
        Describe the kind of claim this evidence can safely support.

        We intentionally avoid converting source presence into claims
        of provider quality or clinical superiority.
        """

        result = evidence.result

        if result.source_type == SourceType.PROVIDER:
            return (
                "Supports provider identity, reported location, "
                "NPI, and specialty/taxonomy information present "
                "in the provider registry."
            )

        if result.source_type == SourceType.PUBMED:
            return (
                "Supports general scientific context described in the indexed biomedical article."
            )

        return "Supports factual information contained in the retrieved source."


def citation_map(
    citations: list[Citation],
) -> dict[str, Citation]:
    """
    Convenience helper for mapping C1 -> Citation.
    """

    return {citation.citation_id: citation for citation in citations}
