#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "${1:-}" in
  install|check|rollback) exec python3 "$script_dir/workflow_package.py" "$@" ;;
  codex|orca|omnigent) target=$1; shift; exec python3 "$script_dir/workflow_package.py" install --target "$target" "$@" ;;
  '') exec python3 "$script_dir/workflow_package.py" install --target codex ;;
  *) exec python3 "$script_dir/workflow_package.py" "$@" ;;
esac
