#!/usr/bin/env bash
set -euo pipefail

IPSW_PATH="${1:-}"
HEADERS_DIR="${2:-$(pwd)/headers}"

if [[ -z "$IPSW_PATH" ]]; then
    echo "Usage: $0 <path/to/firmware.ipsw> [headers_dir]"
    echo ""
    echo "Example:"
    echo "  $0 ~/Downloads/iPhone18,3_26.5_23F77_Restore.ipsw"
    exit 1
fi

if ! command -v ipsw &>/dev/null; then
    echo "Error: 'ipsw' not found. Install with: brew install blacktop/tap/ipsw"
    exit 1
fi

IPSW_PATH="$(cd "$(dirname "$IPSW_PATH")" && pwd)/$(basename "$IPSW_PATH")"

INFO=$(ipsw info "$IPSW_PATH" 2>/dev/null)
VERSION=$(echo "$INFO" | grep "Version" | head -1 | awk '{print $3}')
BUILD=$(echo "$INFO" | grep "BuildVersion" | head -1 | awk '{print $3}')

if [[ -z "$VERSION" || -z "$BUILD" ]]; then
    echo "Warning: Could not determine version/build"
    VERSION="unknown"
    BUILD="unknown"
fi

DSC_TMP="$(mktemp -d /tmp/ipsw_dsc_XXXXXX)"

echo "=== iOS Header Dump ==="
echo "IPSW    : $IPSW_PATH"
echo "Version : iOS $VERSION ($BUILD)"
echo "Output  : $HEADERS_DIR"
echo ""

if [[ -d "$HEADERS_DIR" ]] && find "$HEADERS_DIR" -name "*.h" -maxdepth 2 | read -r; then
    PREV_VERSION=$(cat "$HEADERS_DIR/version.txt" 2>/dev/null || echo "unknown")
    echo "Warning: $HEADERS_DIR already contains headers (version: $PREV_VERSION)"
    echo "         Existing headers will be replaced."
    echo ""
fi

trap 'echo "Cleaning up temp files..."; rm -rf "$DSC_TMP"' EXIT

echo "[1/2] Extracting dyld_shared_cache from IPSW..."
ipsw extract --dyld "$IPSW_PATH" -o "$DSC_TMP" 2>&1 | grep -v "^$"

DSC_PATH=$(find "$DSC_TMP" -name "dyld_shared_cache_arm64e" 2>/dev/null | grep -v '\.' | head -1)
if [[ -z "$DSC_PATH" ]]; then
    DSC_PATH=$(find "$DSC_TMP" -name "dyld_shared_cache_arm64*" 2>/dev/null | grep -v '\.\|dylddata\|\.map' | head -1)
fi
if [[ -z "$DSC_PATH" ]]; then
    echo "Error: Could not find dyld_shared_cache"
    find "$DSC_TMP" -type f | head -10
    exit 1
fi

echo "Found DSC: $DSC_PATH"
echo ""

echo "[2/2] Dumping ObjC headers..."
echo "      This may take 10-20 minutes..."
mkdir -p "$HEADERS_DIR"

# 既存ヘッダーを削除（フレームワークディレクトリのみ）
find "$HEADERS_DIR" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null || true

ipsw class-dump --all --headers -o "$HEADERS_DIR" "$DSC_PATH" 2>&1 | grep -v "^$"

# フレームワークを先頭文字ごとのバケットに整理
echo "Reorganizing into letter buckets..."
python3 "$(dirname "$0")/reorganize.py" "$HEADERS_DIR"

# バージョン情報を記録
echo "$VERSION ($BUILD)" > "$HEADERS_DIR/version.txt"

HEADER_COUNT=$(find "$HEADERS_DIR" -name "*.h" | wc -l | tr -d ' ')
FRAMEWORK_COUNT=$(find "$HEADERS_DIR" -mindepth 2 -maxdepth 2 -type d | wc -l | tr -d ' ')

echo ""
echo "=== Done ==="
echo "Frameworks : $FRAMEWORK_COUNT"
echo "Headers    : $HEADER_COUNT"
echo "Output     : $HEADERS_DIR"
echo ""
echo "Next steps:"
echo "  make site              # generate browsable HTML"
echo "  git add headers/"
echo "  git commit -m \"iOS $VERSION ($BUILD)\""
