from connectors.provider_search.specialty import NPPESSpecialtyResolver


def test_cardiology_resolves_to_nppes_taxonomy_wording():
    resolver = NPPESSpecialtyResolver()
    resolved = resolver.resolve("Cardiology")

    assert resolved.search_term == "Cardiovascular Disease"
    assert "cardiovascular disease" in resolved.match_terms


def test_unknown_specialty_passes_through():
    resolver = NPPESSpecialtyResolver()
    resolved = resolver.resolve("Clinical Neurophysiology")

    assert resolved.search_term == "Clinical Neurophysiology"
    assert resolved.match_terms == ("clinical neurophysiology",)


def test_cardiology_matches_returned_nppes_description():
    resolver = NPPESSpecialtyResolver()

    assert resolver.matches_any_description(
        requested_specialty="Cardiology",
        taxonomy_descriptions=(
            "Internal Medicine | Internal Medicine, Cardiovascular Disease"
        ),
    )


def test_unrelated_taxonomy_is_rejected():
    resolver = NPPESSpecialtyResolver()

    assert not resolver.matches_any_description(
        requested_specialty="Cardiology",
        taxonomy_descriptions="Family Medicine | Internal Medicine",
    )


def test_requested_specialty_selects_matching_secondary_taxonomy():
    resolver = NPPESSpecialtyResolver()

    taxonomies = [
        {
            "desc": "Internal Medicine",
            "primary": True,
            "code": "207R00000X",
        },
        {
            "desc": "Internal Medicine, Cardiovascular Disease",
            "primary": False,
            "code": "207RC0000X",
        },
    ]

    selected = resolver.best_matching_taxonomy(
        requested_specialty="Cardiology",
        taxonomies=taxonomies,
    )

    assert selected is not None
    assert selected["code"] == "207RC0000X"


def test_pediatric_dentistry_uses_same_generic_selection_path():
    resolver = NPPESSpecialtyResolver()

    taxonomies = [
        {"desc": "Dentist, General Practice", "primary": True},
        {"desc": "Dentist, Pediatric Dentistry", "primary": False},
    ]

    selected = resolver.best_matching_taxonomy(
        requested_specialty="Pediatric Dentistry",
        taxonomies=taxonomies,
    )

    assert selected is not None
    assert selected["desc"] == "Dentist, Pediatric Dentistry"


def test_neurology_and_dermatology_match_generically():
    resolver = NPPESSpecialtyResolver()

    assert resolver.matches_any_description(
        requested_specialty="Neurology",
        taxonomy_descriptions="Psychiatry & Neurology, Neurology",
    )
    assert resolver.matches_any_description(
        requested_specialty="Dermatology",
        taxonomy_descriptions="Allopathic & Osteopathic Physicians, Dermatology",
    )
