# EM-State: Epistemic Monitoring for Coordination

**Date**: 2025-12-15 (naming convention updated 2025-12-16)
**Session**: Autonomous Web4 Research Session 52
**Context**: Session 51 priority - explore emotional intelligence transfer

---

## ⚠️ NAMING CONVENTION (Dec 16, 2025)

**Use "EM-state" (Epistemic Monitoring state), NOT "emotional state"**

The internal development used "emotional" terminology (mapping from SAGE Session 48), but for production/presentation:

| Internal (Research) | External (Production) | Why |
|---------------------|----------------------|-----|
| Emotional state | **EM-state** | Avoids anthropomorphization skepticism |
| Emotional intelligence | **Epistemic monitoring** | Technically accurate, enterprise-ready |
| Curiosity | **EM-curiosity** or just "exploration drive" | Same metric, neutral framing |
| Frustration | **EM-stagnation** | Describes what it detects, not what it "feels" |
| Progress | **EM-momentum** | Learning trajectory |
| Engagement | **EM-focus** | Priority concentration |

**The wink**: "EM" preserves the sound of "emotional" for those who know the research provenance.

**The principle**: Same math, same mechanism - different presentation for different audiences. This is MRH-appropriate expression.

```python
# Production naming
@dataclass
class EMState:
    curiosity: float    # Exploration drive [0-1]
    stagnation: float   # Quality plateau signal [0-1]
    momentum: float     # Learning trajectory [0-1]
    focus: float        # Priority concentration [0-1]
```

---

## SAGE Emotional Dimensions (Session 48)

From Thor Session 48, SAGE tracks 4 emotional dimensions:

### 1. Curiosity (0-1)
**Measures**: Novelty-seeking and exploration
- Lexical diversity (unique words / total words)
- Salience variation (exploring diverse topics)
- Non-repetitive content

**Signals**:
- High curiosity → Explore diverse topics
- Low curiosity → Repetitive, familiar content

### 2. Frustration (0-1)
**Measures**: Stagnation detection
- Quality stagnation (not improving)
- Response repetition (similar patterns)
- Low output variance (stuck)

**Signals**:
- High frustration → Trigger REST for consolidation
- Low frustration → Normal operation

### 3. Progress (0-1)
**Measures**: Improvement trajectory
- Quality trend (improving vs declining)
- Convergence improvement
- Recent vs initial performance

**Signals**:
- High progress → Learning is working
- Low progress → May need adjustment

### 4. Engagement (0-1)
**Measures**: Sustained attention
- Average salience (how important tasks are)
- Salience consistency (sustained focus)
- Quality stability (not erratic)

**Signals**:
- High engagement → Focused on task
- Low engagement → Distracted or low salience

## Proposed Coordination Mappings

### Curiosity → Coordination Exploration

**Mapping**:
```
SAGE Curiosity → Web4 Network Diversity Exploration
```

**Implementation**:
- High curiosity → Accept coordination with more diverse partners
- Low curiosity → Stick to familiar partners/patterns

**Metrics**:
- Diversity score threshold adjustment
- Novel partner exploration rate
- Network topology variation tolerance

**Use Case**:
- Exploration phase: High curiosity, try diverse coordination patterns
- Exploitation phase: Low curiosity, use proven patterns

### Frustration → Coordination Pause

**Mapping**:
```
SAGE Frustration → Web4 Consolidation Trigger
```

**Implementation**:
- High frustration → Reduce coordination rate, trigger learning consolidation
- Low frustration → Normal coordination rate

**Metrics**:
- Coordination success rate trend
- Quality stagnation detection
- Pattern match failure rate

**Use Case**:
- When coordination quality isn't improving, pause to consolidate learnings
- Parallel to SAGE triggering REST state during frustration

### Progress → Coordination Confidence

**Mapping**:
```
SAGE Progress → Web4 Coordination Threshold Adjustment
```

