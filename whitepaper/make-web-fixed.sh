#!/bin/bash

# make-web-fixed.sh - Generate navigable web version with all content
# Usage: ./make-web-fixed.sh

echo "Building Web4 whitepaper web version with navigation..."

OUTPUT_DIR="build/web"
BUILD_DIR="build"
ASSETS_DIR="$OUTPUT_DIR/assets"

# Create output directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$ASSETS_DIR"

# Check if markdown version exists
if [ ! -f "$BUILD_DIR/WEB4_Whitepaper_Complete.md" ]; then
    echo "Error: Run ./make-md.sh first to generate the complete markdown"
    exit 1
fi

# Create CSS file
cat > "$ASSETS_DIR/style.css" << 'CSS'
/* Web4 Whitepaper Styles */
:root {
    --primary-color: #374151;
    --secondary-color: #64748b;
    --background: #ffffff;
    --text-color: #1e293b;
    --border-color: #e2e8f0;
    --code-bg: #f8fafc;
    --sidebar-width: 280px;
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
    background: var(--background);
}

/* Layout */
.container {
    display: flex;
    min-height: 100vh;
}

/* Sidebar Navigation */
.sidebar {
    width: var(--sidebar-width);
    background: #f8fafc;
    border-right: 1px solid var(--border-color);
    padding: 2rem 1rem;
    position: fixed;
    height: 100vh;
    overflow-y: auto;
}

.sidebar h2 {
    font-size: 1.2rem;
    margin-bottom: 1rem;
    color: var(--primary-color);
}

.nav-list {
    list-style: none;
}

.nav-list li {
    margin-bottom: 0.5rem;
}

.nav-list a {
    color: var(--text-color);
    text-decoration: none;
    padding: 0.5rem 1rem;
    display: block;
    border-radius: 4px;
    transition: all 0.2s;
    font-size: 0.9rem;
}

.nav-list a:hover {
    background: white;
    color: var(--primary-color);
}

.nav-list a.active {
    background: var(--primary-color);
    color: white;
}

/* Main Content */
.main-content {
    margin-left: var(--sidebar-width);
    flex: 1;
    padding: 3rem;
    max-width: 900px;
}

/* Section Pages */
.section {
    display: none;
    animation: fadeIn 0.3s;
}

.section.active {
    display: block;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Typography */
h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: var(--primary-color);
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.5rem;
}

h2 {
    font-size: 2rem;
    margin: 2rem 0 1rem;
    color: var(--text-color);
}

h3 {
    font-size: 1.5rem;
    margin: 1.5rem 0 0.75rem;
    color: var(--text-color);
}

h4 {
    font-size: 1.25rem;
    margin: 1rem 0 0.5rem;
    color: var(--text-color);
}

p {
    margin-bottom: 1rem;
    line-height: 1.8;
}

/* Lists */
ul, ol {
    margin: 1rem 0 1rem 2rem;
}

li {
    margin-bottom: 0.5rem;
}

/* Code */
code {
    background: var(--code-bg);
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
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

/* Tables */
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
    font-weight: 600;
}

/* Blockquotes */
blockquote {
    border-left: 4px solid var(--primary-color);
    padding-left: 1rem;
    margin: 1rem 0;
    color: var(--secondary-color);
    font-style: italic;
}

/* Links */
a {
    color: var(--primary-color);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
    color: #1f2937;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .sidebar {
        width: 100%;
        height: auto;
        position: relative;
        border-right: none;
        border-bottom: 1px solid var(--border-color);
    }
    
    .main-content {
        margin-left: 0;
        padding: 2rem 1rem;
    }
    
    .container {
        flex-direction: column;
    }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
    :root {
        --background: #0f172a;
        --text-color: #e2e8f0;
        --border-color: #334155;
        --code-bg: #1e293b;
    }
    
    .sidebar {
        background: #1e293b;
    }
    
    .nav-list a:hover {
        background: #334155;
    }
    
    th {
        background: #1e293b;
    }
}

