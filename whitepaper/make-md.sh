#!/bin/bash

# make-md.sh - Combine whitepaper sections into monolithic markdown
# Now works with fractal directory structure (sections/*/index.md)

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

# Add sections in proper order
add_section "01-title-authors"
add_section "00-executive-summary"
add_section "00-introduction"
add_section "02-glossary"
add_section "03-part1-defining-web4"
add_section "04-part2-foundational-concepts"
add_section "05-part3-value-trust-mechanics"
add_section "06-part4-implications-vision"
add_section "07-part5-memory"
add_section "08-part6-blockchain-typology"
add_section "09-part7-implementation-details"
add_section "09-part7-implementation-examples"
add_section "10-part8-web4-context"
add_section "11-conclusion"
add_section "12-references"
add_section "13-appendices"

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