#!/bin/sh
set -e

REPO="https://github.com/babbworks/heybabb"
INSTALL_DIR="$HOME/.heybabb"

echo "Installing heybabb..."

if [ -d "$INSTALL_DIR" ]; then
  echo "Updating existing install at $INSTALL_DIR"
  git -C "$INSTALL_DIR" pull --quiet
else
  git clone --quiet "$REPO" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -e . --quiet

SHELL_RC=""
case "$SHELL" in
  */zsh)  SHELL_RC="$HOME/.zshrc" ;;
  */bash) SHELL_RC="$HOME/.bashrc" ;;
esac

EXPORT_LINE="export PATH=\"\$HOME/.heybabb/.venv/bin:\$PATH\""

if [ -n "$SHELL_RC" ] && ! grep -q "heybabb" "$SHELL_RC" 2>/dev/null; then
  echo "\n# heybabb" >> "$SHELL_RC"
  echo "$EXPORT_LINE" >> "$SHELL_RC"
  echo "Added heybabb to PATH in $SHELL_RC"
  echo "Run: source $SHELL_RC"
fi

echo ""
echo "Done. Try: heybabb"
