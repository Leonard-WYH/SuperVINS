#!/usr/bin/env bash
# Files inside the project are resolved from this script, independently of pwd.
SUPERVINS_WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
supervins_path() {
    case "$1" in
        /*) realpath -m -- "$1" ;;
        *) realpath -m -- "$SUPERVINS_WS/$1" ;;
    esac
}
mkdir -p "$SUPERVINS_WS/logs" "$SUPERVINS_WS/results"
