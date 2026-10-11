"""Inspect catalogued upstream installers without executing their contents."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen


MAX_BODY_BYTES = 64 * 1024
CONFIGURABLE_ENVIRONMENT = re.compile(
    r"^\s*(?P<name>[A-Z][A-Z0-9_]*)=(?:[\"'])?\$\{(?P=name):-", re.MULTILINE
)
COMMAND_LINE_ARGUMENT = re.compile(
    r"\b(?:getopts|shift)\b|\b(?:case|if|while|for)\b[^\n]*\$(?:\{)?1\b"
)


class UpstreamInspectionError(RuntimeError):
    """Raised when an explicitly allowed inspection cannot produce evidence."""


def validate_component(component: dict[str, Any]) -> None:
    config = component.get("upstream_inspection")
    if config is None:
        return
    if not isinstance(config, dict):
        raise UpstreamInspectionError("upstream inspection metadata must be an object")
    url = config.get("url")
    parser = config.get("parser")
    environment = config.get("allowed_configurable_environment")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise UpstreamInspectionError("upstream inspection URL must be HTTPS")
    if parser != "aoe-install-sh-v1":
        raise UpstreamInspectionError("upstream inspection parser is unsupported")
    if not isinstance(environment, list) or not all(isinstance(item, str) for item in environment):
        raise UpstreamInspectionError("allowed configurable environment must be a string list")
    if config.get("on_contract_change") != "block":
        raise UpstreamInspectionError("upstream contract changes must block the action")
    expected_hash = config.get("expected_sha256")
    if expected_hash is not None and (
        not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash)
    ):
        raise UpstreamInspectionError("expected upstream hash must be a lowercase SHA-256")


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "pennix-workflow-lifecycle/1"})
    try:
        with urlopen(request, timeout=10) as response:  # nosec B310: URL is catalog-controlled
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_BODY_BYTES:
                raise UpstreamInspectionError("upstream installer exceeds inspection size limit")
            body = response.read(MAX_BODY_BYTES + 1)
    except (OSError, ValueError, URLError) as error:
        raise UpstreamInspectionError("could not retrieve the catalogued upstream installer") from error
    if len(body) > MAX_BODY_BYTES:
        raise UpstreamInspectionError("upstream installer exceeds inspection size limit")
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise UpstreamInspectionError("upstream installer is not UTF-8 text") from error


def inspect_component(
    component: dict[str, Any], fetcher: Callable[[str], str] = fetch_text
) -> dict[str, Any]:
    """Return bounded evidence for one catalogued installer control surface."""

    validate_component(component)
    config = component.get("upstream_inspection")
    if not isinstance(config, dict):
        raise UpstreamInspectionError("component has no upstream inspection metadata")
    content = fetcher(config["url"])
    configurable = set(CONFIGURABLE_ENVIRONMENT.findall(content))
    allowed = set(config["allowed_configurable_environment"])
    changed: list[str] = []
    unexpected = sorted(configurable - allowed)
    if unexpected:
        changed.append("unexpected configurable environment: " + ", ".join(unexpected))
    if not allowed.issubset(configurable):
        changed.append("expected configurable environment is missing")
    if COMMAND_LINE_ARGUMENT.search(content):
        changed.append("command-line argument handling changed")
    if "releases/latest" not in content:
        changed.append("release resolution changed")

    result: dict[str, Any] = {
        "url": config["url"],
        "parser": config["parser"],
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }
    expected_hash = config.get("expected_sha256")
    if isinstance(expected_hash, str) and result["sha256"] != expected_hash:
        changed.append("upstream installer hash changed")
    if changed:
        result.update({"status": "upstream-contract-changed", "reason": "; ".join(changed)})
        return result
    result.update(
        {
            "status": "match",
            "semantics": {
                "configurable_environment": sorted(allowed),
                "delivery_mapping": "not-applicable-to-selected-package",
            },
        }
    )
    return result
