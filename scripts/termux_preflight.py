"""Check Raven's runtime prerequisites on Termux without importing heavy modules.

This preflight is intentionally standard-library-only so it can run before Raven's
runtime dependencies have been installed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Check:
    name: str
    module: str
    purpose: str
    required_for_core: bool


CHECKS = (
    Check("Typer", "typer", "CLI entry point", True),
    Check("Rich", "rich", "CLI rendering", True),
    Check("Pydantic", "pydantic", "configuration and data models", True),
    Check("Pydantic Settings", "pydantic_settings", "configuration loading", True),
    Check("HTTPX", "httpx", "HTTP provider clients", True),
    Check("LiteLLM", "litellm", "model provider integration", True),
    Check("Loguru", "loguru", "application logging", True),
    Check("MCP", "mcp", "MCP tool integration", True),
    Check("orjson", "orjson", "JSON acceleration", True),
    Check("NumPy", "numpy", "numeric and routing features", True),
    Check("LanceDB", "lancedb", "embedded vector memory and knowledge", False),
    Check("PyArrow", "pyarrow", "columnar data used by vector storage", False),
    Check("ONNX Runtime", "onnxruntime", "local document vision models", False),
    Check("OpenCV", "cv2", "document image processing", False),
    Check("Shapely", "shapely", "document geometry processing", False),
    Check("PyClipper", "pyclipper", "document polygon processing", False),
    Check("A2A SDK", "a2a", "agent-to-agent protocol", False),
    Check("WebSockets", "websockets", "optional channel transports", False),
)


def module_available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False


def collect() -> dict[str, object]:
    results = []
    for check in CHECKS:
        results.append(
            {
                **asdict(check),
                "available": module_available(check.module),
            }
        )
    missing_core = [item["name"] for item in results if item["required_for_core"] and not item["available"]]
    missing_optional = [item["name"] for item in results if not item["required_for_core"] and not item["available"]]
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "termux": "com.termux" in __import__("os").environ.get("PREFIX", ""),
        "checks": results,
        "missing_core": missing_core,
        "missing_optional": missing_optional,
        "core_ready": not missing_core,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    report = collect()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("Raven Termux preflight")
        print(f"Python: {report['python']} | {report['implementation']} | {report['machine']}")
        print(f"Platform: {report['platform']}")
        print()
        for item in report["checks"]:
            state = "OK" if item["available"] else "MISSING"
            group = "core" if item["required_for_core"] else "optional"
            print(f"[{state:7}] [{group:8}] {item['name']}: {item['purpose']}")
        print()
        if report["missing_core"]:
            print("Core startup is not ready. Missing: " + ", ".join(report["missing_core"]))
        else:
            print("Core import prerequisites appear present; run Raven's own CLI checks next.")
        if report["missing_optional"]:
            print("Optional integrations may be unavailable: " + ", ".join(report["missing_optional"]))
        print("This checks import availability only; it does not prove native libraries can load.")

    return 0 if report["core_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
