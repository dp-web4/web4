#!/bin/bash

# make-pdf.sh - Convert whitepaper to PDF with proper formatting
# Usage: ./make-pdf.sh

echo "Building Web4 whitepaper PDF..."

OUTPUT_DIR="build"
MD_FILE="$OUTPUT_DIR/WEB4_Whitepaper_Complete.md"
PDF_FILE="$OUTPUT_DIR/WEB4_Whitepaper.pdf"
TEMP_TEX="$OUTPUT_DIR/temp_whitepaper.tex"

# Create build directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# First, ensure we have the markdown file
if [ ! -f "$MD_FILE" ]; then
    echo "Markdown file not found. Running make-md.sh first..."
    ./make-md.sh
fi

# Check for required tools
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "⚠ Warning: $1 is not installed. Trying alternative method..."
        return 1
    fi
    return 0
}

# Method 1: Using pandoc with LaTeX (best quality)
if check_tool pandoc; then
    echo "Using pandoc for PDF generation..."
    
    # Create custom LaTeX template for better formatting
    cat > "$OUTPUT_DIR/template.tex" << 'EOF'
\documentclass[11pt,a4paper]{article}
\usepackage[margin=1in]{geometry}
\usepackage{hyperref}
\usepackage{graphicx}
\usepackage{listings}
\usepackage{color}
\usepackage{fancyhdr}
\usepackage{titlesec}

% Code highlighting
\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},
    commentstyle=\color{codegreen},
    keywordstyle=\color{magenta},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,
    breaklines=true,
    captionpos=b,
    keepspaces=true,
    numbers=left,
    numbersep=5pt,
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    tabsize=2
}

\lstset{style=mystyle}

% Headers and footers
\pagestyle{fancy}
\fancyhf{}
\rhead{WEB4 Whitepaper}
\lhead{\leftmark}
\cfoot{\thepage}

% Section formatting
\titleformat{\section}
  {\normalfont\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}
  {\normalfont\large\bfseries}{\thesubsection}{1em}{}

\title{WEB4: A Comprehensive Architecture for Trust-Native Distributed Intelligence}
\author{Dennis Palatov, GPT4o, Deepseek, Grok, Claude, Gemini, Manus}
\date{\today}

\begin{document}
\maketitle
\tableofcontents
\newpage

$body$

\end{document}
EOF

    # Generate PDF with pandoc
    pandoc "$MD_FILE" \
        --from markdown \
        --to pdf \
        --pdf-engine=xelatex \
        --highlight-style=tango \
        --toc \
        --toc-depth=3 \
        --number-sections \
        -V geometry:margin=1in \
        -V fontsize=11pt \
        -V documentclass=article \
        -V colorlinks=true \
        -V linkcolor=blue \
        -V urlcolor=blue \
        -V toccolor=black \
        -o "$PDF_FILE" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "✅ PDF created with pandoc: $PDF_FILE"
    else
        echo "Pandoc failed. Trying alternative method..."
        
        # Method 2: Using wkhtmltopdf (fallback)
        if check_tool wkhtmltopdf; then
            echo "Using wkhtmltopdf for PDF generation..."
            
            # First convert markdown to HTML
            if check_tool markdown; then
                markdown "$MD_FILE" > "$OUTPUT_DIR/temp.html"
            elif check_tool python3; then
                python3 -c "
import markdown
with open('$MD_FILE', 'r') as f:
    html = markdown.markdown(f.read(), extensions=['extra', 'codehilite', 'toc'])
with open('$OUTPUT_DIR/temp.html', 'w') as f:
    f.write('''
<html>
<head>
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
h1, h2, h3 { color: #333; }
code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #f2f2f2; }
</style>
</head>
<body>
''' + html + '''
</body>
</html>
''')
"
            fi
            
            wkhtmltopdf "$OUTPUT_DIR/temp.html" "$PDF_FILE"
            rm -f "$OUTPUT_DIR/temp.html"
            echo "✅ PDF created with wkhtmltopdf: $PDF_FILE"
        else
            # Method 3: Using Python libraries (last resort)
            echo "Trying Python method..."
            python3 << 'PYTHON_SCRIPT'
import os
import sys

try:
    from markdown2pdf import convert
    convert(f"{os.environ.get('OUTPUT_DIR')}/WEB4_Whitepaper_Complete.md",
            f"{os.environ.get('OUTPUT_DIR')}/WEB4_Whitepaper.pdf")
    print("✅ PDF created with Python markdown2pdf")
except ImportError:
    try:
        import markdown
        import pdfkit
        
        with open(f"{os.environ.get('OUTPUT_DIR')}/WEB4_Whitepaper_Complete.md", 'r') as f:
            html = markdown.markdown(f.read())
        
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None
        }
        
        pdfkit.from_string(html, f"{os.environ.get('OUTPUT_DIR')}/WEB4_Whitepaper.pdf", options=options)
        print("✅ PDF created with Python pdfkit")
    except ImportError:
        print("⚠ No PDF generation tools available.")
        print("Please install one of the following:")
        print("  - pandoc (recommended): apt-get install pandoc texlive-xetex")
        print("  - wkhtmltopdf: apt-get install wkhtmltopdf")
        print("  - Python libraries: pip install markdown2pdf pdfkit")
        sys.exit(1)
PYTHON_SCRIPT
        fi
    fi
else
    echo "⚠ pandoc not found. Please install pandoc for best PDF quality:"
    echo "  Ubuntu/Debian: sudo apt-get install pandoc texlive-xetex"
    echo "  macOS: brew install pandoc basictex"
    echo ""
    echo "Alternatively, install wkhtmltopdf or Python libraries."
fi

# Clean up temporary files
rm -f "$OUTPUT_DIR/template.tex" "$OUTPUT_DIR/temp_whitepaper.tex"

# Show file info
if [ -f "$PDF_FILE" ]; then
    size=$(du -h "$PDF_FILE" | cut -f1)
    echo ""
    echo "📊 PDF Statistics:"
    echo "   Size: $size"
    echo "   Location: $PDF_FILE"
fi