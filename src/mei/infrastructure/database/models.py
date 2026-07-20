"""Import every domain model module so it registers on `Base.metadata`.

Alembic autogenerate, `Base.metadata.create_all` in tests, and any code that
needs the full mapper graph configured (cross-module foreign keys resolve by
table name, not import order) should import this module rather than
individual domain packages.
"""

from mei.domain.actors import models as actors_models
from mei.domain.audit import models as audit_models
from mei.domain.claims import models as claims_models
from mei.domain.documents import models as documents_models
from mei.domain.events import models as events_models
from mei.domain.evidence import models as evidence_models
from mei.domain.identity import models as identity_models
from mei.domain.sources import models as sources_models

__all__ = [
    "actors_models",
    "audit_models",
    "claims_models",
    "documents_models",
    "events_models",
    "evidence_models",
    "identity_models",
    "sources_models",
]
