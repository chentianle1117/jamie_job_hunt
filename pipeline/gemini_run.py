#!/usr/bin/env python3
"""
Fat-context AI wrapper for the Oracle pipeline — PROVIDER-AGNOSTIC.

Despite the historical name, this routes to whichever "brain" engine is available:
  - Gemini CLI   (`gemini`)        — Google AI Pro subscription (RETIRES 2026-06-18 for Pro tier)
  - Codex CLI    (`codex exec`)    — ChatGPT Plus subscription (Jamie's Mac; David's secondary)
  - native       (exit 1)          — caller (Claude/Codex itself) does the analysis inline

Pick the engine with the AI_BRAIN env var:
  AI_BRAIN=auto    (default)  try gemini → codex → native fallback
  AI_BRAIN=gemini             gemini only (then native)
  AI_BRAIN=codex              codex exec only (then native)
  AI_BRAIN=native             skip subprocess brains; exit 1 so the caller handles it
Optional model overrides: GEMINI_MODEL, CODEX_MODEL.

Usage (unchanged — every existing caller keeps working):
    python3 pipeline/gemini_run.py --prompt "..." --context file1 file2 ...
    python3 pipeline/gemini_run.py --prompt "..." --context file1 --verify "term" --cliche-check

Exit codes:
    0 = success (output on stdout)
    1 = no brain engine succeeded (caller should handle natively)
    2 = cliché detected in output (stderr has details; output still printed)

Why a router, not a binary swap: Gemini CLI and `codex exec` take the SAME interface
(stdin context + prompt → stdout text), so one wrapper serves both. When Gemini retires,
set AI_BRAIN=codex (Jamie) or AI_BRAIN=native (David, in Claude) and nothing else changes.
Cross-platform: pure subprocess, no shell, works on Windows + macOS.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys


def _resolve_cli(name: str):
    """Find a CLI cross-platform. On Windows, npm-global tools are `.cmd`/`.exe` shims that
    subprocess can't exec by bare name without shell=True; shutil.which resolves the real path
    (incl. the .cmd) so we avoid shell=True entirely. Returns the resolved path or None."""
    return (
        shutil.which(name)
        or shutil.which(name + ".cmd")   # Windows npm shim
        or shutil.which(name + ".exe")
    )

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
CODEX_MODEL = os.environ.get("CODEX_MODEL", "")  # empty = Codex default model
TIMEOUT = int(os.environ.get("AI_BRAIN_TIMEOUT", "120"))  # seconds
AI_BRAIN = os.environ.get("AI_BRAIN", "auto").strip().lower()

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


def build_context(files: list) -> str:
    """Concatenate context files into a single text blob."""
    parts = []
    for f in files:
        if os.path.isfile(f):
            parts.append(f"===== {os.path.basename(f)} =====\n")
            with open(f, encoding="utf-8", errors="replace") as fh:
                parts.append(fh.read())
            parts.append("\n")
        else:
            print(f"⚠ context file not found: {f}", file=sys.stderr)
    return "".join(parts)


# ---------------------------------------------------------------------------
# Engine: Gemini CLI  (gemini -m MODEL -p PROMPT  < context)
# ---------------------------------------------------------------------------
def run_gemini(prompt: str, context: str) -> tuple:
    exe = _resolve_cli("gemini")
    if not exe:
        print("ℹ gemini CLI not found (skipping). Install: npm i -g @google/gemini-cli", file=sys.stderr)
        return False, ""
    try:
        result = subprocess.run(
            [exe, "-m", GEMINI_MODEL, "-p", prompt],
            input=context.encode("utf-8"),
            capture_output=True,
            timeout=TIMEOUT,
        )
        output = result.stdout.decode("utf-8", errors="replace").strip()
        if result.returncode == 0 and output:
            return True, output
        err = result.stderr.decode("utf-8", errors="replace")[:300]
        print(f"⚠ Gemini failed (exit {result.returncode}): {err}", file=sys.stderr)
        return False, ""
    except subprocess.TimeoutExpired:
        print(f"⚠ Gemini timed out after {TIMEOUT}s", file=sys.stderr)
        return False, ""


# ---------------------------------------------------------------------------
# Engine: Codex CLI  (codex exec "PROMPT"  < context)  — ChatGPT Plus, no API key
# `codex exec` is non-interactive: prompt = instruction, piped stdin = added context,
# final agent message printed to stdout. Subscription-funded when logged in via ChatGPT.
# ---------------------------------------------------------------------------
def run_codex(prompt: str, context: str) -> tuple:
    full_prompt = (
        prompt
        + "\n\n----- CONTEXT FILES (use ONLY what's below) -----\n"
        + context
        + "\nReturn ONLY the requested analysis text. No preamble, no code fences."
    )
    exe = _resolve_cli("codex")
    if not exe:
        print("ℹ codex CLI not found (skipping). Install: npm i -g @openai/codex", file=sys.stderr)
        return False, ""
    cmd = [exe, "exec"]
    if CODEX_MODEL:
        cmd += ["-m", CODEX_MODEL]
    cmd += ["--", full_prompt]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT)
        output = result.stdout.decode("utf-8", errors="replace").strip()
        if result.returncode == 0 and output:
            return True, output
        err = result.stderr.decode("utf-8", errors="replace")[:300]
        print(f"⚠ Codex failed (exit {result.returncode}): {err}", file=sys.stderr)
        return False, ""
    except subprocess.TimeoutExpired:
        print(f"⚠ Codex timed out after {TIMEOUT}s", file=sys.stderr)
        return False, ""


def run_brain(prompt: str, context: str) -> tuple:
    """Route to the selected engine(s) per AI_BRAIN, with retry + native fallback."""
    if AI_BRAIN == "native":
        print("ℹ AI_BRAIN=native — caller handles analysis inline.", file=sys.stderr)
        return False, ""

    order = {
        "auto": [run_gemini, run_codex],
        "gemini": [run_gemini],
        "codex": [run_codex],
    }.get(AI_BRAIN, [run_gemini, run_codex])

    for engine in order:
        ok, output = engine(prompt, context)
        if ok:
            return True, output
        # one retry with strict grounding prefix before moving to the next engine
        ok, output = engine(GROUNDING_PREFIX + prompt, context)
        if ok:
            return True, output
    return False, ""


def verify_grounding(terms: list, context_files: list) -> None:
    for term in terms:
        found = any(
            os.path.isfile(f)
            and term.lower() in open(f, encoding="utf-8", errors="replace").read().lower()
            for f in context_files
        )
        if not found:
            print(f"⚠ Grounding FAILED: '{term}' not found in context files", file=sys.stderr)


def cliche_check(text: str) -> list:
    return list(set(CLICHE_PATTERN.findall(text)))


def main():
    parser = argparse.ArgumentParser(
        description="Run a fat-context AI brain (Gemini/Codex/native) with grounding + cliché checks."
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--context", nargs="+", default=[], metavar="FILE")
    parser.add_argument("--verify", nargs="*", metavar="TERM")
    parser.add_argument("--cliche-check", action="store_true")
    args = parser.parse_args()

    context = build_context(args.context)
    ok, output = run_brain(args.prompt, context)

    if not ok:
        print(
            f"✗ No brain engine available (AI_BRAIN={AI_BRAIN}) — caller should handle natively.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.verify:
        verify_grounding(args.verify, args.context)

    if args.cliche_check:
        hits = cliche_check(output)
        if hits:
            print(f"⚠ Cliché check FAILED — remove before presenting: {', '.join(hits)}", file=sys.stderr)
            print(output)
            sys.exit(2)

    print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
