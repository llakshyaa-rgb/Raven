"""Tests for the standard-library-only Termux preflight."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "termux_preflight.py"
SPEC = importlib.util.spec_from_file_location("termux_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
PREFLIGHT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PREFLIGHT
SPEC.loader.exec_module(PREFLIGHT)


def test_module_available_handles_missing_modules() -> None:
    with patch.object(PREFLIGHT.importlib.util, "find_spec", return_value=None):
        assert PREFLIGHT.module_available("definitely_missing_module") is False


def test_module_available_handles_import_errors() -> None:
    with patch.object(PREFLIGHT.importlib.util, "find_spec", side_effect=ModuleNotFoundError):
        assert PREFLIGHT.module_available("broken_module") is False


def test_collect_separates_core_and_optional_dependencies() -> None:
    with patch.object(PREFLIGHT, "module_available", side_effect=lambda module: module == "typer"):
        report = PREFLIGHT.collect()

    assert report["core_ready"] is False
    assert "Typer" not in report["missing_core"]
    assert "Rich" in report["missing_core"]
    assert "LanceDB" in report["missing_optional"]
    assert any(item["name"] == "ONNX Runtime" for item in report["checks"])


def test_collect_reports_runtime_platform() -> None:
    with patch.object(PREFLIGHT, "module_available", return_value=True):
        report = PREFLIGHT.collect()

    assert report["python"] == sys.version.split()[0]
    assert report["machine"]
    assert report["core_ready"] is True
    assert report["missing_core"] == []
