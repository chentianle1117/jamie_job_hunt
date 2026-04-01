#!/bin/bash
# =============================================================================
# gemini_run.sh — DEPRECATED
#
# Superseded by pipeline/gemini_run.py (Python version).
# The Python version is more robust: no shell quoting issues, has timeout
# handling, automatic temp file cleanup, and cleaner error reporting.
#
# Skills (/evaluate, /tailor) now call:
#   python3 pipeline/gemini_run.py --prompt "..." --context file1 file2 ...
#
# This file is kept as a fallback for environments where Python is unavailable.
# =============================================================================
#
# Original usage (bash version):
#   source pipeline/gemini_run.sh
#   gemini_run "prompt text" context_file1 [context_file2 ...]
#
# Returns:
#   GEMINI_OUTPUT  — the text output (empty if failed)
#   GEMINI_OK      — "true" if succeeded, "false" if fell back to Claude
# =============================================================================

GEMINI_MODEL="gemini-2.5-pro"
GEMINI_CONTEXT_FILE="/tmp/gemini_context.txt"
GEMINI_PROMPT_FILE="/tmp/gemini_prompt.txt"
GEMINI_ERR_FILE="/tmp/gemini_err.txt"
GEMINI_OUTPUT=""
GEMINI_OK="false"

gemini_run() {
  local PROMPT="$1"
  shift
  local CONTEXT_FILES=("$@")

  # Write prompt to file to avoid shell quoting/newline mangling
  printf '%s' "$PROMPT" > "$GEMINI_PROMPT_FILE"

  # Build context file from all inputs
  rm -f "$GEMINI_CONTEXT_FILE"
  for f in "${CONTEXT_FILES[@]}"; do
    if [ -f "$f" ]; then
      echo "===== $(basename $f) =====" >> "$GEMINI_CONTEXT_FILE"
      cat "$f" >> "$GEMINI_CONTEXT_FILE"
      echo "" >> "$GEMINI_CONTEXT_FILE"
    else
      echo "⚠ gemini_run: context file not found: $f" >&2
    fi
  done

  # Attempt 1 — prompt via file to preserve newlines and special chars
  GEMINI_OUTPUT=$(cat "$GEMINI_CONTEXT_FILE" | gemini -m "$GEMINI_MODEL" -p "$(cat $GEMINI_PROMPT_FILE)" 2>"$GEMINI_ERR_FILE")
  local EXIT1=$?

  if [ $EXIT1 -eq 0 ] && [ -n "$GEMINI_OUTPUT" ]; then
    GEMINI_OK="true"
    return 0
  fi

  # Log attempt 1 failure
  echo "⚠ Gemini attempt 1 failed (exit $EXIT1): $(cat $GEMINI_ERR_FILE | head -3)" >&2

  # Attempt 2 — prepend strict grounding instruction
  printf 'IMPORTANT: Use ONLY information explicitly present in the provided files. Do not invent or extrapolate. If a fact is not in the files, omit it.\n\n%s' "$PROMPT" > "$GEMINI_PROMPT_FILE"

  GEMINI_OUTPUT=$(cat "$GEMINI_CONTEXT_FILE" | gemini -m "$GEMINI_MODEL" -p "$(cat $GEMINI_PROMPT_FILE)" 2>"$GEMINI_ERR_FILE")
  local EXIT2=$?

  if [ $EXIT2 -eq 0 ] && [ -n "$GEMINI_OUTPUT" ]; then
    GEMINI_OK="true"
    echo "ℹ Gemini succeeded on retry (attempt 2)" >&2
    return 0
  fi

  # Both attempts failed — Claude handles natively
  echo "✗ Gemini unavailable after 2 attempts. Claude should handle natively." >&2
  echo "  Error: $(cat $GEMINI_ERR_FILE | head -3)" >&2
  GEMINI_OUTPUT=""
  GEMINI_OK="false"
  return 1
}

# Grounding check — verify a term exists in source files
# Usage: gemini_verify "term" file1 [file2 ...]
# Returns: 0 = found (grounded), 1 = not found (flag to Claude)
gemini_verify() {
  local TERM="$1"
  shift
  local FILES=("$@")

  for f in "${FILES[@]}"; do
    if [ -f "$f" ] && grep -qi "$TERM" "$f"; then
      return 0  # found
    fi
  done
  echo "⚠ Grounding check FAILED: '$TERM' not found in source files" >&2
  return 1  # not found
}

# Cliché check — detect AI-sounding phrases in Gemini output
# Usage: gemini_cliche_check "$GEMINI_OUTPUT"
# Returns: 0 = clean, 1 = clichés detected (prints what was found)
gemini_cliche_check() {
  local TEXT="$1"
  local FOUND=$(echo "$TEXT" | grep -iE \
    "spearhead|leverage[d]?|synerg|drove strategic|cross-functional impact|thrilled|truly inspirational|extensive experience|impressive career|passionate about|pick your brain|results-driven|dynamic team" \
    2>/dev/null)

  if [ -n "$FOUND" ]; then
    echo "⚠ Cliché check FAILED — remove before presenting:" >&2
    echo "$FOUND" >&2
    return 1
  fi
  return 0
}
