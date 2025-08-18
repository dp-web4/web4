#!/bin/bash

# make-web.sh - Generate navigable web version of whitepaper
# Usage: ./make-web.sh

echo "Building Web4 whitepaper web version..."

OUTPUT_DIR="build/web"
SECTIONS_DIR="sections"
ASSETS_DIR="$OUTPUT_DIR/assets"

# Create output directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$ASSETS_DIR"

# Function to convert markdown to HTML with syntax highlighting
md_to_html() {
    local input=$1
    local output=$2
    
    if command -v python3 &> /dev/null; then
        python3 << PYTHON_SCRIPT
import re
import json

def convert_md_to_html(md_file, html_file):
    try:
        import markdown
        extensions = ['extra', 'codehilite', 'toc', 'tables', 'fenced_code']
    except ImportError:
        # Fallback to basic conversion
        extensions = []
    
    with open(md_file, 'r') as f:
        content = f.read()
    
    if extensions:
        html = markdown.markdown(content, extensions=extensions)
    else:
        # Basic conversion without markdown library
        html = content
        # Convert headers
        html = re.sub(r'^### (.+)$', r'<h3>\\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\\1</h1>', html, flags=re.MULTILINE)
        # Convert code blocks
        html = re.sub(r'\`\`\`(\w+)?\n(.*?)\`\`\`', r'<pre><code class="\\1">\\2</code></pre>', html, flags=re.DOTALL)
        # Convert inline code
        html = re.sub(r'\`([^\`]+)\`', r'<code>\\1</code>', html)
        # Convert bold
        html = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\\1</strong>', html)
        # Convert italic
        html = re.sub(r'\*([^\*]+)\*', r'<em>\\1</em>', html)
        # Convert lists
        html = re.sub(r'^- (.+)$', r'<li>\\1</li>', html, flags=re.MULTILINE)
        # Convert paragraphs
        html = '<p>' + html.replace('\\n\\n', '</p><p>') + '</p>'
    
    with open(html_file, 'w') as f:
        f.write(html)

convert_md_to_html('$input', '$output')
print("  ✓ Converted $(basename $input)")
PYTHON_SCRIPT
    else
        # Fallback to simple copy if Python not available
        cp "$input" "$output"
        echo "  ⚠ Python not available, copied raw markdown"
    fi
}

# Create main CSS file
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
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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
    
    // Add search functionality
    const searchBox = document.getElementById('search-box');
    if (searchBox) {
        searchBox.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            
            sections.forEach(section => {
                const content = section.textContent.toLowerCase();
                const matches = content.includes(query);
                
                // Highlight matching sections in navigation
                const sectionId = section.id;
                const navLink = document.querySelector(`[data-section="${sectionId}"]`);
                
                if (navLink) {
                    if (query && matches) {
                        navLink.style.background = '#fef3c7';
                    } else {
                        navLink.style.background = '';
                    }
                }
            });
        });
    }
    
    // Add table of contents generation for each section
    sections.forEach(section => {
        const headers = section.querySelectorAll('h2, h3');
        if (headers.length > 2) {
            const toc = document.createElement('div');
            toc.className = 'section-toc';
            toc.innerHTML = '<h4>In this section:</h4><ul></ul>';
            
            headers.forEach(header => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#' + header.id;
                a.textContent = header.textContent;
                li.appendChild(a);
                toc.querySelector('ul').appendChild(li);
            });
            
            // Insert TOC after first h2
            const firstH2 = section.querySelector('h2');
            if (firstH2) {
                firstH2.parentNode.insertBefore(toc, firstH2.nextSibling);
            }
        }
    });
});

// Add copy code button to code blocks
document.addEventListener('DOMContentLoaded', function() {
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(block => {
        const button = document.createElement('button');
        button.className = 'copy-code-btn';
        button.textContent = 'Copy';
        
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(block.textContent).then(() => {
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = 'Copy';
                }, 2000);
            });
        });
        
        block.parentNode.style.position = 'relative';
        block.parentNode.appendChild(button);
    });
});
JAVASCRIPT

echo "  ✓ Created JavaScript navigation"

# Create main HTML file
cat > "$OUTPUT_DIR/index.html" << 'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WEB4: Trust-Native Distributed Intelligence</title>
    <meta name="description" content="WEB4 Whitepaper - A comprehensive architecture for trust-native distributed intelligence">
    <link rel="stylesheet" href="assets/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
