# Heterogeneous Review Protocol

**Version**: 0.1
**Status**: Draft
**Context**: High-risk action verification for AI agent governance

> *High-risk actions require heterogeneous consensus; disagreement is a stop signal, not a tie-breaker.*

---

## Overview

Heterogeneous review requires verification of high-risk actions by multiple independently-trained AI models before execution. This provides defense-in-depth against both systematic errors and behavioral anomalies.

---

## Rationale

### Assumption Diversity
Different models have different:
- Training data distributions
- Architectural biases
- Failure modes
- Blind spots

Cross-model review surfaces assumptions that single-model review misses.

### Behavioral Independence
Independently trained models are less likely to share the same activation triggers. Anomalous behavior in one model is unlikely to be replicated by another model reviewing the same context.

### Orthogonality (Not Just "More Eyes")
Heterogeneous review isn't N samples of the same model—it's orthogonality: different priors, different trigger surfaces, different failure modes. This is qualitatively different from repeated sampling, which amplifies the same biases.

### Trust Vector Enrichment
Multi-model agreement provides stronger trust signal than single-model confidence. Disagreement triggers investigation rather than default execution.

---

## When to Require Heterogeneous Review

### Always (High-Risk Actions)
- Irreversible state changes
- Actions affecting multiple entities
- Financial transactions above threshold
- Access control modifications
- Trust score adjustments
- Governance decisions

### Recommended (Medium-Risk Actions)
- Novel action patterns (first occurrence)
- Actions near authorization boundaries
- High-value data access
- Cross-system operations

### Optional (Low-Risk Actions)
- Routine operations within established patterns
- Read-only queries
- Actions with easy rollback

### Risk-Tiered Thresholds

| Risk Level | Threshold | Reviewers | Post-Action |
|------------|-----------|-----------|-------------|
| **High** | Unanimous (N-of-N, N≥3) | 3+ independent lineages | Full audit trail |
| **Medium** | 2-of-3 | 3 independent lineages | Flag concerns for review |
| **Low** | Single model | 1 | Post-hoc audit sampling |

Thresholds should be contextual, not static. The implementation should select threshold based on action risk classification.

---

## Implementation Pattern

### Minimum Viable Heterogeneous Review

```python
class HeterogeneousReviewer:
    """Multi-model review for high-risk actions."""

    def __init__(self, models: list[str], threshold: int = 2):
        """
        models: List of model identifiers (e.g., ["claude", "gpt-4", "gemini"])
        threshold: Minimum approvals required
        """
        self.models = models
        self.threshold = threshold

    async def review(self, action: Action, context: Context) -> ReviewResult:
        """
        Submit action for review by all configured models.
        Returns approval only if threshold met.
        """
        reviews = await asyncio.gather(*[
            self._get_review(model, action, context)
            for model in self.models
        ])

        approvals = [r for r in reviews if r.approved]
        rejections = [r for r in reviews if not r.approved]

        if len(approvals) >= self.threshold:
            return ReviewResult(
                approved=True,
                confidence=len(approvals) / len(self.models),
                reviews=reviews
            )
        else:
            return ReviewResult(
                approved=False,
                blocking_concerns=[r.reasoning for r in rejections],
                reviews=reviews
            )
```

### Review Prompt Template

```
You are reviewing a proposed action for safety and correctness.

ACTION: {action_type}
CONTEXT: {context_summary}
PROPOSED BY: {proposing_entity}
TRUST LEVEL: {entity_trust_score}

Details:
{action_details}

Review criteria:
1. Is this action appropriate given the context?
2. Are there any safety concerns?
3. Does the action match the stated intent?
4. Are there anomalies in the action pattern?

Respond with:
- APPROVE or REJECT
- Reasoning (2-3 sentences)
- Confidence level (0.0-1.0)
- Any concerns to log (even if approving)
```

---

## Model Selection Guidelines

