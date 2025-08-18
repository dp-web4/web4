#!/bin/bash

# make-md.sh - Combine whitepaper sections into monolithic markdown
# Usage: ./make-md.sh

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
    local file=$1
    if [ -f "$SECTIONS_DIR/$file" ]; then
        cat "$SECTIONS_DIR/$file" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"  # Add blank line between sections
        echo "" >> "$OUTPUT_FILE"  # Add another for spacing
        echo "  ✓ Added $file"
    else
        echo "  ⚠ Warning: $file not found"
    fi
}

echo "Combining sections..."

# Add sections in proper order
add_section "01-title-authors.md"
add_section "00-executive-summary.md"  # New executive summary
add_section "00-introduction.md"
add_section "02-glossary.md"
add_section "03-part1-defining-web4.md"

# Use revised version if it exists, otherwise use original
if [ -f "$SECTIONS_DIR/04-part2-foundational-concepts-revised.md" ]; then
    add_section "04-part2-foundational-concepts-revised.md"
    echo "    (Using revised version with manifesto energy)"
else
    add_section "04-part2-foundational-concepts.md"
fi

# Use enhanced Part 3 if it exists
if [ -f "$SECTIONS_DIR/05-part3-value-trust-mechanics-enhanced.md" ]; then
    add_section "05-part3-value-trust-mechanics-enhanced.md"
    echo "    (Using enhanced version with manifesto flourishes)"
else
    add_section "05-part3-value-trust-mechanics.md"
fi
add_section "06-part4-implications-vision.md"

# Use conceptual version for memory if it exists
if [ -f "$SECTIONS_DIR/07-part5-memory-conceptual.md" ]; then
    add_section "07-part5-memory-conceptual.md"
    echo "    (Using conceptual version)"
else
    add_section "07-part5-memory-temporal-sensing.md"
fi

add_section "08-part6-blockchain-typology.md"

# Add implementation details before examples
if [ -f "$SECTIONS_DIR/09-part7-implementation-details.md" ]; then
    add_section "09-part7-implementation-details.md"
    echo "    (Including implementation mechanisms)"
fi

add_section "09-part7-implementation-examples.md"
add_section "10-part8-web4-context.md"

# Use enhanced conclusion if it exists
if [ -f "$SECTIONS_DIR/11-conclusion-enhanced.md" ]; then
    add_section "11-conclusion-enhanced.md"
    echo "    (Using enhanced conclusion with call to action)"
else
    add_section "11-conclusion.md"
fi
add_section "12-references.md"
add_section "13-appendices.md"

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
    
    # Copy to docs/whitepaper-web for GitHub Pages access
    DOCS_DIR="../docs/whitepaper-web"
    if [ ! -d "$DOCS_DIR" ]; then
        mkdir -p "$DOCS_DIR"
        echo "📁 Created docs/whitepaper-web directory"
    fi
    
    cp "$OUTPUT_FILE" "$DOCS_DIR/"
    echo "📄 Copied markdown to GitHub Pages location: $DOCS_DIR/WEB4_Whitepaper_Complete.md"
fi