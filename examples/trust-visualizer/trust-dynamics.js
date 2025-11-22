class TrustState {
  constructor() {
    this.value = 0.0; // -1 (distrust) to +1 (trust)
    this.certainty = 0.0; // 0 (uncertain) to 1 (certain)
    this.history = [];
  }

  /**
   * Record an interaction and update trust state.
   * @param {"positive"|"negative"|"neutral"} outcome
   * @param {number} magnitude 0..1
   */
  interact(outcome, magnitude = 0.5) {
    magnitude = Math.max(0, Math.min(1, magnitude));

    // 1. Update value: asymmetric response
    if (outcome === "positive") {
      // Move toward +1, slower
      this.value += (1 - this.value) * magnitude * 0.3;
    } else if (outcome === "negative") {
      // Move toward -1, faster
      this.value += (-1 - this.value) * magnitude * 0.5;
    } else {
      // Neutral interaction: tiny drift toward 0 (stabilization)
      this.value += (0 - this.value) * 0.05 * magnitude;
    }

    // Clamp
    this.value = Math.max(-1, Math.min(1, this.value));

    // 2. Update certainty (any interaction increases certainty)
    this.certainty += (1 - this.certainty) * 0.2;

    // 3. Global decay on certainty to reflect fading memory
    this.certainty *= 0.98;
    this.certainty = Math.max(0, Math.min(1, this.certainty));

    // 4. Record history point
    const point = {
      time: this.history.length,
      value: this.value,
      certainty: this.certainty,
      outcome,
      magnitude
    };
    this.history.push(point);

    return point;
  }

  /** Reset trust state to initial neutral conditions. */
  reset() {
    this.value = 0.0;
    this.certainty = 0.0;
    this.history = [];
  }

  /**
   * Compute uncertainty bounds based on certainty.
   * Returns [lower, upper].
   */
  getUncertaintyBounds() {
    const uncertainty = 1 - this.certainty; // 0 certainty => wide band
    return [this.value - uncertainty, this.value + uncertainty];
  }
}

// Simple helper to generate a random interaction
function randomInteraction() {
  const r = Math.random();
  if (r < 0.45) return "positive";
  if (r < 0.75) return "neutral";
  return "negative";
}