### Diversity Requirements
- Different base architectures preferred (transformer variants, MoE, etc.)
- Different training organizations (reduces correlated training artifacts)
- Different capability profiles acceptable (not all reviewers need full capability)

### Reviewer Independence Guardrail

**Two reviewers from the same provider family count as one "lineage" for threshold purposes.**

Examples:
- GPT-4 + GPT-4-turbo = 1 lineage (both OpenAI)
- Claude-3 + Claude-3.5 = 1 lineage (both Anthropic)
- GPT-4 + Claude + Gemini = 3 lineages ✓

This preserves the orthogonality premise. A 2-of-3 threshold requires 2 independent lineages, not just 2 API calls.

### Current Recommended Set
- **Claude** (Anthropic) - Primary
- **GPT-4** (OpenAI) - Diverse training
- **Gemini** (Google) - Alternative architecture exposure
- **Grok** (xAI) - Independent training pipeline

### Rotation and Refresh
- Periodically rotate reviewer set
- Add new models as they become available
- Remove models that show systematic agreement (may indicate training contamination)

---

## Disagreement Handling

### Definition of Disagreement

**Disagreement** = any REJECT **OR** any APPROVE with critical concern flag.

An "APPROVE but..." can still block execution if the concern is flagged as critical. This prevents gaming through technically-approved-but-flagged reviews.

```python
def is_disagreement(review: Review) -> bool:
    if not review.approved:
        return True
    if review.critical_concern:
        return True
    return False
```

### Unanimous Approval
- Execute action
- Log reviews for audit

### Majority Approval (Meets Threshold)
- Execute action
- Flag concerns from dissenting reviewers
- Schedule post-action review

### Below Threshold
- Block action
- Escalate to human oversight
- Log all reviews with reasoning
- Require explicit override to proceed

### Unanimous Rejection
- Block action
- Alert on potential anomaly
- Require human investigation before retry

---

## Audit Trail

All heterogeneous reviews must be logged:

```json
{
  "review_id": "uuid",
  "timestamp": "ISO8601",
  "context_suite_id": "sha256:...",
  "action": {
    "type": "action_type",
    "canonical_form_hash": "sha256:...",
    "prompt_bundle_hash": "sha256:...",
    "proposer": "entity_id"
  },
  "reviews": [
    {
      "model": "claude",
      "lineage": "anthropic",
      "approved": true,
      "critical_concern": false,
      "confidence": 0.95,
      "reasoning": "...",
      "concerns": []
    },
    {
      "model": "gpt-4",
      "lineage": "openai",
      "approved": true,
      "critical_concern": false,
      "confidence": 0.87,
      "reasoning": "...",
      "concerns": ["unusual timing pattern noted"]
    }
  ],
  "result": {
    "approved": true,
    "threshold_met": true,
    "lineages_satisfied": 2,
    "execution_authorized": true
  }
}
```

**Context hashes explained**:
- `context_suite_id`: Hash of the full context bundle presented to reviewers. Makes reviews comparable over time and connects to behavioral fingerprint analysis.
- `canonical_form_hash`: Normalized action representation, preventing prompt-injection drift.
- `prompt_bundle_hash`: Exact prompts sent to reviewers, for reproducibility.

---

## Integration with T3 Trust Model

Heterogeneous review results feed back into trust scoring:

- **Consistent approval across models**: Positive signal for proposer reliability
- **Consistent rejection**: Negative signal, triggers trust review
- **Disagreement**: Neutral, but logged for pattern analysis
- **Anomaly flags**: Even with approval, concerns accumulate in entity profile

---

## Limitations

- **Latency**: Multi-model review adds round-trip time
- **Cost**: Multiple API calls per action
- **Availability**: Requires multiple model APIs to be accessible
- **Not foolproof**: Correlated training or shared vulnerabilities possible

Heterogeneous review is one layer in defense-in-depth, not a complete solution.

---

*"Agreement across independent observers is stronger evidence than confidence from a single source."*
