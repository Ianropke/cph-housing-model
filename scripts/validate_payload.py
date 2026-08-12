#!/usr/bin/env python3
"""Validate a generated dashboard payload and fail closed on any error."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from payload_validation import validate_pipeline_payload


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dashboard/public/data/latest_pipeline.json")
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        print(f"Payload validation failed: {error}", file=sys.stderr)
        return 1

    errors = validate_pipeline_payload(payload)
    if errors:
        print("Payload validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"Payload valid: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
