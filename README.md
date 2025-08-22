# WEB4: The Trust-Native Internet

> *Where trust is earned, not granted. Where value flows to genuine contribution. Where humans and artificial intelligences collaborate as peers.*

---

## What is WEB4?

WEB4 represents a fundamental reconception of the internet—from platform-controlled (Web2) and token-speculated (Web3) to **trust-native** and **intelligence-distributed**. 

At its core, WEB4 makes trust the fundamental force of digital interaction, like gravity in physics, binding intelligent entities into coherent systems that learn, remember, and evolve through genuine interaction rather than central declaration.

## 📚 Read the Whitepaper

The comprehensive Web4 whitepaper is available in three formats (always current):

### **[📄 Markdown Version](https://dp-web4.github.io/web4/whitepaper-web/WEB4_Whitepaper_Complete.md)**
Complete technical document for reading in any markdown viewer or text editor

### **[📕 PDF Version](https://dp-web4.github.io/web4/whitepaper-web/WEB4_Whitepaper.pdf)**
Professional formatting for offline reading, printing, or sharing

### **[🌐 Web Version](https://dp-web4.github.io/web4/whitepaper-web/)**
Interactive HTML with navigation, search, and responsive design  
*Also available locally at: [whitepaper/build/web/index.html](whitepaper/build/web/index.html)*

---

## Core Concepts

### 🔑 Linked Context Tokens (LCTs)
The **reification of presence itself**. Every entity—human, AI, or hybrid—gains an unforgeable footprint in the digital realm. Your LCT is born with you, lives through your actions, and bears witness to your contributions. It cannot be stolen, sold, or transferred. It is you, crystallized in cryptographic reality.

### ⚡ Alignment Transfer Protocol (ATP)
Energy becomes value through a biological metaphor made digital. Like ATP in living cells, our protocol tracks energy expenditure and value creation in a continuous cycle. Work consumes energy, creating value, which when recognized by others, generates new energy. This is not mining or staking—it's genuine contribution recognized by genuine benefit.

### 🧠 Memory as Temporal Sensor
Memory doesn't just record the past—it **senses** it. Alongside physical sensors (spatial) and cognitive sensors (future projection), memory as temporal sensor creates the complete reality field where intelligence operates. Every interaction leaves a trace, every trace can be witnessed, and every witness strengthens the fabric of collective trust.

### 📊 T3 and V3 Tensors
**Trust** and **Value** become measurable, multidimensional:
- **T3 (Trust Tensor)**: Talent, Training, Temperament—capturing an entity's capabilities
- **V3 (Value Tensor)**: Valuation, Veracity, Validity—measuring created value

### 🌐 Markov Relevancy Horizon (MRH)
Each entity's contextual lens—defining what is knowable, actionable, and relevant within their scope. Not everything is relevant to everyone at all times. The MRH ensures efficient, focused interaction.

### 🔗 Fractal Lightchain Architecture
Hierarchical witness-based verification that scales from nanosecond cell operations to permanent blockchain anchors—all without global consensus bottlenecks. Trust emerges from witnessed interactions at every scale.

### ⚡ LRC Governance Model
A physics-inspired governance system where change resistance emerges from natural dynamics. Components have inductance (change resistance), capacitance (experimentation potential), and resistance (quality filtering), creating self-balancing systems. This README describes the Web4 instantiation while LRC provides the stack-agnostic transfer layer. [Learn more →](LRC_GOVERNANCE.md)

---

## A Worked Example

*Imagine a human researcher and an AI collaborator co-authoring a paper. Their roles, trust, and contributions are tracked seamlessly through LCTs. Every edit and validation flows through ATP, consuming energy when work is done, generating new energy when value is recognized. Their MRHs keep focus at the right scope: local edits for the AI, long-term framing for the human. The T3 tensors ensure each contributes where they're strongest. Together, they produce work that is verifiable, witnessed, and trusted—without any central authority. The paper itself becomes an entity with its own LCT, accumulating reputation as others cite and build upon it.*

---

## Key Innovations

### Trust Through Witnessing
Trust emerges from accumulated witnessed interactions. Every action creates a witness mark, every witness can be acknowledged, creating bidirectional proof without global consensus.

### Entities Beyond Users
Anything with presence can be an entity: humans, AIs, organizations, roles, tasks, even thoughts. Each gets an LCT, making them first-class participants in the trust network.

### Memory as Living History
Memory actively perceives temporal patterns, building trust through witnessed experience. It's not storage—it's the sense that makes time itself tangible.

### Four-Tier Blockchain Typology
- **Compost** (milliseconds): Ephemeral working memory
- **Leaf** (seconds-minutes): Short-term episodic memory
- **Stem** (minutes-hours): Consolidated patterns
- **Root** (permanent): Crystallized wisdom

---

## Project Structure

