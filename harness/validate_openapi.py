"""
validate_openapi.py — Validate openapi.yaml against the OpenAPI 3.0.3 specification.

Checks:
  1. File can be parsed as valid YAML.
  2. Document passes OpenAPIV30SpecValidator (structural / schema correctness).
  3. All 10 SOW-required operationIds are present.

Exit codes:
  0 — validation passed
  1 — one or more checks failed

Usage:
  python harness/validate_openapi.py
"""
import os
import sys

import yaml
from openapi_spec_validator import OpenAPIV30SpecValidator

SPEC_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "openapi.yaml")
)

REQUIRED_OPERATION_IDS = {
    "listMenu",
    "getMenuItem",
    "createCustomer",
    "listDiningTables",
    "createReservation",
    "getReservation",
    "createOrder",
    "getOrder",
    "updateOrderStatus",
    "listCustomerOrders",
}


def validate():
    print(f"Validating: {SPEC_PATH}")
    print()

    # ── 1. YAML syntax ─────────────────────────────────────────────────────────
    try:
        with open(SPEC_PATH, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        print("[PASS] YAML syntax: valid")
    except yaml.YAMLError as exc:
        print(f"[FAIL] YAML syntax error: {exc}")
        return False

    # ── 2. OpenAPI structural validation ───────────────────────────────────────
    errors = list(OpenAPIV30SpecValidator(spec).iter_errors())
    if errors:
        print(f"[FAIL] OpenAPI structure: {len(errors)} error(s)")
        for err in errors:
            print(f"       • {err.message}")
        return False
    print("[PASS] OpenAPI 3.0.3 structure: valid")

    # ── 3. operationId coverage ────────────────────────────────────────────────
    found = set()
    for path_item in spec.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "operationId" in operation:
                found.add(operation["operationId"])

    missing = REQUIRED_OPERATION_IDS - found
    extra   = found - REQUIRED_OPERATION_IDS

    if missing:
        print(f"[FAIL] Missing operationIds: {sorted(missing)}")
        return False
    print(f"[PASS] operationIds: all {len(REQUIRED_OPERATION_IDS)} required operations present")

    if extra:
        print(f"[WARN] Unexpected operationIds (not in SOW): {sorted(extra)}")

    print()
    print("VALIDATION PASSED")
    return True


if __name__ == "__main__":
    ok = validate()
    sys.exit(0 if ok else 1)
