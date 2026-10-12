#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/common.sh"
ws="$SUPERVINS_WS"
cd "$ws"
[[ -s data/V2_01_easy.bag ]] || { echo 'First run scripts/download_euroc.sh and scripts/prepare_euroc.sh.' >&2; exit 1; }
[[ -s src/SuperVINS/supervins_loop_fusion/src/ThirdParty/Voc/superpoint1.yml.gz ]] || { echo 'First extract demo crops and run scripts/train_vocabulary.sh.' >&2; exit 1; }
scripts/build.sh
log="logs/reproduce_$(date +%Y%m%d_%H%M%S).log"
scripts/run_euroc.sh "$@" 2>&1 | tee "$log"
run="$(sed -n 's/^RESULT_DIR=//p' "$log" | tail -1)"
[[ -n "$run" ]]
/usr/bin/python3 tools/check_results.py "$run" | tee "$run/validation_console.log"
scripts/evaluate_euroc.sh "$run" | tee "$run/evaluation_console.log"
ln -sfn "$(basename "$run")" results/latest
printf 'Validated result directory: %s\n' "$run"
