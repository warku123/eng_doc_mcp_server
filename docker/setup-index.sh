#!/bin/bash
# Download java-tron documentation index

INDEX_URL="https://raw.githubusercontent.com/tronprotocol/documentation-en/gh-pages/search/search_index.json"
INDEX_DIR="./site/search"
INDEX_FILE="$INDEX_DIR/search_index.json"

echo "📥 Downloading java-tron documentation index..."

mkdir -p "$INDEX_DIR"

if command -v curl &> /dev/null; then
    curl -L -o "$INDEX_FILE" "$INDEX_URL"
elif command -v wget &> /dev/null; then
    wget -O "$INDEX_FILE" "$INDEX_URL"
else
    echo "❌ curl or wget is required"
    exit 1
fi

if [ -f "$INDEX_FILE" ]; then
    echo "✅ Index downloaded: $INDEX_FILE"
    # Verify JSON
    python3 -c "import json; f=open('$INDEX_FILE'); d=json.load(f); print(f'   Documents: {len(d[\"docs\"])}')"
else
    echo "❌ Download failed"
    exit 1
fi
