# Visual Tokenizer Path — VAE, VQ‑VAE, and Dictionary Entities (Mermaid)

```mermaid
flowchart TD
  %% Inputs
  X[Perceptual Input<br/>(image / crop / sensor)]

  %% VAE branch (continuous)
  subgraph VAE[VAE — Continuous Latent]
    direction LR
    V1[Encoder: μ, σ] --> V2[z ∈ R^d<br/>(continuous latent)]
    V2 --> V3[Decoder → Reconstruction]
  end

  %% VQ-VAE branch (discrete)
  subgraph VQVAE[VQ‑VAE — Discrete Codes]
    direction LR
    Q1[Encoder → z_enc] --> Q2[Nearest Codebook Entry e_i]
    Q2 --> Q3[Token ID i]
    Q3 --> Q4[Decoder(e_i) → Reconstruction]
  end

  %% Dictionary Entities + LCT
  subgraph WEB4[Web4 Dictionary Entities]
    direction TB
    D1[Dictionary Entity<br/>(Shared Codebook)]
    D2[ID ↔ Embedding Mapping]
    D3[LCT Wrapper<br/>(provenance • trust • alignment)]
  end

  %% Vector DB (optional)
  subgraph VDB[Vector DB (optional)]
    direction TB
    B1[Store Latents / IDs + Metadata]
    B2[Similarity Search / Recall]
  end

  %% Flows
  X --> V1
  X --> Q1

  %% VAE connections
  V2 -->|store| B1
  V2 -.wrapped by .-> D3

  %% VQ-VAE connections
  Q2 -->|uses| D1
  Q3 -->|is| D2
  Q3 -->|store| B1
  Q3 -.wrapped by .-> D3

  %% Retrieval path
  B2 -->|nearest| V2
  B2 -->|IDs| Q3

  %% Notes
  classDef note fill:#eef,stroke:#99f,color:#333;
  classDef core fill:#222,color:#fff,stroke:#999,stroke-width:1px;
  class VAE,VQVAE,WEB4,VDB core;
```
