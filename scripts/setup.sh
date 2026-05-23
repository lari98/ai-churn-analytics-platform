#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Setup Script — AI Customer Churn & Behavioral Analytics Platform
# Installs dependencies, configures local dev environment, and validates setup.
# Usage: bash scripts/setup.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${BLUE}[SETUP]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
fail() { echo -e "${RED}[FAIL]${NC}  $1"; exit 1; }

log "AI Churn Analytics Platform — Environment Setup"
log "================================================"

# ── Check prerequisites ───────────────────────────────────────────────────────
log "Checking prerequisites..."
command -v python3 &>/dev/null || fail "python3 not found. Install Python 3.11+"
command -v docker  &>/dev/null || fail "docker not found. Install Docker Desktop"
command -v git     &>/dev/null || fail "git not found"
command -v az      &>/dev/null || { log "Azure CLI not found — skipping Azure checks"; }

PYTHON_VER=$(python3 --version | awk '{print $2}')
log "Python version: $PYTHON_VER"
ok "Prerequisites satisfied"

# ── Python virtual environment ────────────────────────────────────────────────
log "Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    ok "Virtual environment created at .venv/"
else
    ok "Virtual environment already exists"
fi

source .venv/bin/activate
pip install --upgrade pip --quiet

log "Installing API dependencies..."
pip install -r api/requirements.txt --quiet
ok "API dependencies installed"

log "Installing ML dependencies..."
pip install mlflow xgboost lightgbm scikit-learn imbalanced-learn shap pandas numpy --quiet
ok "ML dependencies installed"

log "Installing dev/test tools..."
pip install ruff black mypy isort bandit pytest pytest-asyncio pytest-cov httpx --quiet
ok "Dev tools installed"

# ── Environment configuration ─────────────────────────────────────────────────
log "Configuring environment..."
if [ ! -f "docker/.env" ]; then
    cp docker/.env.example docker/.env
    log "Created docker/.env from template — edit it with your Azure credentials"
else
    ok "docker/.env already exists"
fi

# ── Docker secrets directory ──────────────────────────────────────────────────
mkdir -p docker/secrets
if [ ! -f "docker/secrets/db_password.txt" ]; then
    echo "dev_db_password_$(openssl rand -hex 8)" > docker/secrets/db_password.txt
    chmod 600 docker/secrets/db_password.txt
    ok "Generated docker/secrets/db_password.txt"
fi

# ── Local Docker environment ──────────────────────────────────────────────────
log "Starting local Docker services (postgres + redis + mlflow)..."
docker-compose -f docker/docker-compose.yml up -d postgres redis mlflow 2>/dev/null && \
    ok "Docker services started" || \
    log "Docker services failed to start — check docker-compose.yml and .env"

# ── Run lint checks ───────────────────────────────────────────────────────────
log "Running lint checks..."
ruff check api/ ml/ --quiet && ok "Ruff lint passed" || log "Lint issues found — run: ruff check api/ ml/"

# ── Run tests ─────────────────────────────────────────────────────────────────
log "Running test suite..."
export ENVIRONMENT=development
export SECRET_KEY="setup-test-secret-key-minimum-32-chars-long"
export DATABASE_URL="sqlite+aiosqlite:///./test.db"
export AZURE_TENANT_ID="test" AZURE_CLIENT_ID="test" AZURE_CLIENT_SECRET="test"
export AZURE_KEY_VAULT_URL="https://test.vault.azure.net/"
export AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com/"
export AZURE_OPENAI_API_KEY="test" PII_MASKING_SALT="test-pii-salt-32-chars-here!!!!!!"
export AZURE_STORAGE_ACCOUNT="test" AZURE_STORAGE_KEY="test"
export MLFLOW_TRACKING_URI="http://localhost:5000"
export AZURE_SEARCH_ENDPOINT="https://test.search.windows.net" AZURE_SEARCH_KEY="test"
export REDIS_URL="redis://localhost:6379/0"

pytest api/tests/ -q --tb=short 2>/dev/null && ok "Tests passed" || log "Some tests failed — check above"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo "  API (swagger):  http://localhost:8000/docs"
echo "  MLflow UI:      http://localhost:5000"
echo "  Grafana:        http://localhost:3000"
echo ""
echo "  Next steps:"
echo "  1. Edit docker/.env with your Azure credentials"
echo "  2. docker-compose -f docker/docker-compose.yml up -d"
echo "  3. python ml/training/train_churn.py --data-path data/sample/customers.csv"
echo ""
