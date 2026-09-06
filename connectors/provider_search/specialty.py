from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedNPPESSpecialty:
    """NPPES-facing representation of a planner/user specialty."""

    original: str
    search_term: str
    match_terms: tuple[str, ...]


class NPPESSpecialtyResolver:
    """
    Resolve healthcare specialty wording for NPPES search and validation.

    Unknown specialties pass through unchanged. Aliases are intentionally
    limited to common wording differences between user language and NPPES
    taxonomy descriptions; this is not a supported-specialty allowlist.
    """

    _ALIASES: dict[str, tuple[str, tuple[str, ...]]] = {
        "cardiology": (
            "Cardiovascular Disease",
            ("cardiovascular disease", "cardiology"),
        ),
        "cardiologist": (
            "Cardiovascular Disease",
            ("cardiovascular disease", "cardiology"),
        ),
        "cardiologists": (
            "Cardiovascular Disease",
            ("cardiovascular disease", "cardiology"),
        ),
        "neurologist": ("Neurology", ("neurology",)),
        "neurologists": ("Neurology", ("neurology",)),
        "dermatologist": ("Dermatology", ("dermatology",)),
        "dermatologists": ("Dermatology", ("dermatology",)),
        "pediatric dentist": (
            "Pediatric Dentistry",
            ("pediatric dentistry",),
        ),
        "pediatric dentists": (
            "Pediatric Dentistry",
            ("pediatric dentistry",),
        ),
    }

    def resolve(self, specialty: str) -> ResolvedNPPESSpecialty:
        cleaned = " ".join(specialty.strip().split())
        if not cleaned:
            raise ValueError("Provider specialty must not be empty.")

        key = self._normalize(cleaned)
        alias = self._ALIASES.get(key)
        if alias is not None:
            search_term, match_terms = alias
            return ResolvedNPPESSpecialty(
                original=cleaned,
                search_term=search_term,
                match_terms=match_terms,
            )

        return ResolvedNPPESSpecialty(
            original=cleaned,
            search_term=cleaned,
            match_terms=(self._normalize(cleaned),),
        )

    def best_matching_taxonomy(
        self,
        *,
        requested_specialty: str,
        taxonomies: list[dict],
    ) -> dict | None:
        resolved = self.resolve(requested_specialty)

        for taxonomy in taxonomies:
            description = str(taxonomy.get("desc") or "")
            if self._description_matches(
                description=description,
                match_terms=resolved.match_terms,
            ):
                return taxonomy

        return None

    def matches_any_description(
        self,
        *,
        requested_specialty: str,
        taxonomy_descriptions: str,
    ) -> bool:
        resolved = self.resolve(requested_specialty)

        return any(
            self._description_matches(
                description=description,
                match_terms=resolved.match_terms,
            )
            for description in taxonomy_descriptions.split("|")
        )

    @classmethod
    def _description_matches(
        cls,
        *,
        description: str,
        match_terms: tuple[str, ...],
    ) -> bool:
        normalized_description = cls._normalize(description)

        for term in match_terms:
            normalized_term = cls._normalize(term)
            if not normalized_term:
                continue

            if normalized_term in normalized_description:
                return True

            term_tokens = set(normalized_term.split())
            description_tokens = set(normalized_description.split())
            if term_tokens and term_tokens.issubset(description_tokens):
                return True

        return False

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", value.lower()))
