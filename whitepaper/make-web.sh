#!/bin/bash

# make-web.sh - Generate navigable web version of whitepaper
# Usage: ./make-web.sh

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

echo "Building Web4 whitepaper web version..."

# Guard: the md->HTML converter uses the Python `markdown` library; WITHOUT it,
# it silently falls back to a regex hack that DROPS every [text](url) link and
# mangles tables (this shipped link-broken HTML to production before this guard).
# Ensure the module is present — install if missing, hard-fail rather than degrade.
if ! python3 -c 'import markdown' 2>/dev/null; then
  echo "  'markdown' module missing — attempting install…"
  python3 -m pip install --quiet --break-system-packages markdown 2>/dev/null \
    || python3 -m pip install --quiet --user markdown 2>/dev/null || true
  if ! python3 -c 'import markdown' 2>/dev/null; then
    echo "❌ ERROR: Python 'markdown' module is required for correct HTML (links/tables)" >&2
    echo "   and could not be auto-installed. Run 'pip install markdown' and retry." >&2
    echo "   Refusing to generate link-broken HTML." >&2
    exit 1
  fi
fi

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
        extensions = ['extra', 'codehilite', 'toc', 'tables', 'fenced_code', 'attr_list']
    except ImportError:
        # Fallback to basic conversion
        extensions = []
    
    with open(md_file, 'r') as f:
        content = f.read()
    
    # Process headers to add IDs for navigation
    import re
    
    # Function to create ID from header text
    def make_id(text):
        # Remove section numbers and clean up
        text = re.sub(r'^[\d\.]+\s*', '', text)
        # Convert to lowercase and replace spaces with hyphens
        return text.lower().replace(' ', '-').replace(':', '')
    
    if extensions:
        # Use the markdown library with proper extensions
        md = markdown.Markdown(extensions=extensions)
        html = md.convert(content)
        
        # Add specific IDs for foundational concepts
        # Match exact patterns from the HTML output
        html = html.replace(
            '<p><h2>2.1. Linked Context Tokens (LCTs): The Reification of Presence</h2></p>',
            '<h2 id="lcts">2.1. Linked Context Tokens (LCTs): The Reification of Presence</h2>'
        )
        
        html = html.replace(
            '<p><h2>2.2. Entities in the WEB4 Framework</h2></p>',
            '<h2 id="entities">2.2. Entities in the WEB4 Framework</h2>'
        )
        
        html = html.replace(
            '<p><h2>2.3. Roles as First-Class Entities</h2></p>',
            '<h2 id="roles">2.3. Roles as First-Class Entities</h2>'
        )
        
        html = html.replace(
            '<p><h2>2.4. The R6 Action Framework: Where Intent Becomes Reality</h2></p>',
            '<h2 id="r6">2.4. The R6 Action Framework: Where Intent Becomes Reality</h2>'
        )
        
        html = html.replace(
            '<p><h2>2.5. Markov Relevancy Horizon (MRH): The Lens of Context</h2></p>',
            '<h2 id="mrh">2.5. Markov Relevancy Horizon (MRH): The Lens of Context</h2>'
        )
        
        html = html.replace(
            '<p><h2>2.6. Dictionaries: The Living Keepers of Meaning</h2></p>',
            '<h2 id="dictionaries">2.6. Dictionaries: The Living Keepers of Meaning</h2>'
        )
        
        # Fix headers that got wrapped in paragraph tags AFTER replacements
        html = re.sub(r'<p>(<h[123])', r'\1', html)
        html = re.sub(r'(</h[123]>)</p>', r'\1', html)
        
        # Also handle case where entire header is inside paragraph
        html = re.sub(r'<p><h([123])>(.*?)</h\1></p>', r'<h\1>\2</h\1>', html)
        
        # Remove any {#id} artifacts that got through
        html = re.sub(r'\s*\{#\w+\}', '', html)
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

/* Expandable Navigation */
.expandable {
    position: relative;
}

.expand-icon {
    display: inline-block;
    transition: transform 0.3s ease;
    margin-left: 0.5rem;
    font-size: 0.8rem;
    float: right;
    margin-top: 0.2rem;
}

.expandable.expanded .expand-icon {
    transform: rotate(90deg);
}

.sub-nav {
    list-style: none;
    padding: 0;
    margin: 0 0 0 1.5rem;
    overflow: hidden;
    transition: all 0.3s ease;
}