```
web4/
├── whitepaper/           # Modular whitepaper sections
│   ├── sections/         # Individual document sections
│   ├── build/           # Generated outputs (MD, PDF, HTML)
│   └── log/             # Changelog and development notes
├── reference/           # Reference materials and archives
├── forum/              # Community discussions
├── trust/              # Trust system implementations
└── integration/        # Cross-project integration logs
```

---

## Implementation Status

🚧 **Active Development** - The Web4 framework is evolving through collaborative implementation.

### Current Focus
- Production lightchain protocol implementation
- SAGE (Sentient Agentic Generative Engine) integration
- Memory sensor standardization
- Cross-project integration with HRM, Memory, and AI-DNA Discovery

### Related Projects
- [HRM](https://github.com/dp-web4/HRM) - Hierarchical Reasoning Model (SAGE foundation)
- [Memory](https://github.com/dp-web4/Memory) - Lightchain and memory paradigms
- [AI-DNA Discovery](https://github.com/dp-web4/ai-dna-discovery) - Sensor fusion experiments

---

## Get Involved

This is not a product to purchase or a platform to join. This is a living fabric we weave together.

**Whether you are a researcher, builder, or dreamer—your perspective is needed.**

### Contributing
- Review the [whitepaper](whitepaper/build/WEB4_Whitepaper_Complete.md)
- Explore [implementation examples](whitepaper/sections/09-part7-implementation-examples.md)
- Join the discussion in [forum](forum/)
- Implement protocols in your preferred language

### Building the Whitepaper
```bash
cd whitepaper
./make-md.sh   # Build markdown version
./make-pdf.sh  # Build PDF version
./make-web.sh  # Build web version
```

### Additional Resources
- [LRC Governance (Derived Principles layer)](LRC_GOVERNANCE.md) - Stack-agnostic governance transfer layer
- [Governance Dashboard](governance/dashboard.md) - Visual overview of section protection levels
- [Governance Manifesto](reference/GOVERNANCE_MANIFESTO.md) - Distributed governance vision
- [Synchronism Framework](https://dpcars.net/synchronism) - Philosophical foundations
- [Changelog](whitepaper/log/CHANGELOG.md) - Track whitepaper evolution

### Governance Evolution

The Web4 project uses the LRC governance model to manage change resistance across different components. View the [Governance Dashboard](governance/dashboard.md) to see current protection levels.

#### Future Governance Considerations
As the project grows, we may adopt additional governance infrastructure from Nova's proposals:
- **Cross-repository alignment** - Ensuring consistency across Synchronism, Web4, SAGE, and other implementations
- **Drift detection** - Automated CI/CD checks for governance parameter divergence
- **Coupling rules** - Formal propagation requirements for high-L changes across related projects
- **Witness marks** - Standardized approval signatures across all repos
- **PR automation** - Bot-computed governance controls for touched sections

See `forum/nova/governance-extras/` for detailed proposals that may be adopted as needed.

### Contact
📩 **dp@metalinxx.io**

We invite thoughtful critique, aligned contribution, and resonant imagination.

---

## Patents and Licensing

The LCT framework is protected by U.S. patents [US11477027](https://patents.google.com/patent/US11477027B1) and [US12278913](https://patents.google.com/patent/US12278913B1), ensuring foundational mechanisms are recognized while preserving public benefit deployment.

Core implementations will be released under the **GNU Affero General Public License (AGPL)**, fostering an open, auditable, and collaboratively stewarded ecosystem.

---

## Vision

In Web4:
- **You don't just have an account**—you have presence
- **You don't just perform roles**—you inhabit them
- **You don't just interact**—you leave footprints in the fabric of digital reality itself

The revolution is not in the technology alone, but in what becomes possible when every interaction carries verifiable trust, every contribution creates measurable value, and every intelligence—human or artificial—can participate as a respected peer in our collective evolution.

> *"Memory witnessed becomes memory trusted. Memory trusted becomes knowledge shared. Knowledge shared becomes intelligence distributed."*

**This is the invitation: to help shape the trust-native fabric of our shared digital future.**

---

**[📄 Read Whitepaper (Markdown)](https://dp-web4.github.io/web4/whitepaper-web/WEB4_Whitepaper_Complete.md)** | **[📕 Download PDF](https://dp-web4.github.io/web4/whitepaper-web/WEB4_Whitepaper.pdf)** | **[🌐 View Interactive Version](https://dp-web4.github.io/web4/whitepaper-web/)**

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

### Key Points:
- ✅ **Open Source**: Source code is freely available
- ✅ **Network Copyleft**: If you run a modified version as a network service, you must provide source code
- ✅ **Patent Protection**: Includes patent grant and termination clauses
- ✅ **Commercial Use**: Allowed, but modifications must remain open source

See [LICENSE](LICENSE) file for full terms.

### Why AGPL?
Web4's trust-native architecture requires transparency. The AGPL ensures that:
- Trust mechanisms remain verifiable
- Improvements benefit the entire ecosystem
- Network effects strengthen rather than fragment the protocol
- No entity can create closed, proprietary versions of core trust infrastructure

For commercial implementations that require different licensing, please contact the maintainers.