# Compression Trust Calibration — Cross-Entity Alignment (Mermaid)

```mermaid
flowchart TD
  %% Entities
  subgraph E1[Entity A]
    A1[Local Input]
    A2[Encode → z_A]
    A3[Quantize / Tokenize → ID_A]
    A4[Dictionary_A]
  end

  subgraph E2[Entity B]
    B1[Local Input]
    B2[Encode → z_B]
    B3[Quantize / Tokenize → ID_B]
    B4[Dictionary_B]
  end

  %% Shared / Exchange
  A3 --> X[Exchange: Token IDs or Latents]
  B3 --> X
  X -->|interpret| A4
  X -->|interpret| B4

  %% Calibration
  subgraph CAL[Compression Trust Calibration]
    C1[Alignment Metric<br/>(cosine similarity / KL divergence / Earth Mover's)]
    C2[Provenance Check<br/>(LCT metadata)]
    C3[Mapping Layer<br/>(Dictionary_A ↔ Dictionary_B)]

    C1 --> C4[Trust Score 0..1]
    C2 --> C4
    C3 --> C4
  end

  %% Flows
  A4 -->|align| C3
  B4 -->|align| C3

  X -->|evaluate| C1
  X -->|validate| C2

  C4 -->|informs| TRUST[Compression Trust Established]

  %% Style
  classDef core fill:#222,color:#fff,stroke:#999,stroke-width:1px;
  class E1,E2,CAL core;
```
