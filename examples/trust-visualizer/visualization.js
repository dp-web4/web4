class TrustVisualizer {
  constructor(elementId, width = 800, height = 360) {
    this.elementId = elementId;
    this.width = width;
    this.height = height;

    this.margin = { top: 18, right: 18, bottom: 28, left: 40 };
    this.innerWidth = this.width - this.margin.left - this.margin.right;
    this.innerHeight = this.height - this.margin.top - this.margin.bottom;

    const container = d3.select(`#${elementId}`);
    this.svg = container
      .append("svg")
      .attr("width", this.width)
      .attr("height", this.height);

    this.g = this.svg
      .append("g")
      .attr("transform", `translate(${this.margin.left},${this.margin.top})`);

    // Scales
    this.xScale = d3.scaleLinear().range([0, this.innerWidth]);
    this.yScale = d3.scaleLinear().domain([-1, 1]).range([this.innerHeight, 0]);

    // Axes groups
    this.xAxisGroup = this.g
      .append("g")
      .attr("class", "axis axis-x")
      .attr("transform", `translate(0,${this.innerHeight})`);

    this.yAxisGroup = this.g
      .append("g")
      .attr("class", "axis axis-y");

    // Paths
    this.uncertaintyArea = this.g
      .append("path")
      .attr("class", "area-uncertainty");

    this.trustLine = this.g
      .append("path")
      .attr("class", "line-trust");

    this.pointsGroup = this.g
      .append("g")
      .attr("class", "points-group");

    // Axis labels
    this.svg
      .append("text")
      .attr("class", "axis-label")
      .attr("x", this.margin.left + this.innerWidth / 2)
      .attr("y", this.height - 2)
      .attr("text-anchor", "middle")
      .text("Interaction number");

    this.svg
      .append("text")
      .attr("class", "axis-label")
      .attr("x", 10)
      .attr("y", this.margin.top - 6)
      .text("Trust");
  }

  update(trustState) {
    const data = trustState.history;
    if (!data.length) {
      // Clear visuals when empty
      this.trustLine.attr("d", null);
      this.uncertaintyArea.attr("d", null);
      this.pointsGroup.selectAll("circle").remove();

      // Reset axes to default range
      this.xScale.domain([0, 5]);
      this.renderAxes();
      return;
    }

    const maxTime = d3.max(data, d => d.time) || 0;
    this.xScale.domain([0, Math.max(5, maxTime + 1)]);

    // Build area data from uncertainty bounds
    const areaData = data.map(d => {
      const uncert = 1 - d.certainty;
      return {
        time: d.time,
        lower: d.value - uncert,
        upper: d.value + uncert
      };
    });

    const areaGenerator = d3
      .area()
      .x(d => this.xScale(d.time))
      .y0(d => this.yScale(Math.max(-1, d.lower)))
      .y1(d => this.yScale(Math.min(1, d.upper)))
      .curve(d3.curveMonotoneX);

    const lineGenerator = d3
      .line()
      .x(d => this.xScale(d.time))
      .y(d => this.yScale(d.value))
      .curve(d3.curveMonotoneX);

    this.uncertaintyArea
      .transition()
      .duration(220)
      .attr("d", areaGenerator(areaData));

    this.trustLine
      .transition()
      .duration(220)
      .attr("d", lineGenerator(data));

    // Points for interactions
    const circles = this.pointsGroup.selectAll("circle").data(data, d => d.time);

    circles
      .enter()
      .append("circle")
      .attr("r", 3.2)
      .attr("cx", d => this.xScale(d.time))
      .attr("cy", d => this.yScale(d.value))
      .attr("class", d => `point point-${d.outcome}`)
      .append("title")
      .text(d => `#${d.time} ${d.outcome} (trust=${d.value.toFixed(3)}, certainty=${d.certainty.toFixed(3)})`);

    circles
      .transition()
      .duration(220)
      .attr("cx", d => this.xScale(d.time))
      .attr("cy", d => this.yScale(d.value));

    circles.exit().remove();

    this.renderAxes();
  }

  renderAxes() {
    const xAxis = d3
      .axisBottom(this.xScale)
      .ticks(6)
      .tickFormat(d3.format("d"));

    const yAxis = d3
      .axisLeft(this.yScale)
      .ticks(5);

    this.xAxisGroup
      .transition()
      .duration(220)
      .call(xAxis);

    this.yAxisGroup
      .transition()
      .duration(220)
      .call(yAxis);
  }
}

// Wire controls on load
window.addEventListener("DOMContentLoaded", () => {
  const trust = new TrustState();
  const viz = new TrustVisualizer("viz-container");

  const trustEl = document.getElementById("stat-trust");
  const certaintyEl = document.getElementById("stat-certainty");
  const countEl = document.getElementById("stat-count");

   const agentSelect = document.getElementById("agent-select");
   const loadLiveBtn = document.getElementById("btn-load-live");
   const agentStatus = document.getElementById("agent-status");

  function render() {
    viz.update(trust);
    trustEl.textContent = trust.value.toFixed(3);
    certaintyEl.textContent = trust.certainty.toFixed(3);
    countEl.textContent = trust.history.length.toString();
  }

  async function loadAgentsFromStore() {
    try {
      const resp = await fetch("http://localhost:8000/api/agents");
      const agents = await resp.json();

      if (!agents.length) {
        agentSelect.innerHTML = '<option value="">No agents</option>';
        agentStatus.textContent = "No agents available from store";
        return;
      }

      agentSelect.innerHTML = agents
        .map(
          (a, idx) => `
          <option value="${a.agent_id}" ${idx === 0 ? "selected" : ""}>
            ${a.agent_name} (${a.agent_id})
          </option>
        `,
        )
        .join("");

      agentStatus.textContent = "Loaded agents from store";
    } catch (e) {
      agentSelect.innerHTML = '<option value="agent-claude-demo">agent-claude-demo</option>';
      agentStatus.textContent = "Could not load agents; using default";
    }
  }

  async function loadLiveHistory() {
    const agentId = agentSelect.value || "agent-claude-demo";
    try {
      const resp = await fetch(
        `http://localhost:8000/api/t3/history?agent_id=${encodeURIComponent(agentId)}`,
      );
      const data = await resp.json();
      const history = data.history || [];

      trust.reset();

      for (const pt of history) {
        trust.history.push({
          time: pt.time,
          value: pt.value,
          certainty: pt.certainty,
          outcome: pt.outcome,
          magnitude: 0.7,
        });
      }

      if (history.length) {
        const last = history[history.length - 1];
        trust.value = last.value;
        trust.certainty = last.certainty;
      }

      render();
      agentStatus.textContent = `Showing live trust history for ${agentId}`;
    } catch (e) {
      agentStatus.textContent = "Failed to load live trust history";
    }
  }

  function applyInteraction(outcome) {
    trust.interact(outcome, 0.7);
    render();
  }

  document.getElementById("btn-positive").addEventListener("click", () => {
    applyInteraction("positive");
  });

  document.getElementById("btn-negative").addEventListener("click", () => {
    applyInteraction("negative");
  });

  document.getElementById("btn-neutral").addEventListener("click", () => {
    applyInteraction("neutral");
  });

  document.getElementById("btn-random").addEventListener("click", () => {
    applyInteraction(randomInteraction());
  });

  document.getElementById("btn-reset").addEventListener("click", () => {
    trust.reset();
    render();
  });

  loadLiveBtn.addEventListener("click", () => {
    loadLiveHistory();
  });

  // Initial render
  render();

  // Load agents from the running store so the user can pick an entity
  loadAgentsFromStore();
});
