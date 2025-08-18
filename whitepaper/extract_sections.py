#!/usr/bin/env python3

import re
import os

# Read the original whitepaper
with open('../WEB4_Whitepaper_MarkedUp_with_Intro.md', 'r') as f:
    content = f.read()

# Define section boundaries based on headers
sections = {
    '04-part2-foundational-concepts.md': {
        'start': '## 2. Foundational Concepts and Entities in WEB4',
        'end': '## 3. Value, Trust, and Capability Mechanics',
        'content': ''
    },
    '05-part3-value-trust-mechanics.md': {
        'start': '## 3. Value, Trust, and Capability Mechanics',
        'end': '## 4.2. The Future of Work',
        'content': ''
    },
    '06-part4-implications-vision.md': {
        'start': '## 4.2. The Future of Work',
        'end': '## 5. WEB4 in Context',
        'content': ''
    },
    '10-part8-web4-context.md': {
        'start': '## 5. WEB4 in Context',
        'end': None,  # Goes to end of file
        'content': ''
    }
}

# Extract sections
for filename, section_info in sections.items():
    start_pattern = section_info['start']
    end_pattern = section_info['end']
    
    # Find start position
    start_match = content.find(start_pattern)
    if start_match == -1:
        print(f"Warning: Could not find start pattern for {filename}")
        continue
    
    # Find end position
    if end_pattern:
        end_match = content.find(end_pattern, start_match)
        if end_match == -1:
            print(f"Warning: Could not find end pattern for {filename}")
            continue
        section_content = content[start_match:end_match]
    else:
        section_content = content[start_match:]
    
    # Clean up content
    section_content = section_content.strip()
    
    # Save to file
    output_path = f'sections/{filename}'
    with open(output_path, 'w') as f:
        # Add header for Part sections
        if 'part2' in filename:
            f.write('# Part 2: Foundational Concepts and Entities\n\n')
        elif 'part3' in filename:
            f.write('# Part 3: Value, Trust, and Capability Mechanics\n\n')
        elif 'part4' in filename:
            f.write('# Part 4: Implications and Vision\n\n')
        elif 'part8' in filename:
            f.write('# Part 8: WEB4 in Context\n\n')
        
        f.write(section_content)
    
    print(f"✓ Created {filename}")

print("\nExtraction complete!")