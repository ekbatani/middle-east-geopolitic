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


class ReviewType(StrEnum):
    ENTITY_RESOLUTION = "entity_resolution"
    EVENT_DUPLICATE = "event_duplicate"
    HIGH_IMPACT_EVENT = "high_impact_event"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


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
    REVIEW_RESOLVE = "review:resolve"
    ANALYST_ASSESSMENTS_RECORD = "analyst_assessments:record"
    IMAGERY_SUBMIT = "imagery:submit"


class AuditActorType(StrEnum):
    USER = "user"
    API_KEY = "api_key"
    SYSTEM = "system"


class RelationshipStatus(StrEnum):
    ACTIVE = "active"
    DORMANT = "dormant"
    ENDED = "ended"


class RelationshipDirectionality(StrEnum):
    SYMMETRIC = "symmetric"
    SOURCE_TO_TARGET = "source_to_target"
    TARGET_TO_SOURCE = "target_to_source"


class Trend(StrEnum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"


class ScopeType(StrEnum):
    """What a risk or indicator observation is measured against (design doc section 8.7)."""

    COUNTRY = "country"
    RELATIONSHIP = "relationship"
    ACTOR = "actor"
    CONFLICT = "conflict"
    GLOBAL = "global"


class IndicatorNormalizationMethod(StrEnum):
    """How `indicator_observations.raw_value` maps to a 0-1 `normalized_value`."""

    MIN_MAX = "min_max"
    BOOLEAN = "boolean"
    MANUAL = "manual"


class IndicatorDirection(StrEnum):
    """Whether a higher normalized indicator value raises or lowers the risk it feeds."""

    POSITIVE = "positive"
    INVERSE = "inverse"


class RiskApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ScenarioFamily(StrEnum):
    """The four scenario families a scope is tracked against (design doc section 19.1)."""

    CONTROLLED_DEESCALATION = "controlled_deescalation"
    MANAGED_CONFRONTATION = "managed_confrontation"
    REGIONAL_ESCALATION = "regional_escalation"
    SYSTEMIC_REGIONAL_WAR = "systemic_regional_war"


class ScenarioStatus(StrEnum):
    ACTIVE = "active"
    INVALIDATED = "invalidated"
    ARCHIVED = "archived"


class ForecastStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    CANCELED = "canceled"


class ForecastOutcome(StrEnum):
    """Design doc section 8.9 `outcome` column. `AMBIGUOUS` resolves the
    forecast's status without a scorable Brier outcome (design doc section
    16.4-style unresolved-question handling applied to forecasts)."""

    YES = "yes"
    NO = "no"
    AMBIGUOUS = "ambiguous"


class ReportType(StrEnum):
    DAILY_BRIEF = "daily_brief"
    WEEKLY_OUTLOOK = "weekly_outlook"
    COUNTRY_BRIEF = "country_brief"
    CONFLICT_BRIEF = "conflict_brief"


class ReportStatus(StrEnum):
    GENERATED = "generated"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class DisagreementSubjectType(StrEnum):
    """What kind of record an `AnalystAssessment` records a position on (design doc section 35)."""

    CLAIM = "claim"
    EVENT = "event"
    RISK_ASSESSMENT = "risk_assessment"
    RELATIONSHIP_OBSERVATION = "relationship_observation"


class ModelReviewSubjectType(StrEnum):
    """What kind of record a `ModelReviewResult` shadow-reviewed (design doc section 35)."""

    RISK_ASSESSMENT = "risk_assessment"
