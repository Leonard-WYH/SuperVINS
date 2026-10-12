#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/common.sh"
py="${1:-${EVO_PYTHON:-}}"
if [[ -z "$py" ]]; then
    for candidate in python3.10 python3; do
        if command -v "$candidate" >/dev/null; then py="$(command -v "$candidate")"; break; fi
    done
fi
[[ -n "$py" ]] || { echo 'Python 3 is required; pass its executable as the first argument.' >&2; exit 1; }
if [[ "$py" == */* ]]; then py="$(supervins_path "$py")"; fi
"$py" -m venv "$SUPERVINS_WS/deps/evo-venv310"
"$SUPERVINS_WS/deps/evo-venv310/bin/python" -m pip install 'evo==1.29.0'
