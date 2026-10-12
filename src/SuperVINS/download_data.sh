#!/usr/bin/env bash
set -eo pipefail
ws="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
exec "$ws/scripts/download_euroc.sh" "$@"