.sub-nav-link {
    font-size: 0.9rem !important;
    padding: 0.4rem 0.75rem !important;
    opacity: 0.9;
}

.sub-nav-link:hover {
    opacity: 1;
    background: white !important;
}

.sub-nav-link.active {
    background: var(--secondary-color) !important;
    color: white !important;
    opacity: 1;
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

/* Table of Contents within sections */
.section-toc {
    background: #f8fafc;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 1rem;
    margin: 1rem 0 2rem 0;
}

.section-toc h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
    color: var(--primary-color);
}

.section-toc ul {
    list-style: none;
    margin: 0;
    padding: 0;
}

.section-toc li {
    margin: 0.25rem 0;
}

.section-toc a {
    color: var(--secondary-color);
    text-decoration: none;
    display: block;
    padding: 0.25rem 0.5rem;
    border-radius: 3px;
    transition: all 0.2s;
}

.section-toc a:hover {
    background: white;
    color: var(--primary-color);
    text-decoration: none;
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
    
    .section-toc {
        display: none;
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
    
    // Handle expandable navigation
    const expandableToggles = document.querySelectorAll('.expandable-toggle');
    expandableToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            // Check if we clicked on the main link, not a sub-link
            if (!e.target.closest('.sub-nav')) {
                const expandable = this.closest('.expandable');
                const subNav = expandable.querySelector('.sub-nav');
                
                // Toggle expanded state
                expandable.classList.toggle('expanded');
                if (expandable.classList.contains('expanded')) {
                    subNav.style.display = 'block';
                } else {
                    subNav.style.display = 'none';
                }
                
                // Still navigate to the section
                const sectionId = this.getAttribute('data-section');
                if (sectionId) {
                    showSection(sectionId);
                }
            }
        });
    });
    
    // Handle sub-navigation clicks
    const subNavLinks = document.querySelectorAll('.sub-nav-link');
    subNavLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const sectionId = this.getAttribute('data-section');
            const targetId = this.getAttribute('data-target');
            
            // Show the section first
            showSection(sectionId);
            
            // Then scroll to the specific subsection after a brief delay
            setTimeout(() => {
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    // If no element with that ID, try to find a header containing the text
                    const headers = document.querySelectorAll('h2, h3');
                    headers.forEach(h => {
                        if (h.id === targetId || h.textContent.toLowerCase().includes(targetId.replace('-', ' '))) {
                            h.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    });
                }
            }, 200);
            
            // Update active states
            document.querySelectorAll('.sub-nav-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
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
        
        // Check if hash corresponds to a section ID
        const validSectionIds = Array.from(navLinks).map(link => link.getAttribute('data-section'));
        
        if (hash && validSectionIds.includes(hash)) {
            // This is a section navigation
            showSection(hash);
        } else if (hash && document.getElementById(hash)) {
            // This is a header within a section - just scroll to it
            const targetHeader = document.getElementById(hash);
            const parentSection = targetHeader.closest('.section');
            
            if (parentSection && !parentSection.classList.contains('active')) {
                // First show the section containing this header
                const sectionId = parentSection.id;
                showSection(sectionId);
                
                // Then scroll to the header after a brief delay
                setTimeout(() => {
                    targetHeader.scrollIntoView({ behavior: 'smooth' });
                }, 100);
            } else {
                // Section is already active, just scroll
                targetHeader.scrollIntoView({ behavior: 'smooth' });
            }
        } else if (!hash) {
            // Show first section by default
            showSection('why-web4');
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
            
            headers.forEach((header, index) => {
                // Generate ID if header doesn't have one
                if (!header.id) {
                    header.id = header.textContent
                        .toLowerCase()
                        .replace(/[^\w\s-]/g, '') // Remove special characters
                        .replace(/\s+/g, '-')     // Replace spaces with dashes
                        .replace(/--+/g, '-')     // Replace multiple dashes with single
                        .trim();
                    
                    // Ensure unique IDs by adding section prefix
                    header.id = section.id + '-' + header.id;
                }
                
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#' + header.id;
                a.textContent = header.textContent;
                a.className = 'toc-link'; // Add class to distinguish from nav links
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
    <title>WEB4: A Technical Introduction</title>
    <meta name="description" content="WEB4 Whitepaper - a technical introduction to the trust-native internet, explained through its canonical equation">
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
            
            <!-- Navigation List (flat: one entry per section — nav ids MUST match the
                 `sections` array below; a nav entry without a matching real section is
                 the bug class that made links land on the wrong content) -->
            <ul class="nav-list">
                <li><a href="#why-web4" class="nav-link active" data-section="why-web4">Why Web4</a></li>
                <li><a href="#the-equation" class="nav-link" data-section="the-equation">The Canonical Equation</a></li>
                <li><a href="#mcp" class="nav-link" data-section="mcp">MCP: The I/O Membrane</a></li>
                <li><a href="#rdf" class="nav-link" data-section="rdf">RDF: The Ontological Backbone</a></li>
                <li><a href="#lct" class="nav-link" data-section="lct">LCT: The Presence Substrate</a></li>
                <li><a href="#t3v3" class="nav-link" data-section="t3v3">T3/V3: Trust &amp; Value Tensors</a></li>
                <li><a href="#mrh" class="nav-link" data-section="mrh">MRH: The Relevancy Horizon</a></li>
                <li><a href="#atp-adp" class="nav-link" data-section="atp-adp">ATP/ADP: The Value Cycle</a></li>
                <li><a href="#composed" class="nav-link" data-section="composed">Built on the Foundation</a></li>
                <li><a href="#standard" class="nav-link" data-section="standard">Standard &amp; Implementations</a></li>
                <li><a href="#conclusion" class="nav-link" data-section="conclusion">Conclusion</a></li>
                <li><a href="#glossary" class="nav-link" data-section="glossary">Glossary</a></li>
                <li><a href="#references" class="nav-link" data-section="references">References</a></li>
            </ul>
            
            <!-- Download Links -->
            <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                <h3 style="font-size: 1rem; margin-bottom: 0.5rem;">Downloads</h3>
                <a href="WEB4_Whitepaper.pdf" download style="display: block; margin-bottom: 0.5rem;">📄 PDF Version</a>
                <a href="WEB4_Whitepaper_Complete.md" download style="display: block;">📝 Markdown Version</a>
            </div>
        </nav>
        
        <!-- Main Content Area -->
        <main class="main-content">
            <!-- Header -->
            <header>
                <h1>WEB4: A Technical Introduction</h1>
                <p style="color: var(--secondary-color); margin-bottom: 2rem;">
                    <em>The trust-native internet, explained through its canonical equation</em><br>
                    <em>Updated: July 9, 2026</em><br>
                    <em>Authors: Dennis Palatov, GPT4o, Deepseek, Grok, Claude, Gemini, Manus</em>
                </p>
            </header>
            
            <!-- Content Sections (dynamically populated) -->
HTML

# Convert each section to HTML and add to index
echo "Converting sections to HTML..."

# Process sections in order (2026-07-09 rewrite: equation-ordered technical introduction).
# Section ids here MUST match the nav-list data-section values above, 1:1.
sections=(
    "02-why-web4/index.md:why-web4"
    "03-the-equation/index.md:the-equation"
    "04-mcp/index.md:mcp"
    "05-rdf/index.md:rdf"
    "06-lct/index.md:lct"
    "07-t3v3/index.md:t3v3"
    "08-mrh/index.md:mrh"
    "09-atp-adp/index.md:atp-adp"
    "10-composed-architecture/index.md:composed"
    "11-standard-and-implementations/index.md:standard"
    "12-conclusion/index.md:conclusion"
    "13-glossary/index.md:glossary"
    "14-references/index.md:references"
)

# Process each section in order
for entry in "${sections[@]}"; do
    IFS=':' read -r file section_id <<< "$entry"

    if [ -f "$SECTIONS_DIR/$file" ]; then
        # First section (why-web4) is the default active/visible one
        if [ "$section_id" = "why-web4" ]; then
            echo "            <section id=\"$section_id\" class=\"section active\">" >> "$OUTPUT_DIR/index.html"
        else
            echo "            <section id=\"$section_id\" class=\"section\">" >> "$OUTPUT_DIR/index.html"
        fi

        # Convert markdown to HTML and append
        md_to_html "$SECTIONS_DIR/$file" "$OUTPUT_DIR/temp_section.html"

        cat "$OUTPUT_DIR/temp_section.html" >> "$OUTPUT_DIR/index.html"
        rm "$OUTPUT_DIR/temp_section.html"

        echo "            </section>" >> "$OUTPUT_DIR/index.html"
    else
        echo "  ⚠ WARNING: $SECTIONS_DIR/$file missing — nav entry '$section_id' would be dead" >&2
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