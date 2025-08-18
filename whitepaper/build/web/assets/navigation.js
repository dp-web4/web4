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
