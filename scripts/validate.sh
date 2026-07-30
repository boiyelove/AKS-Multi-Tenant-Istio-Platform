#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT

python3 -m unittest discover -s "$repo_root/tests" -v
python3 "$repo_root/src/tenant_renderer.py" \
  --config "$repo_root/examples/tenants/team-blue.json" \
  --output "$build_dir/first.json"
python3 "$repo_root/src/tenant_renderer.py" \
  --config "$repo_root/examples/tenants/team-blue.json" \
  --output "$build_dir/second.json"
cmp "$build_dir/first.json" "$build_dir/second.json"
python3 -m json.tool "$build_dir/first.json" >/dev/null

if command -v bicep >/dev/null 2>&1; then
  bicep build "$repo_root/infra/main.bicep" --outfile "$build_dir/main.json"
elif command -v az >/dev/null 2>&1; then
  AZURE_CONFIG_DIR="$build_dir/az" az bicep build \
    --file "$repo_root/infra/main.bicep" \
    --outfile "$build_dir/main.json"
else
  echo "warning: Bicep compiler unavailable; skipped IaC compilation" >&2
fi

if command -v shellcheck >/dev/null 2>&1; then
  shellcheck "$repo_root/scripts/validate.sh"
fi
