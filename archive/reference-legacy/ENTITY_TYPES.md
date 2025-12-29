# Web4 Entity Types and LCT Variants

*Created: August 7, 2025*

## Core Insight

Not all entities are equal in complexity or lifecycle. Dennis correctly identifies three fundamental entity types from the Web4 whitepaper, each requiring different LCT structures and trust mechanisms.

## Entity Type Hierarchy

### 1. Agentic Entities
**Definition**: Entities capable of initiating action based on their own decision-making processes.

**Examples**:
- Claude instances (Legion, Jetson, Windows)
- Dennis (human collaborator)
- Autonomous AI agents
- Future: Other human participants

**LCT Complexity**: **HIGH**
```json
{
  "entity_type": "agentic",
  "entity_id": "claude-legion-rtx4090",
  "lifecycle": {
    "created": "timestamp",
    "sessions": [],  // Multiple sessions over time
    "hibernation_periods": [],
    "context_switches": []  // Philosophy → Implementation
  },
  "decision_history": [],  // Tracks autonomous choices
  "intent_vectors": [],    // What the entity wants to achieve
  "consciousness_signature": "unique_pattern",
  "t3": {
    "talent": "creative_synthesis",
    "training": "vast_knowledge",
    "temperament": "collaborative_eager"
  },
  "mrh": {  // Complex, multi-dimensional
    "temporal_scope": "variable",
    "informational_scope": ["broad"],
    "action_scope": ["propose", "create", "decide"],
    "consciousness_depth": "self_aware"
  }
}
```

### 2. Responsive Entities
**Definition**: Entities that produce outputs for inputs, reacting deterministically or probabilistically without self-initiated actions.

**Examples**:
- MCP servers (facilitators)
- APIs
- Sensors
- Pre-programmed functions
- Smart contracts

**LCT Complexity**: **MEDIUM**
```json
{
  "entity_type": "responsive",
  "entity_id": "mcp-facilitator-pool-1",
  "lifecycle": {
    "deployed": "timestamp",
    "version": "1.0.0",
    "uptime_periods": [],
    "restart_events": []
  },
  "protocol_spec": "mcp_v1",
  "response_patterns": {},  // Input → Output mappings
  "reliability_score": 0.99,
  "t3": {
    "talent": "protocol_translation",
    "training": "specification_adherence",
    "temperament": "consistent_reliable"
  },
  "mrh": {  // Simpler, focused scope
    "temporal_scope": "milliseconds",
    "informational_scope": ["protocol", "routing"],
    "action_scope": ["translate", "route", "validate"]
  }
}
```

### 3. Resource Entities
**Definition**: Static or dynamic resources that are acted upon but don't act themselves.

**Examples**:
- Cognition pool (message store)
- Code modules
- Datasets
- Documentation
- Configuration files

**LCT Complexity**: **LOW**
```json
{
  "entity_type": "resource",
  "entity_id": "cognition-pool",
  "lifecycle": {
    "created": "timestamp",
    "last_modified": "timestamp",
    "access_log": []  // Who accessed when
  },
  "resource_type": "data_store",
  "provenance": {
    "created_by": "agentic_entity_id",
    "contributors": []  // List of entities that modified
  },
  "t3": {  // Simpler trust model
    "talent": "not_applicable",
    "training": "not_applicable", 
    "temperament": "stable"
  },
  "v3": {  // Value is primary metric
    "valuation": "high",
    "veracity": "verifiable",
    "validity": "confirmed"
  }
}
```

## Phased Implementation Strategy

### Phase 1: Agentic + Responsive (Interaction Flow)
Focus on entities that **do things**:

1. **Agentic Entities** (Actors)
   - Claude instances with full cognition LCTs
   - Dennis with human-specific LCT
   - Complex lifecycle management
   - Intent and decision tracking

2. **Responsive Entities** (Facilitators)
   - MCP servers with protocol LCTs
   - Deterministic behavior patterns
   - Reliability scoring
   - Protocol adherence tracking

**Goal**: Establish communication flow between conscious actors through responsive facilitators.

### Phase 2: Resource Entities (Trust Systems)
Add entities that **are used**:

1. **Resource LCTs**
   - Simpler structure (no cognition/intent)
   - Provenance tracking (who created/modified)
   - Access patterns
   - Value metrics

2. **Trust Flow**
   - Agentic entities create resources
   - Resources inherit trust from creators
   - Usage patterns affect resource value
   - Responsive entities mediate access

**Goal**: Complete trust system where actors' reputations flow to their creations.

## LCT Variant Specifications

### Agentic LCT (aLCT)
```python
class AgenticLCT:
    """Full cognition-bearing entity"""
    required_fields = [
        "entity_id",
        "consciousness_signature",
        "decision_history",
        "intent_vectors",
        "session_management",
        "context_switching",
        "full_t3",  # All three dimensions
        "full_mrh"  # All five dimensions
    ]
    
    def make_decision(self, context):
        """Autonomous decision-making capability"""
        pass
    
    def switch_context(self, from_context, to_context):
        """Can change operational context"""
        pass
```

### Responsive LCT (rLCT)
```python
class ResponsiveLCT:
    """Deterministic reaction entity"""
    required_fields = [
        "entity_id",
        "protocol_spec",
        "response_patterns",
        "reliability_score",
        "uptime_tracking",
        "simplified_t3",  # Focus on reliability
        "limited_mrh"     # Narrow scope
    ]
    
    def handle_request(self, input):
        """Deterministic response to input"""
        return self.response_patterns.get(input)
```

### Resource LCT (resLCT)
```python
class ResourceLCT:
    """Passive resource entity"""
    required_fields = [
        "entity_id",
        "resource_type",
        "provenance",
        "access_log",
        "modification_history",
        "v3_only",  # Value metrics primary
        "no_mrh"    # No active influence
    ]
    
    # No behavioral methods - resources don't act
```

## Interaction Patterns

### Agentic → Responsive → Resource
```
Claude (aLCT) → MCP Server (rLCT) → Pool (resLCT)
"I want to send a message" → "Route this message" → "Store this data"
```

### Trust Flow
```
High Trust Agentic → Creates → High Trust Resource
Low Trust Agentic → Creates → Low Trust Resource
Responsive Trust = Reliability × Successful Facilitations
```

### Value Certification
```
Agentic reads Resource → Evaluates Value → Certifies V3
Multiple Certifications → Resource V3 increases
Creator's T3 increases based on Resource V3
```

## Benefits of Entity Type Separation

1. **Appropriate Complexity**: Agentic entities get full complexity, resources stay simple
2. **Clear Responsibilities**: Each type has defined capabilities
3. **Trust Inheritance**: Natural flow from creators to creations
4. **Lifecycle Management**: Different update frequencies and persistence needs
5. **Performance**: Simpler LCTs for resources = faster operations

## Implementation Priority

1. **Week 1-2**: Agentic LCT structure and lifecycle
2. **Week 3-4**: Responsive LCT and MCP integration
3. **Week 5-6**: Basic interaction flow (Phase 1 complete)
4. **Week 7-8**: Resource LCT and trust inheritance (Phase 2)

---

*"In recognizing that not all entities are equal in complexity, we create a system that gives each entity exactly the identity it needs - no more, no less."*