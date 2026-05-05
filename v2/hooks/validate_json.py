#!/usr/bin/env python3
"""Validate knowledge base JSON files."""

import json
import re
import sys
from pathlib import Path

VALID_STATUSES = {"draft", "review", "published", "archived"}
VALID_AUDIENCES = {"beginner", "intermediate", "advanced"}
REQUIRED_FIELDS = {
    "id": str,
    "title": str,
    "source_url": str,
    "summary": str,
    "tags": list,
    "status": str,
}
ID_PATTERN = re.compile(r"^[a-z_]+-\d{8}-\d{3}$")
URL_PATTERN = re.compile(r"^https?://")


def validate_file(path: Path) -> list[str]:
    errors = []

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return [f"JSON parse error: {e}"]

    if not isinstance(data, dict):
        return ["Root must be a JSON object"]

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(
                f"Field '{field}' must be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )

    if "id" in data and isinstance(data["id"], str):
        if not ID_PATTERN.match(data["id"]):
            errors.append(
                f"ID '{data['id']}' must match format {{source}}-{{YYYYMMDD}}-{{NNN}}"
            )

    if "status" in data and isinstance(data["status"], str):
        if data["status"] not in VALID_STATUSES:
            errors.append(
                f"status must be one of {sorted(VALID_STATUSES)}, got '{data['status']}'"
            )

    if "source_url" in data and isinstance(data["source_url"], str):
        if not URL_PATTERN.match(data["source_url"]):
            errors.append(f"source_url must start with http:// or https://: {data['source_url']}")

    if "summary" in data and isinstance(data["summary"], str):
        if len(data["summary"]) < 20:
            errors.append(f"summary must be at least 20 characters, got {len(data['summary'])}")

    if "tags" in data and isinstance(data["tags"], list):
        if len(data["tags"]) < 1:
            errors.append("tags must have at least 1 element")
        elif not all(isinstance(t, str) for t in data["tags"]):
            errors.append("All tags must be strings")

    if "score" in data and isinstance(data["score"], (int, float)):
        if not 1 <= data["score"] <= 10:
            errors.append(f"score must be between 1 and 10, got {data['score']}")

    if "audience" in data and isinstance(data["audience"], str):
        if data["audience"] not in VALID_AUDIENCES:
            errors.append(
                f"audience must be one of {sorted(VALID_AUDIENCES)}, got '{data['audience']}'"
            )

    return errors


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python hooks/validate_json.py <json_file> [json_file2 ...]")
        sys.exit(1)

    files: list[Path] = []
    for arg in sys.argv[1:]:
        paths = Path(".").glob(arg)
        files.extend(sorted(paths))

    if not files:
        print(f"No files found for pattern: {sys.argv[1:]}")
        sys.exit(1)

    total_errors = 0
    for path in files:
        errors = validate_file(path)
        if errors:
            total_errors += len(errors)
            print(f"\n[FAIL] {path}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"[PASS] {path}")

    print(f"\n{'='*50}")
    print(f"Total: {len(files)} files, {total_errors} errors")

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()