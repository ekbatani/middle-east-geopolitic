from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]

# Versioned prompt files (design doc section 13.3 / repo layout section 5),
# keyed by the `(task_name, prompt_version)` a caller passes to
# `StructuredLLM.generate_structured`.
_PROMPT_FILES: dict[tuple[str, str], Path] = {
    ("claim_event_extraction", "claims_events_v1"): _REPO_ROOT
    / "prompts"
    / "extraction"
    / "claims_events_v1.md",
    ("risk_adjustment", "risk_adjustment_v1"): _REPO_ROOT
    / "prompts"
    / "risks"
    / "risk_adjustment_v1.md",
}


@lru_cache
def load_prompt(task_name: str, prompt_version: str) -> str:
    try:
        path = _PROMPT_FILES[(task_name, prompt_version)]
    except KeyError as exc:
        raise KeyError(f"No prompt registered for {task_name}/{prompt_version}") from exc
    return path.read_text(encoding="utf-8")


__all__ = ["load_prompt"]