/* Print Styles */
@media print {
    .sidebar {
        display: none;
    }
    
    .main-content {
        margin-left: 0;
        padding: 0;
        max-width: 100%;
    }
    
    .section {
        display: block !important;
        page-break-after: always;
    }
}
CSS

echo "  ✓ Created CSS styles"

# Create JavaScript for navigation
cat > "$ASSETS_DIR/navigation.js" << 'JAVASCRIPT'
// Web4 Whitepaper Navigation
document.addEventListener('DOMContentLoaded', function() {
    // Get all navigation links and sections
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');
    
    // Function to show a specific section
    function showSection(sectionId) {
        // Hide all sections
        sections.forEach(section => {
            section.classList.remove('active');
        });
        
        // Remove active class from all nav links
        navLinks.forEach(link => {
            link.classList.remove('active');
        });
        
        // Show the selected section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
            
            // Mark the corresponding nav link as active
            const targetLink = document.querySelector(`[data-section="${sectionId}"]`);
            if (targetLink) {
                targetLink.classList.add('active');
            }
            
            // Update URL hash
            window.location.hash = sectionId;
            
            // Scroll to top of content
            window.scrollTo(0, 0);
        }
    }
    
    // Add click handlers to navigation links
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const sectionId = this.getAttribute('data-section');
            showSection(sectionId);
        });
    });
    
    // Handle direct URL access with hash
    function handleHashChange() {
        const hash = window.location.hash.slice(1);
        if (hash) {
            showSection(hash);
        } else {
            // Show first section by default
            showSection('executive-summary');
        }
    }
    
    // Handle browser back/forward buttons
    window.addEventListener('hashchange', handleHashChange);
    
    // Initialize on page load
    handleHashChange();
});
JAVASCRIPT

echo "  ✓ Created JavaScript navigation"

# Now create the HTML with actual content sections
echo "Converting markdown to HTML sections..."

# First, read the complete markdown and split it into sections
python3 << 'PYTHON_SCRIPT'
import re
import html

def escape_html(text):
    """Escape HTML special characters"""
    return html.escape(text)

def markdown_to_html(text):
    """Convert markdown to HTML"""
    # Save code blocks first to protect them
    code_blocks = []
    def save_code_block(match):
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(code_blocks)-1}__"
    
    text = re.sub(r'```[\s\S]*?```', save_code_block, text)
    
    # Convert headers
    text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Bold and italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^\*\n]+?)\*', r'<em>\1</em>', text)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Lists
    lines = text.split('\n')
    result = []
    in_ul = False
    in_ol = False
    
    for line in lines:
        if re.match(r'^- ', line):
            if not in_ul:
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append('<ul>')
                in_ul = True
            result.append('<li>' + line[2:] + '</li>')
        elif re.match(r'^\d+\. ', line):
            if not in_ol:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                result.append('<ol>')
                in_ol = True
            result.append('<li>' + re.sub(r'^\d+\. ', '', line) + '</li>')
        else:
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            result.append(line)
    
    if in_ul:
        result.append('</ul>')
    if in_ol:
        result.append('</ol>')
    
    text = '\n'.join(result)
    
    # Blockquotes
    text = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
    
    # Horizontal rules
    text = re.sub(r'^---+$', r'<hr>', text, flags=re.MULTILINE)
    
    # Restore code blocks
    for i, code_block in enumerate(code_blocks):
        match = re.match(r'```(\w*)\n(.*?)```', code_block, re.DOTALL)
        if match:
            lang = match.group(1) or ''
            code = escape_html(match.group(2))
            replacement = f'<pre><code class="{lang}">{code}</code></pre>'
        else:
            replacement = code_block
        text = text.replace(f"__CODE_BLOCK_{i}__", replacement)
    
    # Paragraphs
    lines = text.split('\n')
    result = []
    in_tag = False
    para_lines = []
    
    for line in lines:
        if line.strip().startswith('<') or not line.strip():
            if para_lines:
                result.append('<p>' + ' '.join(para_lines) + '</p>')
                para_lines = []
            result.append(line)
        else:
            para_lines.append(line)
    
    if para_lines:
        result.append('<p>' + ' '.join(para_lines) + '</p>')
    
    return '\n'.join(result)

