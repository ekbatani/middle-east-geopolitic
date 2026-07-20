"""Idempotent seed-data loader.

Empty for now: seed content (countries, external powers, organizations,
aliases, event types, risk definitions, indicators, report templates,
source registry) lands with the domain models in Phase 1, driven by the
YAML files under configs/.
"""

from mei.shared.logging import configure_logging, get_logger

configure_logging(json_output=False)
logger = get_logger(__name__)


def main() -> None:
    logger.info("seed.not_implemented")


if __name__ == "__main__":
    main()
