#!/usr/bin/env bash
set -eo pipefail
ws="$(cd "$(dirname "$0")/.." && pwd)"
py="${1:-/home/wyh/anaconda3/envs/neo/bin/python}"
"$py" -m venv "$ws/deps/evo-venv310"
"$ws/deps/evo-venv310/bin/python" -m pip install 'evo==1.29.0'