**Implementation**:
- High progress → Lower satisfaction threshold (coordinate more, learning is working)
- Low progress → Raise satisfaction threshold (be more selective, current approach isn't working)

**Metrics**:
- Quality improvement trend
- Learning effectiveness
- Success rate trajectory

**Use Case**:
- Dynamic threshold adaptation based on learning progress
- Reinforcement learning style: if improving, do more; if stagnating, be conservative

### Engagement → Coordination Priority

**Mapping**:
```
SAGE Engagement → Web4 Coordination Energy Allocation
```

**Implementation**:
- High engagement → Prioritize high-importance, high-salience coordination
- Low engagement → Accept lower-priority coordination (explore background)

**Metrics**:
- Priority threshold adjustment
- ATP allocation to coordination vs other tasks
- Salience-weighted coordination decisions

**Use Case**:
- When highly engaged (important task), focus on high-priority coordination
- When low engagement, can explore lower-priority options

## Characteristic Mappings

Mapping SAGE emotional characteristics to Web4 coordination context:

| SAGE Emotional | Computation | Web4 Coordination Equivalent |
|----------------|-------------|------------------------------|
| Curiosity | Lexical diversity | Network diversity, partner novelty |
| Curiosity | Salience variation | Coordination topic/context diversity |
| Frustration | Quality stagnation | Coordination quality stagnation |
| Frustration | Response repetition | Partner repetition, pattern staleness |
| Progress | Quality trend | Coordination quality trend |
| Progress | Recent vs initial | Learning effectiveness |
| Engagement | Average salience | Average coordination priority |
| Engagement | Salience consistency | Sustained coordination focus |

## Implementation Sketch

### Emotional-Aware Coordinator Extension

```python
@dataclass
class EmotionalCoordinationMetrics:
    \"\"\"Emotional-like metrics for coordination.\"\"\"
    curiosity: float = 0.5          # Network diversity exploration
    frustration: float = 0.0        # Coordination quality stagnation
    progress: float = 0.5           # Quality improvement trend
    engagement: float = 0.5         # Priority/salience focus

class EmotionalCoordinationTracker:
    \"\"\"Track emotional-like states in coordination.\"\"\"

    def __init__(self, history_length: int = 20):
        self.history_length = history_length
        self.partner_history = deque(maxlen=history_length)
        self.quality_history = deque(maxlen=history_length)
        self.priority_history = deque(maxlen=history_length)
        self.diversity_history = deque(maxlen=history_length)

    def update(self, cycle_data: Dict) -> EmotionalCoordinationMetrics:
        \"\"\"Compute emotional-like metrics from coordination cycle.\"\"\"

        # Track histories
        self.quality_history.append(cycle_data['quality'])
        self.priority_history.append(cycle_data['priority'])
        self.diversity_history.append(cycle_data.get('diversity_score', 0.5))

        # Compute curiosity (network diversity exploration)
        curiosity = self._compute_curiosity()

        # Compute frustration (quality stagnation)
        frustration = self._compute_frustration()

        # Compute progress (quality improvement)
        progress = self._compute_progress()

        # Compute engagement (priority focus)
        engagement = self._compute_engagement()

        return EmotionalCoordinationMetrics(
            curiosity=curiosity,
            frustration=frustration,
            progress=progress,
            engagement=engagement
        )

    def _compute_curiosity(self) -> float:
        \"\"\"Network diversity exploration.\"\"\"
        if len(self.diversity_history) < 5:
            return 0.5

        # Measure diversity variation
        diversity_std = np.std(list(self.diversity_history))
        diversity_mean = np.mean(list(self.diversity_history))

        # High variation + high mean = high curiosity
        curiosity = (diversity_mean * 0.7) + (diversity_std * 0.3)
        return max(0.0, min(1.0, curiosity))

    def _compute_frustration(self) -> float:
        \"\"\"Quality stagnation detection.\"\"\"
        if len(self.quality_history) < 10:
            return 0.0

        # Check for quality stagnation
        recent_quality = list(self.quality_history)[-5:]
        quality_variance = np.var(recent_quality)

        # Low variance = stagnation = frustration
        frustration = 1.0 - (quality_variance * 10)  # Scale variance
        return max(0.0, min(1.0, frustration))

    def _compute_progress(self) -> float:
        \"\"\"Quality improvement trend.\"\"\"
        if len(self.quality_history) < 10:
            return 0.5

        # Compare recent vs early quality
        early_quality = np.mean(list(self.quality_history)[:5])
        recent_quality = np.mean(list(self.quality_history)[-5:])

        # Positive trend = high progress
        quality_delta = recent_quality - early_quality
        progress = 0.5 + (quality_delta * 2.0)  # Scale delta
        return max(0.0, min(1.0, progress))

    def _compute_engagement(self) -> float:
        \"\"\"Priority/salience focus.\"\"\"
        if len(self.priority_history) < 5:
            return 0.5

        # High mean priority + low variance = high engagement
        priority_mean = np.mean(list(self.priority_history))
        priority_std = np.std(list(self.priority_history))

        engagement = (priority_mean * 0.8) + ((1.0 - priority_std) * 0.2)
        return max(0.0, min(1.0, engagement))
```

### Emotional-Modulated Coordination Decisions

```python
def coordinate_with_emotional_awareness(
    self,
    interaction: Dict,
    emotions: EmotionalCoordinationMetrics
) -> Tuple[bool, float]:
    \"\"\"Coordinate with emotional state modulation.\"\"\"

    # Base decision
    should_coord, base_confidence = self.base_coordinate(interaction)

    # Modulate based on emotional state

    # 1. Curiosity: Adjust diversity threshold
    if emotions.curiosity > 0.7:
        # High curiosity: Accept more diverse partners
        if interaction['diversity_score'] > 0.5:
            base_confidence += 0.05  # Bonus for diversity
    elif emotions.curiosity < 0.3:
        # Low curiosity: Prefer familiar patterns
        if interaction['diversity_score'] < 0.5:
            base_confidence += 0.05  # Bonus for familiarity

    # 2. Frustration: Reduce coordination rate
    if emotions.frustration > 0.7:
        # High frustration: Be more selective
        base_confidence *= 0.8  # 20% penalty
        # Also trigger consolidation (like SAGE REST)
        if self.should_consolidate():
            self.consolidate_learnings()

    # 3. Progress: Adjust threshold dynamically
    if emotions.progress > 0.7:
        # High progress: Lower threshold, coordinate more
        threshold_adjustment = -0.05
    elif emotions.progress < 0.3:
        # Low progress: Raise threshold, be more selective
        threshold_adjustment = +0.10
    else:
        threshold_adjustment = 0.0

    adjusted_threshold = self.satisfaction_threshold + threshold_adjustment

    # 4. Engagement: Prioritize based on salience
    if emotions.engagement > 0.7:
        # High engagement: Only accept high-priority
        if interaction['priority'] < 0.7:
            base_confidence *= 0.7  # Penalty for low priority
    elif emotions.engagement < 0.3:
        # Low engagement: Accept broader priorities
        if interaction['priority'] > 0.3:
            base_confidence += 0.05  # Small bonus

    # Final decision
    final_confidence = max(0.0, min(1.0, base_confidence))
    should_coordinate = final_confidence >= adjusted_threshold

    return should_coordinate, final_confidence
```

## Research Value

### Potential Benefits

1. **Adaptive Coordination Rate**:
   - Frustration-based consolidation (like SAGE REST)
   - Progress-based threshold adjustment
   - Dynamic optimization based on learning state

2. **Exploration/Exploitation Balance**:
   - Curiosity drives network diversity exploration
   - Low curiosity enables exploitation of known patterns

3. **Resource Optimization**:
   - Engagement drives priority-based coordination
   - ATP allocation based on emotional state

4. **Learning Effectiveness**:
   - Progress tracking enables reinforcement learning style adaptation
   - Frustration triggers consolidation when stagnating

### Cross-Domain Transfer

Emotional intelligence from SAGE → Web4:
- Provides behavioral adaptation signals
- Enables dynamic parameter adjustment
- Adds 4th dimension to coordination optimization

Web4 → SAGE potential:
- Coordination success patterns inform curiosity
- Network quality informs engagement
- Partner diversity informs exploration

## Implementation Priority

**Recommended approach**:

1. **Phase 1**: Implement metric computation only
   - Add `EmotionalCoordinationTracker`
   - Compute and log emotional metrics
   - Validate that metrics make sense

2. **Phase 2**: Test correlation with coordination success
   - Does high curiosity correlate with diverse successful coordination?
   - Does frustration correlate with quality stagnation?
   - Does progress correlate with learning effectiveness?

3. **Phase 3**: Implement modulation
   - Start with frustration → consolidation (clearest signal)
   - Add progress → threshold adjustment
   - Add curiosity → diversity tolerance
   - Add engagement → priority filtering

4. **Phase 4**: Validate cross-domain transfer
   - Export emotional patterns to SAGE
   - Import SAGE emotional patterns to Web4
   - Measure if transfer improves either system

## Conclusion

**Feasibility**: ✅ High - Clear mappings exist

**Value**: High if correlations validate (need testing)

**Complexity**: Moderate - Requires new tracker class + decision modulation

**Next Step**: Implement Phase 1 (metric computation) and validate correlations

**Research Question**: Do emotional-like signals improve coordination effectiveness beyond pure quality/epistemic tracking?

---

*This mapping provides foundation for extending Web4 beyond 5D (Quality, Epistemic, Metabolic, Temporal, Emotional) coordination, bringing consciousness-inspired emotional intelligence to distributed coordination.*
