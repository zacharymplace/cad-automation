"""Explicit acceptance rules layered over validation evidence."""

import json


def load_policy(path=None, *, required_checks=(), fail_on_warnings=False):
    """Load a strict versioned policy; CLI options can only add requirements."""
    policy = {"schema_version": "1.0", "required_checks": [], "fail_on_warnings": False}
    if path is not None:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Policy must be an object")
        version = value.get("schema_version")
        expected = set(policy)
        if version == "1.1":
            expected.add("build_volume_orientation")
        if set(value) != expected:
            raise ValueError(
                "Policy must contain schema_version, required_checks, "
                "and fail_on_warnings only"
            )
        if version not in ("1.0", "1.1"):
            raise ValueError("Unsupported policy schema_version")
        if version == "1.1" and value["build_volume_orientation"] not in (
            "generated",
            "xy_90",
        ):
            raise ValueError("Unsupported build_volume_orientation")
        if type(value["fail_on_warnings"]) is not bool:
            raise ValueError("fail_on_warnings must be a boolean")
        if not isinstance(value["required_checks"], list):
            raise ValueError("required_checks must be a list")
        policy = value
    codes = [*policy["required_checks"], *required_checks]
    if any(
        not isinstance(code, str) or not code or code.strip() != code for code in codes
    ):
        raise ValueError("Required check codes must be nonempty trimmed strings")
    return {
        **policy,
        "required_checks": sorted(set(codes)),
        "fail_on_warnings": policy["fail_on_warnings"] or fail_on_warnings,
    }


def evaluate_policy(report, policy):
    """Require every occurrence of selected codes to pass; absence fails."""
    reasons = []
    orientation = policy.get("build_volume_orientation", "generated")
    for check in report["checks"]:
        if (
            check["code"] == "build_volume"
            and check.get("orientation_policy", "generated") != orientation
        ):
            reasons.append("Build-volume evidence orientation differs from policy")
    if report["evaluated_status"] != "PASS":
        reasons.append("Evaluated validation checks did not pass")
    for code in policy["required_checks"]:
        matches = [c for c in report["checks"] if c["code"] == code]
        if not matches:
            reasons.append(f"Required check is absent: {code}")
        for check in matches:
            if check["status"] != "PASS":
                subject = f" ({check['part_name']})" if "part_name" in check else ""
                reasons.append(f"Required check {code}{subject}: {check['status']}")
    if policy["fail_on_warnings"] and report["warning_count"] > 0:
        reasons.append(f"Warnings prohibited: {report['warning_count']}")
    return {
        "status": "FAIL" if reasons else "PASS",
        "policy": policy,
        "reasons": reasons,
    }
