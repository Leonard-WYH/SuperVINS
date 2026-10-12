#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/common.sh"
sdk="$(supervins_path "${ONNXRUNTIME_ROOTDIR:-deps/onnxruntime-1.23.2}")"
libsrc="${1:-}"
if [[ -n "$libsrc" ]]; then
    libsrc="$(supervins_path "$libsrc")"
elif [[ -f "$sdk/lib/libonnxruntime.so.1.23.2" && -f "$sdk/lib/libonnxruntime_providers_cuda.so" && -f "$sdk/lib/libonnxruntime_providers_shared.so" ]]; then
    libsrc="$sdk/lib"
else
    for py in "${ORT_PYTHON:-}" python3.10 python3; do
        [[ -n "$py" ]] || continue
        if [[ "$py" == */* ]]; then py="$(supervins_path "$py")"; fi
        command -v "$py" >/dev/null || continue
        if libsrc="$("$py" -c 'import pathlib, onnxruntime as o; assert o.__version__ == "1.23.2"; print(pathlib.Path(o.__file__).parent / "capi")' 2>/dev/null)"; then break; fi
        libsrc=""
    done
fi
[[ -n "$libsrc" ]] || { echo 'Provide an ORT 1.23.2 lib/capi directory, or set ORT_PYTHON to an environment containing onnxruntime-gpu==1.23.2.' >&2; exit 1; }
mkdir -p "$sdk/include" "$sdk/lib"
for lib in libonnxruntime.so.1.23.2 libonnxruntime_providers_cuda.so libonnxruntime_providers_shared.so; do
    [[ -f "$libsrc/$lib" ]] || { echo "Missing $libsrc/$lib" >&2; exit 1; }
    if [[ "$libsrc/$lib" != "$sdk/lib/$lib" && ! "$libsrc/$lib" -ef "$sdk/lib/$lib" ]]; then cp "$libsrc/$lib" "$sdk/lib/"; fi
done
for link in libonnxruntime.so libonnxruntime.so.1; do
    [[ -e "$sdk/lib/$link" ]] || ln -s libonnxruntime.so.1.23.2 "$sdk/lib/$link"
done
for h in onnxruntime_c_api.h onnxruntime_cxx_api.h onnxruntime_cxx_inline.h onnxruntime_float16.h onnxruntime_ep_c_api.h; do
    if [[ ! -s "$sdk/include/$h" ]]; then
        if [[ -s "$libsrc/../include/$h" ]]; then cp "$libsrc/../include/$h" "$sdk/include/$h"
        else curl -fL --retry 3 "https://raw.githubusercontent.com/microsoft/onnxruntime/v1.23.2/include/onnxruntime/core/session/$h" -o "$sdk/include/$h"; fi
    fi
done
ldd "$sdk/lib/libonnxruntime_providers_cuda.so"
