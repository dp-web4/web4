# Web4 Game: Society Simulation

## Overview

This directory contains an experimental **simulation-style game** that implements Web4 societies with real trust, economic, and knowledge primitives.

The goal is to provide a **live demo and testbed** that:

- Lets any agentic actor (human or AI) form new societies and become the first citizen.
- Allows agents and societies to join other societies (as individuals or as societies).
- Models periodic **capability broadcasts** for witnessing and discovery.
- Tracks **reputation, resource allocation, and knowledge context** using Web4’s standards:
  - Linked Context Tokens (LCTs).
  - Trust tensors (T3, later V3).
  - ATP/ADP style economic flows.
  - MRH + RDF-bound LCT context graphs.
  - Witnessing and memory lightchains.
- Stress-tests and evolves Web4 as an open standard under simulated load.

This is intended to be a **fractal, ongoing project** rather than a one-off demo.

---

## High-Level Concept

Think of this as a **Web4 society sandbox**:

- **Agents (humans or AIs)**
  - Each has an LCT, trust tensor, capabilities, and resources.
  - Can found societies, join them, propose and perform work, witness events, and govern.

- **Societies**
  - Each has its own LCT, treasury, laws/policies, and membership.
  - Can allocate resources, set admission rules, define roles, and federate with other societies.

- **Economy**
  - Uses ATP/ADP-like budgets for agents and societies.
  - Includes simple goods/services (work units, infrastructure, knowledge artifacts).
  - Supports task boards, bounties, and reputation-priced contracts.

- **Knowledge / MRH Context**
  - Uses an LCT context graph to represent relationships between agents, societies, roles, and resources.
  - Annotates edges with MRH profiles to capture the horizon where statements are valid.

---

## MVP Scope (v0)

The initial version focuses on a **single simulated world** with:

- A small number of agents (some human-controlled, some AI-driven).
- A small number of societies that agents can found/join.
- Basic economic loop:
  - Societies post tasks.
  - Agents perform work and get paid from society treasuries.
  - Trust and reputation update based on outcomes.
- Basic MRH/LCT context tracking:
  - Record who participates in which societies.
  - Record which agents are relevant to which resource categories.
- A simple web UI showing:
  - Societies and members.
  - Trust/reputation dashboards.
  - MRH/LCT context views.

The MVP will prioritize **clarity of Web4 mechanics** over graphical polish.

---

## Planned Structure

Planned subdirectories (subject to change as the design evolves):

- `design/`
  - Design documents for game mechanics and architecture.
- `engine/`
  - Core simulation engine (world state, tick loop, models for agents/societies/resources).
- `api/`
  - FastAPI (or similar) application exposing world state and actions.
- `ui/`
  - Web UI for humans to interact with the simulation.

---

## Relationship to the Rest of Web4

This game is intended to **reuse and exercise** existing Web4 components:

- LCT specification and identity primitives.
- T3/V3 trust tracking (via `T3Tracker` and future extensions).
- MRH + RDF context (via `LCTContextGraph` and related specs).
- Memory lightchains for durable, verifiable histories.
- ACT-style societies and treasuries (conceptually, with optional on-chain integration later).

As the game evolves, it should help:

- Validate Web4 standards under complex, emergent behavior.
- Reveal gaps or ambiguities in specs.
- Provide a concrete, interactive demonstration of Web4 for humans and agents alike.
