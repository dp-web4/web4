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
