# Compression Trust Unification — Diagram (Mermaid)

```mermaid
graph TD
  %% Core Principle
  A[Compression Trust]:::core --> B[Shared / Aligned Latent Fields]:::core
  B --> C[Meaningful Communication]:::core

  %% Human Language Path
  subgraph H[Human Language]
    H1[Experience] --> H2[Concept Formation (latent manifold)]
    H2 --> H3[Word Token]
    H3 --> H4[Listener Embedding / Meaning Reconstruction]
  end
  B -. enables .-> H2
  H3 -. relies on .-> B

  %% VAE Path (Continuous)
  subgraph V[VAE (Continuous)]
    V1[Input (image/sensor)] --> V2[Encoder μ,σ → z ∈ R^d]
    V2 --> V3[Latent Vector (continuous)]
    V3 --> V4[Decoder → Reconstruction]
  end
  V3 -->|index/search| V5[Vector DB]
  V5 -->|nearest-neighbor| V6[Recall / Similarity]
  B -. alignment governs fidelity .-> V3

  %% VQ-VAE Path (Discrete)
  subgraph Q[VQ-VAE (Discrete)]
    Q1[Input] --> Q2[Encoder → z_enc]
    Q2 --> Q3[Nearest Codebook Entry e_i]
    Q3 --> Q4[Token ID i]
    Q4 --> Q5[Decoder(e_i) → Reconstruction]
  end
  B -. shared codebook .-> Q3

  %% Web4 Dictionary Entities + LCTs
  subgraph W[Web4]
    W1[Dictionary Entity (Codebook)] --> W2[ID ↔ Embedding Mapping]
    W3[LCT: Linked Context Token] --> W4[Provenance • Trust • Alignment]
  end
  Q3 -->|uses| W1
  Q4 -->|is| W2
  W3 -->|wraps| Q4
  W3 -->|wraps| V3
  W4 -. informs .-> B

  %% Synchronism & SAGE/IRP
  subgraph S[Synchronism & SAGE/IRP]
    S1[Witness MRH] --> S2[Compression (IRP)]
    S2 --> S3[VAE / VQ-VAE Tokens]
    S3 --> S4[SNARC Memory]
  end
  S3 -->|index| V5
  W3 -->|attaches| S4
  B -. governs exchange .-> S3

  classDef core fill:#222,color:#fff,stroke:#999,stroke-width:1px;
```
