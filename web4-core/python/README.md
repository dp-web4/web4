# Web4 Python Bindings

Python bindings for the Web4 trust-native infrastructure core library.

## Installation

### From source (requires Rust and maturin)

```bash
pip install maturin
cd python
maturin develop
```

### Building a wheel

```bash
maturin build --release
pip install target/wheels/*.whl
```

## Usage

```python
import web4

# Create an LCT for a human user
lct, keypair = web4.PyLct.new(web4.PyEntityType.Human, None)

# Sign a message
message = b"Hello, Web4!"
signature = keypair.sign(message)

# Verify the signature
assert lct.verify_signature(message, signature)

# Create a trust tensor
trust = web4.PyT3()
trust.observe(web4.PyTrustDimension.Competence, 0.9)
trust.observe(web4.PyTrustDimension.Integrity, 0.85)

# Get aggregate trust score
score = trust.aggregate()
print(f"Aggregate trust: {score:.3f}")

# Create a value tensor
value = web4.PyV3()
value.observe(web4.PyValueDimension.Utility, 0.9)
value.observe(web4.PyValueDimension.Quality, 0.85)

# Calculate coherence
coherence = web4.PyCoherence.with_values(0.8, 0.8, 0.7, 0.9)
print(f"Total coherence: {coherence.total():.3f}")
print(f"Limiting factor: {coherence.limiting_factor()}")
```

## API Reference

### Entity Types

- `PyEntityType.Human` - Human user
- `PyEntityType.AiSoftware` - Software-bound AI agent
- `PyEntityType.AiEmbodied` - Hardware-bound AI agent
- `PyEntityType.Organization` - Organization
- `PyEntityType.Role` - Role (first-class entity)
- `PyEntityType.Task` - Task
- `PyEntityType.Resource` - Resource
- `PyEntityType.Hybrid` - Hybrid entity

### Trust Dimensions (T3)

- `Competence` - Ability to perform claimed capabilities
- `Integrity` - Consistency between stated and actual behavior
- `Benevolence` - Intent toward benefit vs harm
- `Predictability` - Consistency of behavior over time
- `Transparency` - Visibility into decision-making
- `Accountability` - Willingness to accept consequences

### Value Dimensions (V3)

- `Utility` - Practical usefulness
- `Novelty` - Originality and uniqueness
- `Quality` - Craftsmanship and attention to detail
- `Timeliness` - Delivery within appropriate timeframes
- `Relevance` - Alignment with current needs
- `Leverage` - Multiplicative effect on others

### Coherence (C × S × Φ × R)

- `C (Continuity)` - Temporal consistency
- `S (Stability)` - Resistance to perturbation
- `Φ (Phi)` - Information integration
- `R (Reachability)` - Network connection

## License

MIT OR Apache-2.0