# Read the complete markdown
with open('build/WEB4_Whitepaper_Complete.md', 'r') as f:
    content = f.read()

# Define sections and their IDs
sections = [
    ('Executive Summary', 'executive-summary', r'# Executive Summary.*?(?=# |## |$)'),
    ('Introduction', 'introduction', r'# Introduction.*?(?=# Glossary|$)'),
    ('Glossary', 'glossary', r'# Glossary.*?(?=# Part 1:|$)'),
    ('Part 1: Defining Web4', 'part1', r'# Part 1:.*?(?=# Part 2:|$)'),
    ('Part 2: Foundational Concepts', 'part2', r'# Part 2:.*?(?=# Part 3:|$)'),
    ('Part 3: Value & Trust', 'part3', r'# Part 3:.*?(?=# Part 4:|$)'),
    ('Part 4: Implications', 'part4', r'# Part 4:.*?(?=# Part 5:|$)'),
    ('Part 5: Memory', 'part5', r'# Part 5:.*?(?=# Part 6:|$)'),
    ('Part 6: Blockchain', 'part6', r'# Part 6:.*?(?=# Part 7:|$)'),
    ('Part 7: Implementation', 'part7', r'# Part 7:.*?(?=# Part 8:|$)'),
    ('Part 8: Web4 Context', 'part8', r'# Part 8:.*?(?=# Conclusion|$)'),
    ('Conclusion', 'conclusion', r'# Conclusion.*?(?=# References|$)'),
    ('References', 'references', r'# References.*?(?=# Appendices|$)'),
    ('Appendices', 'appendices', r'# Appendices.*?$'),
]

# Start building HTML
html_output = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WEB4: Trust-Native Distributed Intelligence</title>
    <meta name="description" content="WEB4 Whitepaper - A comprehensive architecture for trust-native distributed intelligence">
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <div class="container">
        <!-- Sidebar Navigation -->
        <nav class="sidebar">
            <h2>WEB4 Whitepaper</h2>
            
            <!-- Navigation List -->
            <ul class="nav-list">'''

# Add navigation items
for title, section_id, _ in sections:
    html_output += f'''
                <li><a href="#{section_id}" class="nav-link" data-section="{section_id}">{title}</a></li>'''

html_output += '''
            </ul>
            
            <!-- Download Links -->
            <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                <h3 style="font-size: 1rem; margin-bottom: 0.5rem;">Downloads</h3>
                <a href="../WEB4_Whitepaper.pdf" download style="display: block; margin-bottom: 0.5rem;">📄 PDF Version</a>
                <a href="../WEB4_Whitepaper_Complete.md" download style="display: block;">📝 Markdown Version</a>
            </div>
        </nav>
        
        <!-- Main Content Area -->
        <main class="main-content">'''

# Extract and convert each section
for title, section_id, pattern in sections:
    match = re.search(pattern, content, re.DOTALL)
    if match:
        section_content = match.group(0)
        section_html = markdown_to_html(section_content)
        html_output += f'''
            <section id="{section_id}" class="section">
                {section_html}
            </section>'''
    else:
        # Fallback: try to find section by title
        print(f"Warning: Could not find section '{title}' with pattern")

html_output += '''
        </main>
    </div>
    
    <!-- Scripts -->
    <script src="assets/navigation.js"></script>
</body>
</html>'''

# Write the HTML file
with open('build/web/index.html', 'w') as f:
    f.write(html_output)

print("✓ Created main HTML file with all sections")
PYTHON_SCRIPT

echo ""
echo "✅ Web version with navigation created successfully!"
echo ""
echo "📊 Output Structure:"
echo "   build/web/"
echo "   ├── index.html (main file with all content)"
echo "   ├── assets/"
echo "   │   ├── style.css"
echo "   │   └── navigation.js"
echo ""
echo "🚀 To test: open build/web/index.html in a browser"