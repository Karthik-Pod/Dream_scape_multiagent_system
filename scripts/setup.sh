#!/bin/bash
# ─────────────────────────────────────────────────────────
# Dreamscape - One Command Setup Script
# Run this once on a fresh machine.
# Usage: chmod +x scripts/setup.sh && ./scripts/setup.sh
# ─────────────────────────────────────────────────────────

set -e  # Exit on any error

echo ""
echo "🌙 DREAMSCAPE - Environment Setup"
echo "══════════════════════════════════"

# ── 1. Python version check ───────────────────────────────
echo ""
echo "▶ Checking Python version..."
python3 --version
if ! python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
    echo "❌ Python 3.10+ required. Please upgrade."
    exit 1
fi
echo "✅ Python OK"

# ── 2. Create virtual environment ────────────────────────
echo ""
echo "▶ Creating virtual environment..."
python3 -m venv .venv
echo "✅ Virtual environment created at .venv/"

# ── 3. Activate and install dependencies ─────────────────
echo ""
echo "▶ Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt
echo "✅ Dependencies installed"

# ── 4. Create .env from template ─────────────────────────
echo ""
echo "▶ Setting up .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env created from template"
    echo "⚠️  IMPORTANT: Open .env and add your GROQ_API_KEY"
else
    echo "✅ .env already exists — skipping"
fi

# ── 5. Create storage directories ────────────────────────
echo ""
echo "▶ Creating storage directories..."
mkdir -p storage/{stories,scenes,images,audio,videos,chroma}
echo "✅ Storage directories ready"

# ── 6. CUDA check ────────────────────────────────────────
echo ""
echo "▶ Checking CUDA..."
if python3 -c "import torch; print('CUDA:', torch.cuda.is_available())" 2>/dev/null; then
    echo "✅ PyTorch CUDA check complete"
else
    echo "ℹ️  PyTorch not installed yet (needed for Week 3 image generation)"
fi

# ── 7. Done ───────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE"
echo ""
echo "Next steps:"
echo "  1. Add your GROQ_API_KEY to .env"
echo "  2. source .venv/bin/activate"
echo "  3. cd backend && python main.py"
echo ""
echo "To test your Groq connection:"
echo "  python scripts/test_agents.py"
echo "══════════════════════════════════════════════════════"
