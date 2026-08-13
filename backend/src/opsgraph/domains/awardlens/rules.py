"""Hash-verified AwardLens rule loading."""

import json
from hashlib import sha256
from pathlib import Path

from opsgraph.domains.awardlens.models import AwardRuleSet


class RuleIntegrityError(ValueError):
    """Raised when a rule file does not match its reviewed manifest."""


def load_rule_set(rule_path: Path, manifest_path: Path) -> AwardRuleSet:
    # Hash canonical UTF-8/LF content so reviewed rules survive Git checkouts on
    # Windows (CRLF) and Linux (LF) without weakening the integrity check.
    rule_text = rule_path.read_text(encoding="utf-8")
    payload = rule_text.encode("utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next(
        (item for item in manifest["rule_files"] if item["path"] == rule_path.name),
        None,
    )
    if entry is None:
        raise RuleIntegrityError(f"rule file is not in the source manifest: {rule_path.name}")
    if sha256(payload).hexdigest() != entry["sha256"]:
        raise RuleIntegrityError(f"rule file hash mismatch: {rule_path.name}")
    document = json.loads(rule_text)
    if document["verification_status"] != entry["verification_status"]:
        raise RuleIntegrityError("rule verification status differs from manifest")
    return AwardRuleSet.model_validate(document)
