#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

echo "Installing Diamond Hands in editable mode with python3 -m pip..."
python3 -m pip install --user -e .

USER_BASE="$(python3 -m site --user-base)"
USER_BIN="${USER_BASE}/bin"

if [[ -x "${USER_BIN}/diamondhands" ]]; then
  echo
  echo "Starting Diamond Hands from ${USER_BIN}/diamondhands"
  exec "${USER_BIN}/diamondhands"
fi

echo
echo "diamondhands was not found in ${USER_BIN}."
echo "Falling back to python3 main.py for this session."
echo "To make 'diamondhands' available globally, add this to ~/.zshrc:"
echo "export PATH=\"${USER_BIN}:\$PATH\""
echo
exec python3 main.py
