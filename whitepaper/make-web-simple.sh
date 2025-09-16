#!/bin/bash

# make-web-simple.sh - Generate simple single-page web version of whitepaper
# Usage: ./make-web-simple.sh

echo "Building Web4 whitepaper web version (simple)..."

OUTPUT_DIR="build/web"
BUILD_DIR="build"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if markdown version exists
if [ ! -f "$BUILD_DIR/WEB4_Whitepaper_Complete.md" ]; then
    echo "Error: Run ./make-md.sh first to generate the complete markdown"
    exit 1
fi

# Create simple HTML with embedded content
cat > "$OUTPUT_DIR/index.html" << 'HTML_START'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WEB4: Trust-Native Distributed Intelligence</title>
    <style>
        :root {
            --primary-color: #2563eb;
            --text-color: #1e293b;
            --bg-color: #ffffff;
            --code-bg: #f8fafc;
            --border-color: #e2e8f0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background: var(--bg-color);
            padding: 2rem;
            max-width: 900px;
            margin: 0 auto;
        }
        
        h1 {
            color: var(--primary-color);
            margin: 2rem 0 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--border-color);
        }
        
        h2 {
            color: var(--primary-color);
            margin: 2rem 0 1rem;
        }
        
        h3 {
            margin: 1.5rem 0 0.75rem;
        }
        
        p {
            margin-bottom: 1rem;
        }
        
        ul, ol {
            margin: 1rem 0 1rem 2rem;
        }
        
        li {
            margin-bottom: 0.5rem;
        }
        
        code {
            background: var(--code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: monospace;
        }
        
        pre {
            background: var(--code-bg);
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            margin: 1rem 0;
            border: 1px solid var(--border-color);
        }
        
        pre code {
            background: none;
            padding: 0;
        }
        
        blockquote {
            border-left: 4px solid var(--primary-color);
            padding-left: 1rem;
            margin: 1rem 0;
            font-style: italic;
            color: #64748b;
        }
        
        a {
            color: var(--primary-color);
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        hr {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 2rem 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border: 1px solid var(--border-color);
        }
        
        th {
            background: var(--code-bg);
        }
        
        /* Navigation */
        .nav-header {
            position: sticky;
            top: 0;
            background: var(--bg-color);
            padding: 1rem 0;
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--border-color);
        }
        
        .nav-links {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        .nav-links a {
            padding: 0.5rem 1rem;
            background: var(--code-bg);
            border-radius: 4px;
        }
        
        .nav-links a:hover {
            background: var(--primary-color);
            color: white;
            text-decoration: none;
        }
        
        /* Dark mode */
        @media (prefers-color-scheme: dark) {
            :root {
                --text-color: #e2e8f0;
                --bg-color: #0f172a;
                --code-bg: #1e293b;
                --border-color: #334155;
            }
        }
        
        /* Mobile */
        @media (max-width: 768px) {
            body {
                padding: 1rem;
            }
        }
        
        /* Print */
        @media print {
            .nav-header {
                display: none;
            }
            body {
                padding: 0;
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="nav-header">
        <div class="nav-links">
            <a href="../WEB4_Whitepaper.pdf">📄 Download PDF</a>
            <a href="../WEB4_Whitepaper_Complete.md">📝 Download Markdown</a>
            <a href="https://github.com/dp-web4/web4">🔗 GitHub</a>
        </div>
    </div>
    
    <div id="content">
HTML_START

# Convert markdown to HTML using Python if available
if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import re
import sys

def markdown_to_html(text):
    # Headers
    text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Bold and italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Code blocks
    def replace_code_block(match):
        lang = match.group(1) or ''
        code = match.group(2)
        # HTML escape
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<pre><code class="{lang}">{code}</code></pre>'
    
    text = re.sub(r'```(\w*)\n(.*?)```', replace_code_block, text, flags=re.DOTALL)
    
    # Blockquotes
    text = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
    
    # Horizontal rules
    text = re.sub(r'^---$', r'<hr>', text, flags=re.MULTILINE)
    
    # Lists
    lines = text.split('\n')
    in_list = False
    result = []
    
    for line in lines:
        if re.match(r'^- ', line):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append('<li>' + line[2:] + '</li>')
        elif re.match(r'^\d+\. ', line):
            if not in_list:
                result.append('<ol>')
                in_list = True
            result.append('<li>' + re.sub(r'^\d+\. ', '', line) + '</li>')
        else:
            if in_list:
                if result[-1].startswith('<ul>'):
                    result.append('</ul>')
                else:
                    result.append('</ol>')
                in_list = False
            if line.strip() and not line.startswith('<'):
                result.append('<p>' + line + '</p>')
            else:
                result.append(line)
    
    if in_list:
        if result[-1].startswith('<ul>'):
            result.append('</ul>')
        else:
            result.append('</ol>')
    
    return '\n'.join(result)

# Read markdown
with open('build/WEB4_Whitepaper_Complete.md', 'r') as f:
    content = f.read()

# Convert to HTML
html = markdown_to_html(content)

# Output
print(html)
PYTHON_SCRIPT
else
    # Fallback: just wrap in pre tags
    echo "<pre>"
    cat "$BUILD_DIR/WEB4_Whitepaper_Complete.md"
    echo "</pre>"
fi >> "$OUTPUT_DIR/index.html"

# Close HTML
cat >> "$OUTPUT_DIR/index.html" << 'HTML_END'
    </div>
</body>
</html>
HTML_END

echo "✅ Simple web version created: $OUTPUT_DIR/index.html"
echo ""
echo "This is a single-page version with all content embedded."
echo "To test: open $OUTPUT_DIR/index.html in a browser"