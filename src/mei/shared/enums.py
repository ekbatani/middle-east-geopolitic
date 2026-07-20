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


class ActorStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEFUNCT = "defunct"
    MERGED = "merged"


class SourceType(StrEnum):
    NEWS_OUTLET = "news_outlet"
    WIRE_SERVICE = "wire_service"
    GOVERNMENT = "government"
    THINK_TANK = "think_tank"
    NGO = "ngo"
    ACADEMIC = "academic"
    SOCIAL_MEDIA = "social_media"
    OTHER = "other"


class EndpointType(StrEnum):
    RSS = "rss"
    HTML = "html"
    API = "api"
    MANUAL = "manual"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    FETCHED = "fetched"
    PARSED = "parsed"
    FAILED = "failed"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class RoleName(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    APPROVER = "approver"
    READ_ONLY = "read_only"


class Scope(StrEnum):
    INTELLIGENCE_READ = "intelligence:read"
    SOURCES_SUBMIT = "sources:submit"
    CLAIMS_CREATE = "claims:create"
    CLAIMS_ASSESS = "claims:assess"
    EVENTS_CREATE = "events:create"
    EVENTS_APPROVE = "events:approve"
    INVESTIGATIONS_CREATE = "investigations:create"
    INVESTIGATIONS_READ = "investigations:read"
    RELATIONSHIPS_ASSESS = "relationships:assess"
    RISKS_RECALCULATE = "risks:recalculate"
    SCENARIOS_SIMULATE = "scenarios:simulate"
    REPORTS_GENERATE = "reports:generate"
    REPORTS_APPROVE = "reports:approve"
    MONITORS_MANAGE = "monitors:manage"
    ADMIN_CONFIGURATION = "admin:configuration"


class AuditActorType(StrEnum):
    USER = "user"
    API_KEY = "api_key"
    SYSTEM = "system"
