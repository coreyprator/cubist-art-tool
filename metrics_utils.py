# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: metrics_utils.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:45+02:00
# === CUBIST STAMP END ===

# ======================================================================
# File: metrics_utils.py
# Stamp: 2025-08-22T17:31:37Z
# (Auto-added header for paste verification)
# ======================================================================
import os
import re

_TS = [
    re.compile(r"_\d{8}_\d{6}"),
    re.compile(r"-\d{8}-\d{6}"),
    re.compile(r"\d{4}-\d{2}-\d{2}[T_ ]\d{2}[:\-]\d{2}[:\-]\d{2}"),
]


def normalize_name(s: str | None) -> str | None:
    if not isinstance(s, str):
        return s
    s = os.path.basename(s)
    for rx in _TS:
        s = rx.sub("TIMESTAMP", s)
    s = re.sub(r"\d", "N", s)
    return s


def stabilize_metrics(metrics: dict) -> dict:
    """
    Scrub paths/timestamps on known fields, then deep-scrub everything.
    """

    def stable_metric_path(p):
        if not p:
            return p
        return normalize_name(p)

    def stable_metrics_any(obj):
        if isinstance(obj, dict):
            return {k: stable_metrics_any(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [stable_metrics_any(x) for x in obj]
        elif isinstance(obj, str):
            s = obj
            s = re.sub(r"\d{8}_\d{6,}", "TIMESTAMP", s)
            s = re.sub(r"out\d+\.svg", "OUT.svg", s)
            s = re.sub(r"out\d+\.png", "OUT.png", s)
            s = re.sub(r"m\d+\.json", "OUT.json", s)
            s = re.sub(r"in\.png", "IN.png", s)
            s = s.replace("\\", "/")
            return s
        else:
            return obj

    try:
        if isinstance(metrics, dict):
            t = metrics.get("totals", {})
            if isinstance(t, dict):
                for k in ("output_svg", "output_png", "output_path", "output"):
                    if k in t:
                        t[k] = stable_metric_path(t[k])
                if "output_dir" in t:
                    t["output_dir"] = "<OUTDIR>"
                for k in list(t.keys()):
                    kl = str(k).lower()
                    if any(
                        s in kl for s in ("time", "timestamp", "elapsed", "duration")
                    ):
                        t.pop(k, None)
            stages = metrics.get("stages", [])
            if isinstance(stages, list):
                for s in stages:
                    if not isinstance(s, dict):
                        continue
                    for k in ("output_svg", "output_png", "output_path", "output"):
                        if k in s:
                            s[k] = stable_metric_path(s[k])
                    if "output_dir" in s:
                        s["output_dir"] = "<OUTDIR>"
                    for k in list(s.keys()):
                        kl = str(k).lower()
                        if any(
                            w in kl
                            for w in ("time", "timestamp", "elapsed", "duration")
                        ):
                            s.pop(k, None)
        return stable_metrics_any(metrics)
    except Exception:
        return metrics


# ======================================================================
# End of File: metrics_utils.py  (2025-08-22T17:31:37Z)
# ======================================================================


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:45+02:00
# === CUBIST FOOTER STAMP END ===
