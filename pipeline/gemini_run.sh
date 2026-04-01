#!/bin/bash
# =============================================================================
# gemini_run.sh — Gemini Pro wrapper with fallback for Oracle pipeline
#
# Usage:
#   source pipeline/gemini_run.sh
#   gemini_run "prompt text" context_file1 [context_file2 ...]
#
# Returns:
#   GEMINI_OUTPUT  — the text output (empty if failed)
#   GEMINI_OK      — "true" if succeeded, "false" if fell back to Claude
#
# Behavior:
#   1. Concatenate all context files → /tmp/gemini_context.txt
#   2. Pipe to gemini-2.5-pro with the prompt
#   3. On exit != 0: retry once with stricter grounding instruction
#   4. On second failure: set GEMINI_OK=false so Claude knows to go native
#   5. Grounding check: grep each VERIFY_TERM against context files
#      Call: gemini_verify "term to check" file1 [file2 ...]
#      Returns 0 (found) or 1 (not found → flag to Claude)
# =============================================================================

GEMINI_MODEL="gemini-2.5-pro"
GEMINI_CONTEXT_FILE="/tmp/gemini_context.txt"
GEMINI_ERR_FILE="/tmp/gemini_err.txt"
GEMINI_OUTPUT=""
GEMINI_OK="false"

gemini_run() {
  local PROMPT="$1"
  shift
  local CONTEXT_FILES=("$@")

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

  # Attempt 1
  GEMINI_OUTPUT=$(cat "$GEMINI_CONTEXT_FILE" | gemini -m "$GEMINI_MODEL" -p "$PROMPT" 2>"$GEMINI_ERR_FILE")
  local EXIT1=$?

  if [ $EXIT1 -eq 0 ] && [ -n "$GEMINI_OUTPUT" ]; then
    GEMINI_OK="true"
    return 0
  fi

  # Log attempt 1 failure
  echo "⚠ Gemini attempt 1 failed (exit $EXIT1): $(cat $GEMINI_ERR_FILE | head -3)" >&2

  # Attempt 2 — stricter grounding instruction prepended
  local STRICT_PROMPT="IMPORTANT: Use ONLY information explicitly present in the provided files above. Do not invent, extrapolate, or add external knowledge. If a fact is not in the files, omit it.

$PROMPT"

  GEMINI_OUTPUT=$(cat "$GEMINI_CONTEXT_FILE" | gemini -m "$GEMINI_MODEL" -p "$STRICT_PROMPT" 2>"$GEMINI_ERR_FILE")
  local EXIT2=$?

  if [ $EXIT2 -eq 0 ] && [ -n "$GEMINI_OUTPUT" ]; then
    GEMINI_OK="true"
    echo "ℹ Gemini succeeded on retry (attempt 2)" >&2
    return 0
  fi

  # Both attempts failed
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
