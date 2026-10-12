#!/usr/bin/env bash
set -eo pipefail
ws="$(cd "$(dirname "$0")/.." && pwd)"
libsrc="${1:-/home/wyh/anaconda3/envs/neo/lib/python3.10/site-packages/onnxruntime/capi}"
sdk="$ws/deps/onnxruntime-1.23.2"
mkdir -p "$sdk/include" "$sdk/lib"
for lib in libonnxruntime.so.1.23.2 libonnxruntime_providers_cuda.so libonnxruntime_providers_shared.so; do
 [[ -f "$libsrc/$lib" ]] || { echo "Missing $libsrc/$lib" >&2; exit 1; }
 if [[ ! -f "$sdk/lib/$lib" ]]; then cp "$libsrc/$lib" "$sdk/lib/"; fi
done
for link in libonnxruntime.so libonnxruntime.so.1; do
 [[ -e "$sdk/lib/$link" ]] || ln -s libonnxruntime.so.1.23.2 "$sdk/lib/$link"
done
for h in onnxruntime_c_api.h onnxruntime_cxx_api.h onnxruntime_cxx_inline.h onnxruntime_float16.h onnxruntime_ep_c_api.h; do
 [[ -s "$sdk/include/$h" ]] || curl -fL --retry 3 "https://raw.githubusercontent.com/microsoft/onnxruntime/v1.23.2/include/onnxruntime/core/session/$h" -o "$sdk/include/$h"
done
ldd "$sdk/lib/libonnxruntime_providers_cuda.so"
