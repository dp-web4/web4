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
    # Start with title and Executive Summary on same page
    f.write('# WEB4: A Comprehensive Architecture for Trust-Native Distributed Intelligence\n\n')
    f.write('*Dennis Palatov, GPT4o, Deepseek, Grok, Claude, Gemini, Manus*\n\n')
    f.write('*August 2025*\n\n')
    f.write('---\n\n')
    
    # Executive Summary (without its own title since we have main title)
    if exec_summary:
        # Remove the "# Executive Summary" line from content
        exec_content = exec_summary[1].replace('# Executive Summary', '## Executive Summary')
        f.write(exec_content + '\n\n')
    
    # Add TOC on new page
    f.write('\\newpage\n\n')
    f.write('\\tableofcontents\n\n')
    f.write('\\newpage\n\n')
    
    # All other sections (skip any title sections we already handled)
    for title, content in other_sections:
        if 'WEB4:' not in title and 'Trust-Native' not in title:
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
    -V documentclass=article \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V linkcolor=blue \
    -V urlcolor=blue \
    -V toccolor=black \
    -V colorlinks=true \
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