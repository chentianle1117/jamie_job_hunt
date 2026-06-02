#!/usr/bin/env python3
"""Repair any mojibake replacement char in skills lines back to middot separator."""
import json, os

BASE = os.path.join(os.path.dirname(__file__), "discovered")
REPL = "�"  # replacement char
for r in sorted(os.listdir(BASE)):
    fp = os.path.join(BASE, r, "resume.json")
    if not os.path.exists(fp):
        continue
    raw = open(fp, encoding="utf-8").read()
    if REPL in raw:
        fixed = raw.replace(" " + REPL + " ", " · ").replace(REPL, "·")
        open(fp, "w", encoding="utf-8").write(fixed)
        # validate JSON still parses
        json.load(open(fp, encoding="utf-8"))
        print("[FIXED] " + r)
    else:
        print("[ok]    " + r)
