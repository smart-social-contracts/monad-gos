#!/usr/bin/env bash
# Package Monad GOS backend wasm + frontend dist for GaaS deployment.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/artifacts"
FRONTEND="${ROOT}/src/monad_frontend"

mkdir -p "${OUT}"

echo "==> icp build monad_backend"
cd "${ROOT}"
icp build monad_backend

# icp 1.x writes raw wasm (no extension) here; older layouts keep a .wasm suffix.
WASM_CANDIDATES=(
	"${ROOT}/.icp/cache/artifacts/monad_backend"
	"${ROOT}/.icp/canisters/monad_backend/monad_backend.wasm"
	"${ROOT}/.icp/canisters/monad_backend/monad_backend.wasm.gz"
)

WASM_SRC=""
for candidate in "${WASM_CANDIDATES[@]}"; do
	if [[ -f "${candidate}" ]]; then
		WASM_SRC="${candidate}"
		break
	fi
done

if [[ -z "${WASM_SRC}" ]]; then
	echo "error: monad_backend.wasm not found; searched:" >&2
	printf '  %s\n' "${WASM_CANDIDATES[@]}" >&2
	exit 1
fi

echo "==> gzip wasm -> ${OUT}/monad_backend.wasm.gz"
gzip -c "${WASM_SRC}" > "${OUT}/monad_backend.wasm.gz"

echo "==> npm ci && npm run build (frontend)"
cd "${FRONTEND}"
npm ci
npm run build

echo "==> tar dist -> ${OUT}/monad_frontend.tar.gz"
tar -C "${FRONTEND}/dist" -czf "${OUT}/monad_frontend.tar.gz" .

echo "Done:"
echo "  ${OUT}/monad_backend.wasm.gz"
echo "  ${OUT}/monad_frontend.tar.gz"
