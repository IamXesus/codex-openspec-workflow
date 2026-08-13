#!/usr/bin/env sh
set -eu

target="${1:-codex}"
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

case "$target" in
  codex) agent_root="${CODEX_HOME:-$HOME/.codex}/skills" ;;
  omnigent) agent_root="$HOME/.agents/skills" ;;
  *) echo "usage: $0 [codex|omnigent]" >&2; exit 2 ;;
esac

schema_root="${XDG_DATA_HOME:-$HOME/.local/share}/openspec/schemas"
mkdir -p "$agent_root" "$schema_root"

copy_tree() {
  source_dir=$1
  destination_dir=$2
  find "$source_dir" -type f ! -name '*.pyc' ! -path '*/__pycache__/*' | while IFS= read -r source_file; do
    relative=${source_file#"$source_dir/"}
    mkdir -p "$destination_dir/$(dirname "$relative")"
    cp "$source_file" "$destination_dir/$relative"
  done
}

for skill in openspec-workflow code-reviewer webapp-testing coding-guardrails; do
  copy_tree "$repo_root/skills/$skill" "$agent_root/$skill"
done

for schema in evidence-core evidence-heavy; do
  copy_tree "$repo_root/openspec/schemas/$schema" "$schema_root/$schema"
done

printf '%s\n' "Installed skills into $agent_root"
printf '%s\n' "Installed OpenSpec schemas into $schema_root"
printf '%s\n' 'Review policy/AGENTS.fragment.md manually; existing policy was not changed.'

