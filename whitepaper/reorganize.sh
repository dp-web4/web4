#!/bin/bash

# Script to reorganize whitepaper sections properly
# This creates a mapping between the old monolithic structure and new modular sections

echo "Reorganizing Web4 Whitepaper sections..."

# Clean up old incorrect sections (keep the good ones)
rm -f sections/00-metadata.md
rm -f sections/01-executive-summary.md
rm -f sections/02-foundational-concepts.md
rm -f sections/03-blockchain-typology.md
rm -f sections/04-entity-architecture.md
rm -f sections/05-implementation-examples.md
rm -f sections/06-security-privacy.md
rm -f sections/07-performance.md
rm -f sections/08-future-directions.md
rm -f sections/09-philosophical-implications.md
rm -f sections/10-conclusion.md
rm -f sections/11-references.md
rm -f sections/12-appendices.md
rm -f sections/13-contact.md

echo "✓ Cleaned up old sections"

# The proper structure should be:
# 00-introduction.md (already created)
# 01-title-authors.md (already created)
# 02-glossary.md (already created)
# 03-part1-defining-web4.md (already created)
# 04-part2-foundational-concepts.md
# 05-part3-value-trust-mechanics.md
# 06-part4-implications-vision.md
# 07-part5-memory-temporal-sensing.md (NEW - our additions)
# 08-part6-blockchain-typology.md (NEW - our additions)
# 09-part7-implementation-examples.md (NEW - our additions)
# 10-part8-web4-context.md
# 11-conclusion.md
# 12-references.md
# 13-appendices.md

echo "New structure created. Sections need to be populated from original content."
echo ""
echo "Sections to create:"
echo "  ✓ 00-introduction.md"
echo "  ✓ 01-title-authors.md"
echo "  ✓ 02-glossary.md"
echo "  ✓ 03-part1-defining-web4.md"
echo "  ⚠ 04-part2-foundational-concepts.md"
echo "  ⚠ 05-part3-value-trust-mechanics.md"
echo "  ⚠ 06-part4-implications-vision.md"
echo "  ⚠ 07-part5-memory-temporal-sensing.md"
echo "  ⚠ 08-part6-blockchain-typology.md"
echo "  ⚠ 09-part7-implementation-examples.md"
echo "  ⚠ 10-part8-web4-context.md"
echo "  ⚠ 11-conclusion.md"
echo "  ⚠ 12-references.md"
echo "  ⚠ 13-appendices.md"