#!/usr/bin/env python3
"""
Gemini fat-context wrapper for Oracle pipeline.

Usage:
    python3 pipeline/gemini_run.py --prompt "..." --context file1 file2 ...
    python3 pipeline/gemini_run.py --prompt "..." --context file1 --verify "term" --cliche-check

Exit codes:
    0 = success (output on stdout)
    1 = Gemini failed after 2 attempts (Claude should handle natively)
    2 = cliché detected in output (stderr has details)

How it works:
    1. Concatenates all --context files into a single context blob
    2. Pipes to gemini-2.5-pro via subprocess (no shell — no quoting issues)
    3. On failure: retries once with stricter grounding instruction prepended
    4. On second failure: exits 1 so Claude knows to run natively
    5. Optionally verifies terms exist in source files (grounding check)
    6. Optionally scans output for AI clichés (cliché check)
"""

import argparse
import os
import re
import subprocess
import sys

GEMINI_MODEL = "gemini-2.5-pro"
GEMINI_TIMEOUT = 90  # seconds

CLICHE_PATTERN = re.compile(
    r"spearhead|leverage[d]?|synerg|drove strategic|cross-functional impact"
    r"|thrilled|truly inspirational|extensive experience|impressive career"
    r"|passionate about|pick your brain|results-driven|dynamic team",
    re.IGNORECASE,
)

GROUNDING_PREFIX = (
    "IMPORTANT: Use ONLY information explicitly present in the provided files. "
    "Do not invent, extrapolate, or add external knowledge. "
    "If a fact is not in the files, omit it.\n\n"
)


def build_context(files: list) -> bytes:
    """Concatenate context files into a single bytes blob."""
    parts = []
    for f in files:
        if os.path.isfile(f):
            parts.append(f"===== {os.path.basename(f)} =====\n")
            with open(f, encoding="utf-8", errors="replace") as fh:
                parts.append(fh.read())
            parts.append("\n")
        else:
            print(f"⚠ context file not found: {f}", file=sys.stderr)
    return "".join(parts).encode("utf-8")


def run_gemini(prompt: str, context: bytes) -> tuple:
    """
    Attempt one Gemini call.
    Returns (ok: bool, output: str).
    """
    try:
        result = subprocess.run(
            ["gemini", "-m", GEMINI_MODEL, "-p", prompt],
            input=context,
            capture_output=True,
            timeout=GEMINI_TIMEOUT,
        )
        output = result.stdout.decode("utf-8", errors="replace").strip()
        if result.returncode == 0 and output:
            return True, output
        err = result.stderr.decode("utf-8", errors="replace")[:300]
        print(f"⚠ Gemini failed (exit {result.returncode}): {err}", file=sys.stderr)
        return False, ""
    except subprocess.TimeoutExpired:
        print(f"⚠ Gemini timed out after {GEMINI_TIMEOUT}s", file=sys.stderr)
        return False, ""
    except FileNotFoundError:
        print(
            "✗ gemini CLI not found — install with: npm install -g @google/gemini-cli",
            file=sys.stderr,
        )
        return False, ""


def verify_grounding(terms: list, context_files: list) -> None:
    """Check that each term exists in at least one context file. Warns on stderr."""
    for term in terms:
        found = False
        for f in context_files:
            if os.path.isfile(f):
                with open(f, encoding="utf-8", errors="replace") as fh:
                    if term.lower() in fh.read().lower():
                        found = True
                        break
        if not found:
            print(
                f"⚠ Grounding FAILED: '{term}' not found in context files",
                file=sys.stderr,
            )


def cliche_check(text: str) -> list:
    """Return list of cliché matches found in text."""
    return list(set(CLICHE_PATTERN.findall(text)))


def main():
    parser = argparse.ArgumentParser(
        description="Run Gemini 2.5 Pro with fat context and optional grounding/cliché checks."
    )
    parser.add_argument("--prompt", required=True, help="Prompt to send to Gemini")
    parser.add_argument(
        "--context", nargs="+", default=[], metavar="FILE",
        help="Files to include as context (concatenated and piped to Gemini)"
    )
    parser.add_argument(
        "--verify", nargs="*", metavar="TERM",
        help="Terms to verify exist in context files (grounding check, warns on stderr)"
    )
    parser.add_argument(
        "--cliche-check", action="store_true",
        help="Scan output for AI clichés — exits 2 if found"
    )
    args = parser.parse_args()

    context = build_context(args.context)

    # Attempt 1
    ok, output = run_gemini(args.prompt, context)

    # Attempt 2 — prepend strict grounding instruction
    if not ok:
        print("ℹ Retrying with strict grounding instruction...", file=sys.stderr)
        ok, output = run_gemini(GROUNDING_PREFIX + args.prompt, context)

    if not ok:
        print(
            "✗ Gemini unavailable after 2 attempts — Claude should handle natively.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Grounding check (warns only, does not fail)
    if args.verify:
        verify_grounding(args.verify, args.context)

    # Cliché check (exits 2 if found)
    if args.cliche_check:
        hits = cliche_check(output)
        if hits:
            print(
                f"⚠ Cliché check FAILED — remove before presenting: {', '.join(hits)}",
                file=sys.stderr,
            )
            print(output)  # still print output so caller can fix manually
            sys.exit(2)

    print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
