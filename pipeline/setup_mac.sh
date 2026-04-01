#!/bin/bash
# =============================================================================
# Oracle Job Search — Mac Setup Script
# Run once on Jamie's Mac to install Gemini CLI + authenticate
# Usage: bash pipeline/setup_mac.sh
# =============================================================================

set -e

echo ""
echo "============================================"
echo "  Oracle Job Search — Mac One-Time Setup"
echo "============================================"
echo ""

# --- 1. Check Node.js ---
echo "▶ Checking Node.js..."
if ! command -v node &>/dev/null; then
  echo "  ✗ Node.js not found. Installing via Homebrew..."
  if ! command -v brew &>/dev/null; then
    echo "  Installing Homebrew first..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add brew to PATH for Apple Silicon
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
  brew install node
else
  echo "  ✓ Node.js $(node --version) found"
fi

# --- 2. Install Gemini CLI ---
echo ""
echo "▶ Installing Gemini CLI..."
if command -v gemini &>/dev/null; then
  echo "  ✓ Gemini CLI already installed: $(gemini --version 2>/dev/null || echo 'version unknown')"
else
  npm install -g @google/gemini-cli
  echo "  ✓ Gemini CLI installed"
fi

# --- 3. Authenticate Gemini ---
echo ""
echo "▶ Authenticating Gemini CLI..."
echo "  This will open a browser to sign in with Google."
echo "  Sign in with: davchen1117@gmail.com (Google One AI Pro — Gemini 2.5 Pro included)"
echo ""
read -p "  Press Enter to open browser for Google sign-in..."
gemini auth login
echo "  ✓ Authenticated"

# --- 4. Verify Gemini works ---
echo ""
echo "▶ Verifying Gemini Pro works..."
TEST_RESULT=$(echo "Say only: GEMINI_OK" | gemini -m gemini-2.5-pro -p "Reply with exactly: GEMINI_OK" 2>/dev/null)
if echo "$TEST_RESULT" | grep -q "GEMINI_OK"; then
  echo "  ✓ Gemini 2.5 Pro responding correctly"
else
  echo "  ⚠ Gemini test returned unexpected output: $TEST_RESULT"
  echo "  Try running: gemini auth login"
fi

# --- 5. Install Python deps (for ATS fetch scripts) ---
echo ""
echo "▶ Checking Python + pipeline dependencies..."
if command -v python3 &>/dev/null; then
  echo "  ✓ Python $(python3 --version) found"
  if [ -f "pipeline/scripts/requirements.txt" ]; then
    echo "  Installing pipeline Python dependencies..."
    pip3 install -r pipeline/scripts/requirements.txt --quiet
    echo "  ✓ Dependencies installed"
  fi
else
  echo "  ⚠ Python3 not found — ATS fetch scripts won't work"
  echo "    Install with: brew install python3"
fi

# --- 6. Verify gemini_run.sh is executable ---
echo ""
echo "▶ Setting script permissions..."
chmod +x pipeline/gemini_run.sh 2>/dev/null && echo "  ✓ gemini_run.sh is executable" || echo "  ⚠ gemini_run.sh not found — run git pull"

# --- 7. Summary ---
echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "  Gemini CLI: $(command -v gemini)"
echo "  Account:    davchen1117@gmail.com"
echo "  Model:      gemini-2.5-pro (default for all pipeline tasks)"
echo ""
echo "  To verify: echo 'test' | gemini -m gemini-2.5-pro -p 'say OK'"
echo ""
echo "  Jamie can now run /evaluate, /tailor, /outreach"
echo "  with full Gemini Pro support."
echo ""
