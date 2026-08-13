"""Verify signed evaluation output using only the Python standard library."""

import argparse
import json
from hashlib import sha256
from pathlib import Path


def verify_report(path: Path) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document["passed_cases"] != document["total_cases"]:
        raise SystemExit("evaluation contains failed cases")
    if document["release_failures"]:
        raise SystemExit("evaluation release gate failed")
    signature_path = path.with_suffix(path.suffix + ".sha256")
    expected = signature_path.read_text(encoding="utf-8").strip().split()[0]
    # JSON reports are signed as canonical UTF-8/LF text for cross-platform CI.
    actual = sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    if actual != expected:
        raise SystemExit("evaluation checksum mismatch")
    print(f"verified {document['passed_cases']}/{document['total_cases']} cases: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    verify_report(args.report)


if __name__ == "__main__":
    main()