</head>
<body>
    <div class="container">
        <!-- Sidebar Navigation -->
        <nav class="sidebar">
            <h2>WEB4 Whitepaper</h2>
            
            <!-- Search Box -->
            <input type="text" id="search-box" placeholder="Search..." style="width: 100%; padding: 0.5rem; margin-bottom: 1rem; border: 1px solid var(--border-color); border-radius: 4px;">
            
            <!-- Navigation List -->
            <ul class="nav-list">
                <li><a href="#executive-summary" class="nav-link" data-section="executive-summary">Executive Summary</a></li>
                <li><a href="#foundational-concepts" class="nav-link" data-section="foundational-concepts">Foundational Concepts</a></li>
                <li><a href="#blockchain-typology" class="nav-link" data-section="blockchain-typology">Blockchain Typology</a></li>
                <li><a href="#entity-architecture" class="nav-link" data-section="entity-architecture">Entity Architecture</a></li>
                <li><a href="#implementation" class="nav-link" data-section="implementation">Implementation Examples</a></li>
                <li><a href="#security" class="nav-link" data-section="security">Security & Privacy</a></li>
                <li><a href="#performance" class="nav-link" data-section="performance">Performance</a></li>
                <li><a href="#future" class="nav-link" data-section="future">Future Directions</a></li>
                <li><a href="#philosophy" class="nav-link" data-section="philosophy">Philosophical Implications</a></li>
                <li><a href="#conclusion" class="nav-link" data-section="conclusion">Conclusion</a></li>
                <li><a href="#references" class="nav-link" data-section="references">References</a></li>
                <li><a href="#appendices" class="nav-link" data-section="appendices">Appendices</a></li>
            </ul>
            
            <!-- Download Links -->
            <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                <h3 style="font-size: 1rem; margin-bottom: 0.5rem;">Downloads</h3>
                <a href="../WEB4_Whitepaper.pdf" download style="display: block; margin-bottom: 0.5rem;">📄 PDF Version</a>
                <a href="../WEB4_Whitepaper_Complete.md" download style="display: block;">📝 Markdown Version</a>
            </div>
        </nav>
        
        <!-- Main Content Area -->
        <main class="main-content">
            <!-- Header -->
            <header>
                <h1>WEB4: A Comprehensive Architecture for Trust-Native Distributed Intelligence</h1>
                <p style="color: var(--secondary-color); margin-bottom: 2rem;">
                    <em>Updated: August 18, 2025</em><br>
                    <em>Authors: Dennis Palatov, GPT4o, Deepseek, Grok, Claude, Gemini, Manus</em>
                </p>
            </header>
            
            <!-- Content Sections (dynamically populated) -->
HTML

# Convert each section to HTML and add to index
echo "Converting sections to HTML..."

# Section mapping
declare -A section_map=(
    ["01-executive-summary.md"]="executive-summary"
    ["02-foundational-concepts.md"]="foundational-concepts"
    ["03-blockchain-typology.md"]="blockchain-typology"
    ["04-entity-architecture.md"]="entity-architecture"
    ["05-implementation-examples.md"]="implementation"
    ["06-security-privacy.md"]="security"
    ["07-performance.md"]="performance"
    ["08-future-directions.md"]="future"
    ["09-philosophical-implications.md"]="philosophy"
    ["10-conclusion.md"]="conclusion"
    ["11-references.md"]="references"
    ["12-appendices.md"]="appendices"
)

# Process each section
for file in "${!section_map[@]}"; do
    section_id="${section_map[$file]}"
    if [ -f "$SECTIONS_DIR/$file" ]; then
        echo "            <section id=\"$section_id\" class=\"section\">" >> "$OUTPUT_DIR/index.html"
        
        # Convert markdown to HTML and append
        md_to_html "$SECTIONS_DIR/$file" "$OUTPUT_DIR/temp_section.html"
        cat "$OUTPUT_DIR/temp_section.html" >> "$OUTPUT_DIR/index.html"
        rm "$OUTPUT_DIR/temp_section.html"
        
        echo "            </section>" >> "$OUTPUT_DIR/index.html"
    fi
done

# Close HTML
cat >> "$OUTPUT_DIR/index.html" << 'HTML'
        </main>
    </div>
    
    <!-- Scripts -->
    <script src="assets/navigation.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
</body>
</html>
HTML

echo "  ✓ Created main HTML file"

# Create a simple README for the web directory
cat > "$OUTPUT_DIR/README.md" << 'README'
# Web4 Whitepaper - Web Version

This directory contains the web-ready version of the Web4 whitepaper.

## Files

- `index.html` - Main HTML file with all content
- `assets/style.css` - Styling for the web version
- `assets/navigation.js` - JavaScript for section navigation

## Deployment

To deploy to metalinxx.io:

1. Upload the entire `web` directory contents to the server
2. Ensure the directory is accessible at the desired URL
3. Update any absolute paths if necessary

## Features

- Responsive design for mobile and desktop
- Section-based navigation
- Search functionality
- Code syntax highlighting
- Dark mode support
- Print-friendly CSS

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
README

echo "  ✓ Created README for web directory"

echo ""
echo "✅ Web version created successfully!"
echo ""
echo "📊 Output Structure:"
echo "   $OUTPUT_DIR/"
echo "   ├── index.html (main file)"
echo "   ├── assets/"
echo "   │   ├── style.css"
echo "   │   └── navigation.js"
echo "   └── README.md"
echo ""
echo "🚀 To deploy:"
echo "   1. Test locally: open $OUTPUT_DIR/index.html in a browser"
echo "   2. Upload entire 'web' directory to metalinxx.io"
echo "   3. Ensure proper permissions and paths"

# Copy to docs/whitepaper-web for GitHub Pages access
echo ""
echo "📋 Copying to GitHub Pages location..."
DOCS_DIR="../docs/whitepaper-web"
if [ ! -d "$DOCS_DIR" ]; then
    mkdir -p "$DOCS_DIR"
    echo "📁 Created docs/whitepaper-web directory"
fi

# Copy all web files
cp -r "$OUTPUT_DIR/"* "$DOCS_DIR/"
echo "🌐 Copied web files to: $DOCS_DIR/"

# Also ensure PDF and MD versions are there
if [ -f "../build/WEB4_Whitepaper.pdf" ]; then
    cp "../build/WEB4_Whitepaper.pdf" "$DOCS_DIR/"
    echo "📕 Copied PDF to GitHub Pages location"
fi

if [ -f "../build/WEB4_Whitepaper_Complete.md" ]; then
    cp "../build/WEB4_Whitepaper_Complete.md" "$DOCS_DIR/"
    echo "📄 Copied markdown to GitHub Pages location"
fi

echo ""
echo "✅ GitHub Pages deployment ready at: https://dp-web4.github.io/web4/whitepaper-web/"