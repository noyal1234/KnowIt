#!/usr/bin/env bash
# Install backend dependencies into the project virtual environment.
# Uses ../.venv (workspace root) by default — never installs into system Python.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"
VENV_DIR="${VENV_DIR:-$PROJECT_ROOT/.venv}"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment at $VENV_DIR ..."
  python3 -m venv "$VENV_DIR"
fi

PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

PY_VERSION="$("$PYTHON" --version 2>&1)"
echo "Using Python: $PY_VERSION"
echo "  Interpreter: $PYTHON"
echo "Installing editable package from $BACKEND_DIR ..."

"$PIP" install --upgrade pip
"$PIP" install -e "$BACKEND_DIR[dev]"

echo ""
echo "Done. Activate the venv with:"
echo "  source \"$VENV_DIR/bin/activate\""
echo ""
echo "Then from backend/:"
echo "  uvicorn app.main:app --reload"
