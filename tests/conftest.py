# [stamp:start] Cubist Art — tests/conftest.py — v2.3.7
from __future__ import annotations
import datetime as _dt
import platform as _pf
import sys as _sys
import time as _time
import pytest
import logging

def pytest_report_header(config):
    return [
        f"Python {_sys.version.split()[0]} on {_pf.system()} {_pf.release()}",
        f"PyTest verbosity: {'-vv' if config.option.verbose >= 2 else '-v' if config.option.verbose else 'default'}",
        "Report: -rA (passes, skips, xfails, errors shown); timings: --durations=10",
    ]

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    start = _time.perf_counter()
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] START {item.nodeid}")
    outcome = yield
    dur = _time.perf_counter() - start
    ts2 = _dt.datetime.now().isoformat(timespec="seconds")
    print(f"[{ts2}] END   {item.nodeid}  ({dur:.2f}s)")
    return outcome

def pytest_addoption(parser):
    group = parser.getgroup("cubist")
    group.addoption(
        "--strict-smoke",
        action="store_true",
        default=False,
        help="Error if -m smoke selects zero tests (guard against silent empties).",
    )

def pytest_collection_finish(session):
    """If user asked for -m smoke, ensure we didn't select 0 tests when --strict-smoke is on."""
    config = session.config
    expr = config.getoption("-m") or ""
    strict = config.getoption("--strict-smoke")
    if strict and "smoke" in expr and len(session.items) == 0:
        raise pytest.UsageError("No tests selected by -m smoke (try running without -m or check markers).")

# [stamp:start] collection_noise_guard
def pytest_sessionstart(session):
    # Suppress chatty logs during collection/import of modules
    logging.getLogger("cubist_logger").disabled = True

def pytest_runtest_setup(item):
    # Re-enable logs for the actual running phase
    logging.getLogger("cubist_logger").disabled = False
# [stamp:end]
