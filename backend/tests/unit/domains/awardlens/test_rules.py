from pathlib import Path

from opsgraph.domains.awardlens.rules import load_rule_set


PROJECT_ROOT = Path(__file__).resolve().parents[5]


def test_rule_integrity_is_stable_across_line_endings(tmp_path: Path) -> None:
    source_dir = PROJECT_ROOT / "data" / "awardlens" / "rules"
    rule_path = tmp_path / "retail-level-1-2026.json"
    manifest_path = tmp_path / "source-manifest.json"
    normalized = (source_dir / rule_path.name).read_text(encoding="utf-8")
    rule_path.write_bytes(normalized.replace("\n", "\r\n").encode("utf-8"))
    manifest_path.write_text(
        (source_dir / manifest_path.name).read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    rules = load_rule_set(rule_path, manifest_path)

    assert rules.version == "2026.07.01"
