"""Shared vocabulary for distinguishing assumptions from observations."""

from enum import StrEnum


class EvidenceCategory(StrEnum):
    """Evidence labels used throughout the executable textbook."""

    MODELED_ASSUMPTION = "MODELED ASSUMPTION"
    OBSERVED_LAB_RESULT = "OBSERVED LAB RESULT"
    OBSERVED_IMPLEMENTATION_STRUCTURE = "OBSERVED IMPLEMENTATION STRUCTURE"
    SENSITIVITY_ASSUMPTION = "SENSITIVITY ASSUMPTION"
    MODELED_ALTERNATIVE_ASSUMPTION = "MODELED ALTERNATIVE ASSUMPTION"


EVIDENCE_DEFINITIONS: dict[EvidenceCategory, str] = {
    EvidenceCategory.MODELED_ASSUMPTION:
        "A fictional economic, effort, pricing, or support number.",
    EvidenceCategory.OBSERVED_LAB_RESULT:
        "Behavior actually demonstrated by the executable synthetic system.",
    EvidenceCategory.OBSERVED_IMPLEMENTATION_STRUCTURE: (
        "Repository evidence such as adapters, mappings, transitions, tests, "
        "exceptions, jobs, and reliability mechanisms. It is not automatically "
        "human-hours evidence."
    ),
    EvidenceCategory.SENSITIVITY_ASSUMPTION:
        "A hypothetical changed value used to test economics.",
    EvidenceCategory.MODELED_ALTERNATIVE_ASSUMPTION: (
        "An unverified capability or price attributed to a hypothetical SaaS alternative."
    ),
}
