#!/bin/bash

# make-md.sh - Combine whitepaper sections into monolithic markdown
# Now works with fractal directory structure (sections/*/index.md)

# Pull latest changes before building to avoid conflicts
echo "Checking for updates..."
git fetch

# Check if we're behind the remote
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
BASE=$(git merge-base @ @{u})

if [ $LOCAL = $REMOTE ]; then
    echo "Already up to date."
elif [ $LOCAL = $BASE ]; then
    echo "Pulling latest changes..."
    git pull
else
    echo "❌ Error: Your branch has diverged from the remote branch."
    echo "Please resolve conflicts manually before building:"
    echo "  1. Review changes with: git status"
    echo "  2. Either stash your changes: git stash"
    echo "  3. Or commit them: git add . && git commit -m 'your message'"
    echo "  4. Then pull: git pull"
    echo "  5. Run this script again"
    exit 1
fi

echo "Building monolithic Web4 whitepaper markdown..."

OUTPUT_DIR="build"
OUTPUT_FILE="$OUTPUT_DIR/WEB4_Whitepaper_Complete.md"
SECTIONS_DIR="sections"

# Create build directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Clear output file if it exists
> "$OUTPUT_FILE"

# Function to add section with spacing
add_section() {
    local dir=$1
    local file="$SECTIONS_DIR/$dir/index.md"
    if [ -f "$file" ]; then
        cat "$file" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"  # Add blank line between sections
        echo "" >> "$OUTPUT_FILE"  # Add another for spacing
        echo "  ✓ Added $dir"
    else
        echo "  ⚠ Warning: $dir/index.md not found"
    fi
}

echo "Combining sections..."

# Add sections in proper order (2026-07-09 rewrite: equation-ordered technical introduction)
add_section "01-title-authors"
add_section "02-why-web4"
add_section "03-the-equation"
add_section "04-mcp"
add_section "05-rdf"
add_section "06-lct"
add_section "07-t3v3"
add_section "08-mrh"
add_section "09-atp-adp"
add_section "10-composed-architecture"
add_section "11-standard-and-implementations"
add_section "12-conclusion"
add_section "13-glossary"
add_section "14-references"

# Add timestamp
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "*Generated: $(date '+%Y-%m-%d %H:%M:%S')*" >> "$OUTPUT_FILE"

echo ""
echo "✅ Monolithic markdown created: $OUTPUT_FILE"
echo ""

# Show file info
if [ -f "$OUTPUT_FILE" ]; then
    lines=$(wc -l < "$OUTPUT_FILE")
    size=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "📊 Statistics:"
    echo "   Lines: $lines"
    echo "   Size: $size"
fi

# Copy to GitHub Pages location
GITHUB_PAGES_DIR="../docs/whitepaper-web"
if [ -d "$GITHUB_PAGES_DIR" ]; then
    cp "$OUTPUT_FILE" "$GITHUB_PAGES_DIR/WEB4_Whitepaper_Complete.md"
    echo "📄 Copied markdown to GitHub Pages location: $GITHUB_PAGES_DIR/WEB4_Whitepaper_Complete.md"
fi