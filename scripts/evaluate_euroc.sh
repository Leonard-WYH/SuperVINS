#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/common.sh"
ws="$SUPERVINS_WS"
run="${1:?usage: evaluate_euroc.sh result_directory [groundtruth_tum.txt]}"
run="$(supervins_path "$run")"
gt="${2:-$ws/data/groundtruth_tum.txt}"
gt="$(supervins_path "$gt")"
export MPLBACKEND=Agg
evo="$ws/deps/evo-venv310/bin"
mkdir -p "$run/evaluation"
"$evo/python" "$ws/tools/prepare_eval_subset.py" "$run"
for spec in 'vio.csv:vio' 'loop_corrected_tum.txt:loop' 'vio_loop.csv:pose_graph' 'vio_at_keyframes.tum:vio_keyframes'; do
 file="${spec%%:*}";name="${spec##*:}"
 if [[ ! -s "$run/$file" ]]; then echo "Missing trajectory: $run/$file" >&2; exit 1; fi
 "$evo/evo_ape" tum "$gt" "$run/$file" --align --no_warnings --t_max_diff 0.01 --pose_relation trans_part --save_results "$run/evaluation/${name}_ape.zip" --save_plot "$run/evaluation/${name}_ape.pdf" 2>&1 | tee "$run/evaluation/${name}_ape.log"
done
"$evo/evo_traj" tum "$run/vio.csv" "$run/loop_corrected_tum.txt" --ref "$gt" --align --no_warnings --t_max_diff 0.01 --save_plot "$run/evaluation/trajectories.pdf" 2>&1 | tee "$run/evaluation/trajectories.log"
"$evo/python" "$ws/tools/summarize_eval.py" "$run" "$gt"
