#!/bin/bash

# Create meta subdirectories and files for each section
for dir in */; do
    if [ -d "$dir" ]; then
        # Create meta subdirectory
        mkdir -p "${dir}meta"
        
        # Create proposals subdirectory
        mkdir -p "${dir}meta/proposals"
        
        # Create reviews subdirectory
        mkdir -p "${dir}meta/reviews"
        
        # Create changelog file
        cat > "${dir}meta/CHANGELOG.md" << 'EOF'
# Section Changelog

## Format
Each entry should include:
- Date
- Author (LCT ID)
- Change type (ADD/MODIFY/DELETE)
- Description
- Rationale

## Entries
<!-- Add entries below -->
EOF
        
        # Create section metadata file
        section_name=$(basename "$dir")
        cat > "${dir}meta/metadata.json" << EOF
{
  "section_id": "$section_name",
  "maintainers": [],
  "last_modified": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "active",
  "dependencies": [],
  "tags": [],
  "review_cycle": {
    "frequency": "quarterly",
    "last_review": null,
    "next_review": null
  }
}
EOF
        
        echo "Created meta files for: $dir"
    fi
done

echo "Meta structure creation complete!"