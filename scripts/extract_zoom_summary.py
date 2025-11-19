#!/usr/bin/env python3
"""
Utility script to extract the ingestion summary from logs/zoom_ingestion.log
"""
from __future__ import annotations

import pathlib

def main() -> int:
    log_path = pathlib.Path("logs/zoom_ingestion.log")
    if not log_path.exists():
        print("Log file logs/zoom_ingestion.log not found.")
        return 0

    lines = log_path.read_text().splitlines()
    summary_lines = []
    capture = False

    for line in lines:
        if "INGESTION SUMMARY" in line or "Zoom ingestion complete" in line:
            capture = True
        if capture:
            summary_lines.append(line)

    if summary_lines:
        print("\n".join(summary_lines[-20:]))
    else:
        tail = "\n".join(lines[-20:]) if lines else "Log file was empty."
        print("Summary not found. Recent log lines:\n" + tail)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
