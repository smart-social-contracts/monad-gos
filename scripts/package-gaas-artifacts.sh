#!/usr/bin/env bash
# Package Chora backend wasm + frontend dist for GaaS deployment.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/artifacts"
FRONTEND="${ROOT}/src/chora_frontend"

mkdir -p "${OUT}"

echo "==> icp build chora_backend"
cd "${ROOT}"
icp build chora_backend

# icp 1.x writes raw wasm (no extension) here; older layouts keep a .wasm suffix.
WASM_CANDIDATES=(
	"${ROOT}/.icp/cache/artifacts/chora_backend"
	"${ROOT}/.icp/canisters/chora_backend/chora_backend.wasm"
	"${ROOT}/.icp/canisters/chora_backend/chora_backend.wasm.gz"
)

WASM_SRC=""
for candidate in "${WASM_CANDIDATES[@]}"; do
	if [[ -f "${candidate}" ]]; then
		WASM_SRC="${candidate}"
		break
	fi
done

if [[ -z "${WASM_SRC}" ]]; then
	echo "error: chora_backend.wasm not found; searched:" >&2
	printf '  %s\n' "${WASM_CANDIDATES[@]}" >&2
	exit 1
fi

echo "==> gzip wasm -> ${OUT}/chora_backend.wasm.gz"
gzip -c "${WASM_SRC}" > "${OUT}/chora_backend.wasm.gz"

echo "==> npm ci && npm run build (frontend)"
cd "${FRONTEND}"
npm ci
npm run build

echo "==> tar dist -> ${OUT}/chora_frontend.tar.gz"
tar -C "${FRONTEND}/dist" -czf "${OUT}/chora_frontend.tar.gz" .

echo "Done:"
echo "  ${OUT}/chora_backend.wasm.gz"
echo "  ${OUT}/chora_frontend.tar.gz"
