from enum import StrEnum


class ActorType(StrEnum):
    COUNTRY = "country"
    GOVERNMENT = "government"
    MINISTRY = "ministry"
    MILITARY = "military"
    INTELLIGENCE_SERVICE = "intelligence_service"
    POLITICAL_PARTY = "political_party"
    ARMED_GROUP = "armed_group"
    INTERNATIONAL_ORGANIZATION = "international_organization"
    COMPANY = "company"
    RELIGIOUS_INSTITUTION = "religious_institution"
    TRIBAL_ORGANIZATION = "tribal_organization"
    MEDIA_ORGANIZATION = "media_organization"
    INDIVIDUAL = "individual"
    INFORMAL_NETWORK = "informal_network"


class LifecycleStatus(StrEnum):
    OBSERVED = "observed"
    EXTRACTED = "extracted"
    ASSESSED = "assessed"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class VerificationStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    UNSUPPORTED = "unsupported"
    SINGLE_SOURCE = "single_source"
    PARTIALLY_CORROBORATED = "partially_corroborated"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    CONTRADICTED = "contradicted"
    FALSE = "false"
    UNVERIFIABLE = "unverifiable"


class EvidenceStance(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    PARTIALLY_SUPPORTS = "partially_supports"
    CONTEXTUALIZES = "contextualizes"
    REPEATS = "repeats"
