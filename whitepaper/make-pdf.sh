#!/bin/bash

# make-pdf-better.sh - Generate PDF with TOC after Executive Summary
# Usage: ./make-pdf-better.sh

echo "Building Web4 whitepaper PDF with improved layout..."

OUTPUT_DIR="build"
MD_FILE="$OUTPUT_DIR/WEB4_Whitepaper_Complete.md"
PDF_FILE="$OUTPUT_DIR/WEB4_Whitepaper.pdf"
TEMP_MD="$OUTPUT_DIR/WEB4_Whitepaper_Reordered.md"

# Create build directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# First, ensure we have the markdown file
if [ ! -f "$MD_FILE" ]; then
    echo "Markdown file not found. Running make-md.sh first..."
    ./make-md.sh
fi

# Check for pandoc
if ! command -v pandoc &> /dev/null; then
    echo "Error: pandoc is required for PDF generation"
    echo "Install with: sudo apt-get install pandoc texlive-xetex"
    exit 1
fi

# Reorder the document to put TOC after Executive Summary
echo "Reordering document structure..."
python3 << 'PYTHON_SCRIPT'
import re

# Read the complete markdown
with open('build/WEB4_Whitepaper_Complete.md', 'r') as f:
    content = f.read()

# Split into sections
lines = content.split('\n')
sections = []
current_section = []
current_title = ""

for line in lines:
    if line.startswith('# '):
        if current_section:
            sections.append((current_title, '\n'.join(current_section)))
        current_title = line
        current_section = [line]
    else:
        current_section.append(line)

# Add the last section
if current_section:
    sections.append((current_title, '\n'.join(current_section)))

# Find Executive Summary
exec_summary = None
other_sections = []

for title, content in sections:
    if 'Executive Summary' in title:
        exec_summary = (title, content)
    else:
        other_sections.append((title, content))

# Rebuild document with custom order
with open('build/WEB4_Whitepaper_Reordered.md', 'w') as f:
    # Title and authors (if exists)
    for title, content in other_sections:
        if 'WEB4:' in title or 'Trust-Native' in title:
            f.write(content + '\n\n')
            other_sections.remove((title, content))
            break
    
    # Executive Summary
    if exec_summary:
        f.write(exec_summary[1] + '\n\n')
    
    # Add TOC marker for pandoc
    f.write('\\newpage\n\n')
    f.write('\\tableofcontents\n\n')
    f.write('\\newpage\n\n')
    
    # All other sections
    for title, content in other_sections:
        f.write(content + '\n\n')

print("✓ Document reordered")
PYTHON_SCRIPT

# Generate PDF with pandoc
echo "Generating PDF..."
pandoc "$TEMP_MD" -o "$PDF_FILE" \
    --from markdown+raw_tex \
    --to pdf \
    --pdf-engine=xelatex \
    --toc-depth=3 \
    --highlight-style=tango \
    -V documentclass=report \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V linkcolor=blue \
    -V urlcolor=blue \
    -V toccolor=black \
    -V colorlinks=true \
    --metadata title="WEB4: Trust-Native Distributed Intelligence" \
    --metadata author="Dennis Palatov et al." \
    --metadata date="August 2025" \
    2>/dev/null

if [ -f "$PDF_FILE" ]; then
    echo "✅ PDF created with TOC after Executive Summary: $PDF_FILE"
    echo ""
    echo "📊 PDF Statistics:"
    echo "   Size: $(du -h $PDF_FILE | cut -f1)"
    echo "   Location: $PDF_FILE"
    
    # Clean up temp file
    rm -f "$TEMP_MD"
else
    echo "❌ PDF generation failed"
    echo "Falling back to standard generation..."
    
    # Fallback to original method
    pandoc "$MD_FILE" -o "$PDF_FILE" \
        --from markdown \
        --to pdf \
        --pdf-engine=xelatex \
        --toc \
        --toc-depth=3 \
        --highlight-style=tango \
        -V geometry:margin=1in \
        -V fontsize=11pt
    
    if [ -f "$PDF_FILE" ]; then
        echo "✅ PDF created (standard layout): $PDF_FILE"
    fi
fi