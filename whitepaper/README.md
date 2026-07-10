# Web4 Whitepaper - Modular Documentation

This directory contains the modular, maintainable version of the Web4 whitepaper.

## Structure

```
whitepaper/
├── sections/           # One DIRECTORY per section, content in index.md
│   ├── 01-title-authors/index.md              # Title page
│   ├── 02-why-web4/index.md                   # The stakes (why)
│   ├── 03-the-equation/index.md               # Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
│   ├── 04-mcp/index.md                        # Equation element 1: the I/O membrane
│   ├── 05-rdf/index.md                        # Element 2: the ontological backbone
│   ├── 06-lct/index.md                        # Element 3: the presence substrate
│   ├── 07-t3v3/index.md                       # Element 4: trust & value tensors
│   ├── 08-mrh/index.md                        # Element 5: the relevancy horizon
│   ├── 09-atp-adp/index.md                    # Element 6: the value-feedback cycle
│   ├── 10-composed-architecture/index.md      # R6/R7, roles, societies/SAL/AGY/ACP, dictionaries
│   ├── 11-standard-and-implementations/index.md  # web4-standard + hub + hestia repo links
│   ├── 12-conclusion/index.md                 # Wrap-up, legal, invitation
│   ├── 13-glossary/index.md                   # Compact reference glossary
│   └── 14-references/index.md
│   # reading order is defined by the add_section calls in make-md.sh, not by dir names
│   # pre-2026-07-09 sections archived at archive/sections-2026-07-09-pre-rewrite/
├── build/             # Generated output (git-ignored)
│   ├── WEB4_Whitepaper_Complete.md
│   ├── WEB4_Whitepaper.pdf
│   └── web/
├── make-md.sh         # Combine sections into monolithic markdown
├── make-pdf.sh        # Generate PDF version
└── make-web.sh        # Generate web version for metalinxx.io
```

## Usage

### Generate Monolithic Markdown
```bash
./make-md.sh
```
Creates `build/WEB4_Whitepaper_Complete.md` by combining all sections.

### Generate PDF
```bash
./make-pdf.sh
```
Creates `build/WEB4_Whitepaper.pdf` with proper formatting.

**Requirements for PDF generation:**
- **Option 1 (Best)**: pandoc + LaTeX
  ```bash
  # Ubuntu/Debian
  sudo apt-get install pandoc texlive-xetex
  
  # macOS
  brew install pandoc basictex
  ```

- **Option 2**: wkhtmltopdf
  ```bash
  sudo apt-get install wkhtmltopdf
  ```

- **Option 3**: Python libraries
  ```bash
  pip install markdown pdfkit
  ```

### Generate Web Version
```bash
./make-web.sh
```
Creates `build/web/` directory with navigable HTML version.

## Editing Guidelines

### Adding a New Section

1. Create a new file in `sections/` with appropriate numbering
2. Follow the existing naming convention: `XX-section-name.md`
3. Update the build scripts if the section should appear in a different order

### Updating Existing Sections

Simply edit the relevant file in `sections/`. The modular structure ensures changes to one section don't affect others unless explicitly intended.

### Section Dependencies

Some sections reference others. When making major changes:
- **02-foundational-concepts.md**: Core definitions used throughout
- **03-blockchain-typology.md**: Referenced in implementation examples
- **04-entity-architecture.md**: Foundation for SAGE discussions

## Key Concepts by Section

### Foundational Concepts (02)
- Three-Sensor Reality Field
- Linked Context Tokens (LCTs)
- Trust Through Witnessing

### Blockchain Typology (03)
- Four-Chain Hierarchy (Compost, Leaf, Stem, Root)
- Fractal Lightchain Implementation
- Memory Operation Energy Cycles

### Entity Architecture (04)
- SAGE as Fractal Web4 Instance
- Entity Types (Sensor, Memory, Cognitive, Dictionary)
- Dual Memory Architecture

### Implementation Examples (05)
- Multi-Agent Memory Synchronization
- Autonomous Vehicle Fleet Learning
- SAGE Coherence Through Three Sensors

## Deployment

### To metalinxx.io

1. Generate the web version:
   ```bash
   ./make-web.sh
   ```

2. Upload the contents of `build/web/` to the server

3. Ensure proper permissions and update any absolute paths

### Version Control

The `build/` directory is git-ignored. Only source sections are tracked. This ensures:
- Clean version history
- No merge conflicts in generated files
- Smaller repository size

## Recent Updates (August 18, 2025)

- **Memory as Temporal Sensor**: Reconceptualized memory as active temporal perception
- **Fractal Lightchain**: Added witness-acknowledgment bidirectional proof system
- **Blockchain Typology**: Introduced four-tier temporal hierarchy
- **SAGE Integration**: Incorporated HRM and three-sensor coherence model

## Contributing

When contributing to the whitepaper:

1. Edit only the relevant section files
2. Run `./make-md.sh` to verify your changes compile correctly
3. Test the web version locally with `./make-web.sh`
4. Commit only the section files, not the build output

## Contact

For questions or contributions:
- GitHub: https://github.com/dp-web4/web4 (open an issue or PR)