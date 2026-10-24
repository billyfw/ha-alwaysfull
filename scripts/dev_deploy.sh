#!/bin/bash
# Copy custom_components/alwaysfull to the house HA box (ha-lau) over SSH, for a BENCH build.
#
# The normal path is HACS: the box installs releases of billyfw/ha-alwaysfull (CLAUDE.md,
# "Deploy"). Use this only to try an unreleased build. HACS keeps showing the release it last
# installed, and a HACS redownload overwrites whatever this put there.
#
# Usage:
#   scripts/dev_deploy.sh              copy only; then restart HA yourself (with the owner's approval)
#   scripts/dev_deploy.sh --restart    copy, then `ha core restart` (ONLY with explicit approval)
#   scripts/dev_deploy.sh --host ha    deploy to another host (the other house is `ha`; see CLAUDE.md
#                                      before ever doing that: one poller per account)
#
# Python module changes need a full HA restart: reloading the config entry re-runs setup but
# keeps the already-imported modules. The box auto-commits custom_components/ changes into
# ha-lau-config within a few minutes (its git_autocommit sensor), so run
# `git -C ~/devprojects/ha-lau-config pull` afterwards.

set -euo pipefail

HOST="ha-lau"
RESTART=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --restart) RESTART=true; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/custom_components/alwaysfull"
DEST="/config/custom_components/alwaysfull"
VERSION=$(python3 -c "import json; print(json.load(open('$SRC/manifest.json'))['version'])")

echo "Deploying alwaysfull $VERSION to $HOST:$DEST"
ssh -T "$HOST" "sudo mkdir -p /config/custom_components && sudo rm -rf '$DEST'"
tar -C "$ROOT/custom_components" \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='.pytest_cache' --exclude='.DS_Store' \
  -czf - alwaysfull | ssh -T "$HOST" "sudo tar -xzf - -C /config/custom_components"
echo "Files synced. Deployed manifest: $(ssh -T "$HOST" "cat $DEST/manifest.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["version"])')"

if [[ "$RESTART" == true ]]; then
  echo "Restarting Home Assistant core on $HOST..."
  ssh -T "$HOST" "bash -l -c 'ha core restart'"
  echo "Restart sent; core is back in about a minute."
else
  echo "Not restarting. Python changes need: ssh $HOST \"bash -l -c 'ha core restart'\" (ask the owner first)."
fi
