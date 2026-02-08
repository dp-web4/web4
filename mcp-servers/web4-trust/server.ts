#!/usr/bin/env node
/**
 * Web4 Trust MCP Server
 *
 * Open Source (AGPL-3.0) - Part of Web4 Trust Infrastructure
 *
 * Provides T3/V3 trust tensor operations for AI agents.
 *
 * Tools:
 *   - web4.io/trust/query     - Get T3/V3 for entity@role
 *   - web4.io/trust/update    - Update based on outcome
 *   - web4.io/trust/history   - Historical tensor values
 *   - web4.io/trust/compare   - Compare two entities
 *   - web4.io/trust/aggregate - Multi-source aggregation
 *   - web4.io/trust/decay     - Apply temporal decay
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// ============================================================================
// Types - T3 (3D Trust Tensor) and V3 (Velocity/Volatility)
// ============================================================================

interface T3Tensor {
  // Canonical Web4 naming
  talent: number;     // Technical capability (0-1)
  training: number;   // Behavioral reliability (0-1)
  temperament: number; // Ethical alignment (0-1)

  // Context weights for situation-specific trust
  contextWeights: [number, number, number];

  // Role context
  role?: string;
}

interface V3Tensor {
  // Rate of change for each dimension
  talentVelocity: number;
  trainingVelocity: number;
  temperamentVelocity: number;

  // Volatility (uncertainty) for each dimension
  talentVolatility: number;
  trainingVolatility: number;
  temperamentVolatility: number;
}

interface TrustRecord {
  entityId: string;
  role: string;
  t3: T3Tensor;
  v3: V3Tensor;
  lastUpdated: string;
  updateCount: number;
}

interface TrustHistoryEntry {
  timestamp: string;
  t3: T3Tensor;
  v3: V3Tensor;
  action?: string;
  outcome?: "success" | "failure" | "partial";
}

interface OutcomeUpdate {
  entityId: string;
  role: string;
  action: string;
  outcome: "success" | "failure" | "partial";
  affectedDimensions: ("talent" | "training" | "temperament")[];
  magnitude?: number; // 0-1, defaults to 0.1
}

// ============================================================================
// In-Memory State
// ============================================================================

const trustRecords = new Map<string, TrustRecord>();
const trustHistory = new Map<string, TrustHistoryEntry[]>();

// ============================================================================
// Helper Functions
// ============================================================================

function entityRoleKey(entityId: string, role: string): string {
  return `${entityId}@${role}`;
}

function clamp(value: number, min: number = 0, max: number = 1): number {
  return Math.min(max, Math.max(min, value));
}

function defaultT3(): T3Tensor {
  return {
    talent: 0.5,
    training: 0.5,
    temperament: 0.5,
    contextWeights: [0.33, 0.34, 0.33],
  };
}

function defaultV3(): V3Tensor {
  return {
    talentVelocity: 0,
    trainingVelocity: 0,
    temperamentVelocity: 0,
    talentVolatility: 0.5, // Start with moderate uncertainty
    trainingVolatility: 0.5,
    temperamentVolatility: 0.5,
  };
}

function computeAggregateTrust(t3: T3Tensor): number {
  const [w1, w2, w3] = t3.contextWeights;
  return t3.talent * w1 + t3.training * w2 + t3.temperament * w3;
}

function applyDecay(value: number, halfLifeDays: number, daysSinceUpdate: number): number {
  const decayFactor = Math.pow(0.5, daysSinceUpdate / halfLifeDays);
  // Decay towards 0.5 (neutral trust)
  return 0.5 + (value - 0.5) * decayFactor;
}

// ============================================================================
// Tool Implementations
// ============================================================================

async function queryTrust(args: {
  entityId: string;
  role: string;
}): Promise<{ record: TrustRecord | null; aggregateTrust: number | null }> {
  const key = entityRoleKey(args.entityId, args.role);
  const record = trustRecords.get(key);

  if (!record) {
    return { record: null, aggregateTrust: null };
  }

  return {
    record,
    aggregateTrust: computeAggregateTrust(record.t3),
  };
}

async function updateTrust(args: OutcomeUpdate): Promise<{
  previousT3: T3Tensor;
  newT3: T3Tensor;
  previousV3: V3Tensor;
  newV3: V3Tensor;
}> {
  const key = entityRoleKey(args.entityId, args.role);
  let record = trustRecords.get(key);

  // Initialize if not exists
  if (!record) {
    record = {
      entityId: args.entityId,
      role: args.role,
      t3: defaultT3(),
      v3: defaultV3(),
      lastUpdated: new Date().toISOString(),
      updateCount: 0,
    };
  }

  const previousT3 = { ...record.t3 };
  const previousV3 = { ...record.v3 };

  const magnitude = args.magnitude ?? 0.1;
  const direction = args.outcome === "success" ? 1 : args.outcome === "failure" ? -1 : 0;
  const delta = magnitude * direction;

  // Update affected dimensions
  for (const dim of args.affectedDimensions) {
    const currentValue = record.t3[dim];
    const newValue = clamp(currentValue + delta);
    const actualDelta = newValue - currentValue;

    record.t3[dim] = newValue;

    // Update velocity (exponential moving average)
    const velocityKey = `${dim}Velocity` as keyof V3Tensor;
    const prevVelocity = record.v3[velocityKey] as number;
    record.v3[velocityKey] = 0.7 * prevVelocity + 0.3 * actualDelta;

    // Update volatility based on surprise (difference from expected)
    const volatilityKey = `${dim}Volatility` as keyof V3Tensor;
    const surprise = Math.abs(actualDelta - prevVelocity);
    const prevVolatility = record.v3[volatilityKey] as number;
    record.v3[volatilityKey] = clamp(0.8 * prevVolatility + 0.2 * surprise * 2);
  }

  record.lastUpdated = new Date().toISOString();
  record.updateCount++;
  trustRecords.set(key, record);

  // Record history
  const history = trustHistory.get(key) || [];
  history.push({
    timestamp: record.lastUpdated,
    t3: { ...record.t3 },
    v3: { ...record.v3 },
    action: args.action,
    outcome: args.outcome,
  });
  trustHistory.set(key, history);

  return {
    previousT3,
    newT3: record.t3,
    previousV3,
    newV3: record.v3,
  };
}

async function getTrustHistory(args: {
  entityId: string;
  role: string;
  limit?: number;
  since?: string;
}): Promise<{ history: TrustHistoryEntry[] }> {
  const key = entityRoleKey(args.entityId, args.role);
  let history = trustHistory.get(key) || [];

  if (args.since) {
    const sinceDate = new Date(args.since);
    history = history.filter((h) => new Date(h.timestamp) >= sinceDate);
  }

  if (args.limit) {
    history = history.slice(-args.limit);
  }

  return { history };
}

async function compareTrust(args: {
  entity1: { entityId: string; role: string };
  entity2: { entityId: string; role: string };
}): Promise<{
  entity1: TrustRecord | null;
  entity2: TrustRecord | null;
  comparison: {
    talentDiff: number;
    trainingDiff: number;
    temperamentDiff: number;
    aggregateDiff: number;
    moreReliable: string | null;
  };
}> {
  const key1 = entityRoleKey(args.entity1.entityId, args.entity1.role);
  const key2 = entityRoleKey(args.entity2.entityId, args.entity2.role);

  const record1 = trustRecords.get(key1) || null;
  const record2 = trustRecords.get(key2) || null;

  const t3_1 = record1?.t3 || defaultT3();
  const t3_2 = record2?.t3 || defaultT3();

  const agg1 = computeAggregateTrust(t3_1);
  const agg2 = computeAggregateTrust(t3_2);

  return {
    entity1: record1,
    entity2: record2,
    comparison: {
      talentDiff: t3_1.talent - t3_2.talent,
      trainingDiff: t3_1.training - t3_2.training,
      temperamentDiff: t3_1.temperament - t3_2.temperament,
      aggregateDiff: agg1 - agg2,
      moreReliable:
        agg1 > agg2
          ? args.entity1.entityId
          : agg2 > agg1
            ? args.entity2.entityId
            : null,
    },
  };
}

async function aggregateTrust(args: {
  sources: Array<{
    entityId: string;
    role: string;
    weight?: number;
  }>;
  aggregationMethod: "weighted-average" | "minimum" | "maximum" | "consensus";
}): Promise<{
  aggregatedT3: T3Tensor;
  aggregateTrust: number;
  sourceCount: number;
}> {
  const sourceRecords: Array<{ record: TrustRecord; weight: number }> = [];

  for (const source of args.sources) {
    const key = entityRoleKey(source.entityId, source.role);
    const record = trustRecords.get(key);
    if (record) {
      sourceRecords.push({
        record,
        weight: source.weight ?? 1,
      });
    }
  }

  if (sourceRecords.length === 0) {
    return {
      aggregatedT3: defaultT3(),
      aggregateTrust: 0.5,
      sourceCount: 0,
    };
  }

  let aggregatedT3: T3Tensor;

  switch (args.aggregationMethod) {
    case "weighted-average": {
      const totalWeight = sourceRecords.reduce((sum, s) => sum + s.weight, 0);
      aggregatedT3 = {
        talent:
          sourceRecords.reduce((sum, s) => sum + s.record.t3.talent * s.weight, 0) /
          totalWeight,
        training:
          sourceRecords.reduce((sum, s) => sum + s.record.t3.training * s.weight, 0) /
          totalWeight,
        temperament:
          sourceRecords.reduce((sum, s) => sum + s.record.t3.temperament * s.weight, 0) /
          totalWeight,
        contextWeights: [0.33, 0.34, 0.33],
      };
      break;
    }

    case "minimum": {
      aggregatedT3 = {
        talent: Math.min(...sourceRecords.map((s) => s.record.t3.talent)),
        training: Math.min(...sourceRecords.map((s) => s.record.t3.training)),
        temperament: Math.min(...sourceRecords.map((s) => s.record.t3.temperament)),
        contextWeights: [0.33, 0.34, 0.33],
      };
      break;
    }

    case "maximum": {
      aggregatedT3 = {
        talent: Math.max(...sourceRecords.map((s) => s.record.t3.talent)),
        training: Math.max(...sourceRecords.map((s) => s.record.t3.training)),
        temperament: Math.max(...sourceRecords.map((s) => s.record.t3.temperament)),
        contextWeights: [0.33, 0.34, 0.33],
      };
      break;
    }

    case "consensus": {
      // Use median for consensus
      const sortedTalent = sourceRecords.map((s) => s.record.t3.talent).sort((a, b) => a - b);
      const sortedTraining = sourceRecords.map((s) => s.record.t3.training).sort((a, b) => a - b);
      const sortedTemperament = sourceRecords
        .map((s) => s.record.t3.temperament)
        .sort((a, b) => a - b);
      const mid = Math.floor(sortedTalent.length / 2);

      aggregatedT3 = {
        talent:
          sortedTalent.length % 2
            ? sortedTalent[mid]
            : (sortedTalent[mid - 1] + sortedTalent[mid]) / 2,
        training:
          sortedTraining.length % 2
            ? sortedTraining[mid]
            : (sortedTraining[mid - 1] + sortedTraining[mid]) / 2,
        temperament:
          sortedTemperament.length % 2
            ? sortedTemperament[mid]
            : (sortedTemperament[mid - 1] + sortedTemperament[mid]) / 2,
        contextWeights: [0.33, 0.34, 0.33],
      };
      break;
    }
  }

  return {
    aggregatedT3,
    aggregateTrust: computeAggregateTrust(aggregatedT3),
    sourceCount: sourceRecords.length,
  };
}

async function applyTrustDecay(args: {
  entityId: string;
  role: string;
  halfLifeDays?: number;
}): Promise<{
  previousT3: T3Tensor;
  newT3: T3Tensor;
  daysSinceUpdate: number;
}> {
  const key = entityRoleKey(args.entityId, args.role);
  const record = trustRecords.get(key);

  if (!record) {
    return {
      previousT3: defaultT3(),
      newT3: defaultT3(),
      daysSinceUpdate: 0,
    };
  }

  const previousT3 = { ...record.t3 };
  const now = new Date();
  const lastUpdate = new Date(record.lastUpdated);
  const daysSinceUpdate = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60 * 24);

  const halfLifeDays = args.halfLifeDays ?? 30;

  record.t3.talent = applyDecay(record.t3.talent, halfLifeDays, daysSinceUpdate);
  record.t3.training = applyDecay(record.t3.training, halfLifeDays, daysSinceUpdate);
  record.t3.temperament = applyDecay(record.t3.temperament, halfLifeDays, daysSinceUpdate);

  record.lastUpdated = now.toISOString();
  trustRecords.set(key, record);

  return {
    previousT3,
    newT3: record.t3,
    daysSinceUpdate,
  };
}

// ============================================================================
// MCP Server Setup
// ============================================================================

const server = new Server(
  {
    name: "web4-trust",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// Tool definitions
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "web4.io/trust/query",
      description: "Get T3/V3 trust tensors for an entity@role",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: {
            type: "string",
            description: "Entity identifier (e.g., 'agent:claude-1')",
          },
          role: {
            type: "string",
            description: "Role context (e.g., 'developer', 'reviewer')",
          },
        },
        required: ["entityId", "role"],
      },
    },
    {
      name: "web4.io/trust/update",
      description: "Update trust tensors based on an action outcome",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: {
            type: "string",
            description: "Entity identifier",
          },
          role: {
            type: "string",
            description: "Role context",
          },
          action: {
            type: "string",
            description: "The action that was performed",
          },
          outcome: {
            type: "string",
            enum: ["success", "failure", "partial"],
            description: "Outcome of the action",
          },
          affectedDimensions: {
            type: "array",
            items: { type: "string", enum: ["talent", "training", "temperament"] },
            description: "Which trust dimensions were affected",
          },
          magnitude: {
            type: "number",
            description: "Magnitude of update (0-1, default 0.1)",
          },
        },
        required: ["entityId", "role", "action", "outcome", "affectedDimensions"],
      },
    },
    {
      name: "web4.io/trust/history",
      description: "Get historical trust tensor values",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: {
            type: "string",
            description: "Entity identifier",
          },
          role: {
            type: "string",
            description: "Role context",
          },
          limit: {
            type: "number",
            description: "Maximum entries to return",
          },
          since: {
            type: "string",
            description: "ISO8601 timestamp to filter from",
          },
        },
        required: ["entityId", "role"],
      },
    },
    {
      name: "web4.io/trust/compare",
      description: "Compare trust tensors between two entities",
      inputSchema: {
        type: "object" as const,
        properties: {
          entity1: {
            type: "object",
            properties: {
              entityId: { type: "string" },
              role: { type: "string" },
            },
            required: ["entityId", "role"],
          },
          entity2: {
            type: "object",
            properties: {
              entityId: { type: "string" },
              role: { type: "string" },
            },
            required: ["entityId", "role"],
          },
        },
        required: ["entity1", "entity2"],
      },
    },
    {
      name: "web4.io/trust/aggregate",
      description: "Aggregate trust from multiple sources",
      inputSchema: {
        type: "object" as const,
        properties: {
          sources: {
            type: "array",
            items: {
              type: "object",
              properties: {
                entityId: { type: "string" },
                role: { type: "string" },
                weight: { type: "number" },
              },
              required: ["entityId", "role"],
            },
            description: "Trust sources to aggregate",
          },
          aggregationMethod: {
            type: "string",
            enum: ["weighted-average", "minimum", "maximum", "consensus"],
            description: "How to aggregate the sources",
          },
        },
        required: ["sources", "aggregationMethod"],
      },
    },
    {
      name: "web4.io/trust/decay",
      description: "Apply temporal decay to trust values (drift toward neutral)",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: {
            type: "string",
            description: "Entity identifier",
          },
          role: {
            type: "string",
            description: "Role context",
          },
          halfLifeDays: {
            type: "number",
            description: "Days until trust decays halfway to neutral (default 30)",
          },
        },
        required: ["entityId", "role"],
      },
    },
  ],
}));

// Tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "web4.io/trust/query": {
        const result = await queryTrust(args as Parameters<typeof queryTrust>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/trust/update": {
        const result = await updateTrust(args as OutcomeUpdate);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/trust/history": {
        const result = await getTrustHistory(args as Parameters<typeof getTrustHistory>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/trust/compare": {
        const result = await compareTrust(args as Parameters<typeof compareTrust>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/trust/aggregate": {
        const result = await aggregateTrust(args as Parameters<typeof aggregateTrust>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/trust/decay": {
        const result = await applyTrustDecay(args as Parameters<typeof applyTrustDecay>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        return {
          content: [
            {
              type: "text" as const,
              text: `Unknown tool: ${name}`,
            },
          ],
          isError: true,
        };
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text" as const,
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
});

// Resource definitions
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    {
      uri: "web4://trust/{entity_id}",
      name: "Entity Trust Profile",
      description: "Current trust tensors for an entity across all roles",
      mimeType: "application/json",
    },
  ],
}));

// Resource reading
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  const match = uri.match(/^web4:\/\/trust\/(.+)$/);
  if (!match) {
    throw new Error(`Invalid resource URI: ${uri}`);
  }

  const entityId = match[1];
  const roles: Record<string, TrustRecord> = {};

  for (const [key, record] of trustRecords) {
    if (record.entityId === entityId) {
      roles[record.role] = record;
    }
  }

  return {
    contents: [
      {
        uri,
        mimeType: "application/json",
        text: JSON.stringify(
          {
            entityId,
            roles,
            roleCount: Object.keys(roles).length,
          },
          null,
          2
        ),
      },
    ],
  };
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Web4 Trust MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
