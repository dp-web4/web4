#!/usr/bin/env node
/**
 * Web4 Economy MCP Server
 *
 * Open Source (AGPL-3.0) - Part of Web4 Trust Infrastructure
 *
 * Provides ATP/ADP (Attention Token Protocol / Attention Debt Protocol)
 * operations for AI agent resource management.
 *
 * Tools:
 *   - web4.io/atp/balance    - Query ATP balance
 *   - web4.io/atp/transfer   - Transfer ATP between entities
 *   - web4.io/atp/price      - Get action price (3D pricing)
 *   - web4.io/atp/charge     - Charge ADP → ATP conversion
 *   - web4.io/atp/discharge  - Discharge ATP → ADP
 *   - web4.io/atp/demurrage  - Apply demurrage (holding cost)
 *   - web4.io/atp/history    - Transaction history
 *   - web4.io/atp/budget     - Get session budget
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import * as crypto from "crypto";

// ============================================================================
// Types - ATP (Attention Token Protocol) / ADP (Attention Debt Protocol)
// ============================================================================

interface ATPBalance {
  entityId: string;
  available: number;        // Available ATP tokens
  reserved: number;         // Reserved for pending operations
  adpOwed: number;          // Attention debt owed
  adpReceivable: number;    // Attention debt receivable
  lastUpdated: string;
}

interface ATPTransaction {
  id: string;
  type: "transfer" | "charge" | "discharge" | "demurrage" | "reserve" | "release";
  fromEntity: string;
  toEntity: string;
  amount: number;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

interface ActionPrice {
  basePrice: number;
  trustDiscount: number;     // Discount based on trust level
  urgencyMultiplier: number; // Multiplier for urgent actions
  complexityMultiplier: number; // Multiplier for complex actions
  finalPrice: number;
}

interface SessionBudget {
  sessionId: string;
  entityId: string;
  allocated: number;
  spent: number;
  remaining: number;
  startedAt: string;
  expiresAt?: string;
}

// ============================================================================
// In-Memory State
// ============================================================================

const balances = new Map<string, ATPBalance>();
const transactions: ATPTransaction[] = [];
const sessionBudgets = new Map<string, SessionBudget>();

// Pricing parameters
const BASE_PRICES: Record<string, number> = {
  "read:file": 1,
  "write:file": 5,
  "execute:command": 10,
  "network:request": 3,
  "llm:inference": 20,
  "default": 2,
};

// ============================================================================
// Helper Functions
// ============================================================================

function generateId(prefix: string): string {
  return `${prefix}:${crypto.randomUUID()}`;
}

function getOrCreateBalance(entityId: string): ATPBalance {
  let balance = balances.get(entityId);
  if (!balance) {
    balance = {
      entityId,
      available: 100, // Initial ATP allocation
      reserved: 0,
      adpOwed: 0,
      adpReceivable: 0,
      lastUpdated: new Date().toISOString(),
    };
    balances.set(entityId, balance);
  }
  return balance;
}

function recordTransaction(tx: Omit<ATPTransaction, "id" | "timestamp">): ATPTransaction {
  const fullTx: ATPTransaction = {
    ...tx,
    id: generateId("tx"),
    timestamp: new Date().toISOString(),
  };
  transactions.push(fullTx);
  return fullTx;
}

// ============================================================================
// Tool Implementations
// ============================================================================

async function getBalance(args: {
  entityId: string;
}): Promise<{ balance: ATPBalance }> {
  const balance = getOrCreateBalance(args.entityId);
  return { balance };
}

async function transferATP(args: {
  fromEntity: string;
  toEntity: string;
  amount: number;
  memo?: string;
}): Promise<{ success: boolean; transaction?: ATPTransaction; error?: string }> {
  if (args.amount <= 0) {
    return { success: false, error: "Amount must be positive" };
  }

  const fromBalance = getOrCreateBalance(args.fromEntity);

  if (fromBalance.available < args.amount) {
    return { success: false, error: `Insufficient balance: ${fromBalance.available} < ${args.amount}` };
  }

  const toBalance = getOrCreateBalance(args.toEntity);

  fromBalance.available -= args.amount;
  fromBalance.lastUpdated = new Date().toISOString();
  toBalance.available += args.amount;
  toBalance.lastUpdated = new Date().toISOString();

  balances.set(args.fromEntity, fromBalance);
  balances.set(args.toEntity, toBalance);

  const tx = recordTransaction({
    type: "transfer",
    fromEntity: args.fromEntity,
    toEntity: args.toEntity,
    amount: args.amount,
    metadata: args.memo ? { memo: args.memo } : undefined,
  });

  return { success: true, transaction: tx };
}

async function getActionPrice(args: {
  actionType: string;
  trustLevel?: number;
  urgency?: "low" | "normal" | "high" | "critical";
  complexity?: "simple" | "moderate" | "complex" | "very-complex";
}): Promise<{ price: ActionPrice }> {
  const basePrice = BASE_PRICES[args.actionType] ?? BASE_PRICES.default;

  // Trust discount: higher trust = lower price (up to 50% off)
  const trustLevel = args.trustLevel ?? 0.5;
  const trustDiscount = basePrice * (trustLevel * 0.5);

  // Urgency multiplier
  const urgencyMultipliers = {
    low: 0.8,
    normal: 1.0,
    high: 1.5,
    critical: 2.0,
  };
  const urgencyMultiplier = urgencyMultipliers[args.urgency ?? "normal"];

  // Complexity multiplier
  const complexityMultipliers = {
    simple: 0.5,
    moderate: 1.0,
    complex: 2.0,
    "very-complex": 4.0,
  };
  const complexityMultiplier = complexityMultipliers[args.complexity ?? "moderate"];

  const finalPrice = Math.max(
    1,
    Math.round((basePrice - trustDiscount) * urgencyMultiplier * complexityMultiplier)
  );

  return {
    price: {
      basePrice,
      trustDiscount,
      urgencyMultiplier,
      complexityMultiplier,
      finalPrice,
    },
  };
}

async function chargeATP(args: {
  entityId: string;
  amount: number;
  source?: string;
}): Promise<{ success: boolean; balance?: ATPBalance; transaction?: ATPTransaction; error?: string }> {
  if (args.amount <= 0) {
    return { success: false, error: "Amount must be positive" };
  }

  const balance = getOrCreateBalance(args.entityId);

  // Charging converts ADP debt into ATP availability
  // This represents "earning" attention through productive work
  if (balance.adpOwed > 0) {
    const debtPayment = Math.min(args.amount, balance.adpOwed);
    balance.adpOwed -= debtPayment;
    balance.available += args.amount - debtPayment;
  } else {
    balance.available += args.amount;
  }

  balance.lastUpdated = new Date().toISOString();
  balances.set(args.entityId, balance);

  const tx = recordTransaction({
    type: "charge",
    fromEntity: args.source ?? "system",
    toEntity: args.entityId,
    amount: args.amount,
    metadata: { source: args.source },
  });

  return { success: true, balance, transaction: tx };
}

async function dischargeATP(args: {
  entityId: string;
  amount: number;
  reason?: string;
}): Promise<{ success: boolean; balance?: ATPBalance; transaction?: ATPTransaction; error?: string }> {
  if (args.amount <= 0) {
    return { success: false, error: "Amount must be positive" };
  }

  const balance = getOrCreateBalance(args.entityId);

  // Discharging ATP - can go into debt (ADP)
  if (balance.available >= args.amount) {
    balance.available -= args.amount;
  } else {
    const deficit = args.amount - balance.available;
    balance.available = 0;
    balance.adpOwed += deficit;
  }

  balance.lastUpdated = new Date().toISOString();
  balances.set(args.entityId, balance);

  const tx = recordTransaction({
    type: "discharge",
    fromEntity: args.entityId,
    toEntity: "system",
    amount: args.amount,
    metadata: { reason: args.reason },
  });

  return { success: true, balance, transaction: tx };
}

async function applyDemurrage(args: {
  entityId: string;
  rate?: number; // Default 0.01 (1% per period)
}): Promise<{
  previousBalance: number;
  demurrageAmount: number;
  newBalance: number;
  transaction: ATPTransaction
}> {
  const rate = args.rate ?? 0.01;
  const balance = getOrCreateBalance(args.entityId);

  const previousBalance = balance.available;
  const demurrageAmount = Math.floor(balance.available * rate);

  balance.available -= demurrageAmount;
  balance.lastUpdated = new Date().toISOString();
  balances.set(args.entityId, balance);

  const tx = recordTransaction({
    type: "demurrage",
    fromEntity: args.entityId,
    toEntity: "system:demurrage",
    amount: demurrageAmount,
    metadata: { rate },
  });

  return {
    previousBalance,
    demurrageAmount,
    newBalance: balance.available,
    transaction: tx,
  };
}

async function getTransactionHistory(args: {
  entityId: string;
  limit?: number;
  type?: ATPTransaction["type"];
  since?: string;
}): Promise<{ transactions: ATPTransaction[] }> {
  let filtered = transactions.filter(
    (tx) => tx.fromEntity === args.entityId || tx.toEntity === args.entityId
  );

  if (args.type) {
    filtered = filtered.filter((tx) => tx.type === args.type);
  }

  if (args.since) {
    const sinceDate = new Date(args.since);
    filtered = filtered.filter((tx) => new Date(tx.timestamp) >= sinceDate);
  }

  if (args.limit) {
    filtered = filtered.slice(-args.limit);
  }

  return { transactions: filtered };
}

async function getSessionBudget(args: {
  sessionId: string;
}): Promise<{ budget: SessionBudget | null }> {
  const budget = sessionBudgets.get(args.sessionId);
  return { budget: budget || null };
}

async function createSessionBudget(args: {
  sessionId: string;
  entityId: string;
  allocated: number;
  expiresInHours?: number;
}): Promise<{ success: boolean; budget?: SessionBudget; error?: string }> {
  if (sessionBudgets.has(args.sessionId)) {
    return { success: false, error: "Session budget already exists" };
  }

  // Reserve ATP from entity balance
  const balance = getOrCreateBalance(args.entityId);
  if (balance.available < args.allocated) {
    return {
      success: false,
      error: `Insufficient balance: ${balance.available} < ${args.allocated}`
    };
  }

  balance.available -= args.allocated;
  balance.reserved += args.allocated;
  balance.lastUpdated = new Date().toISOString();
  balances.set(args.entityId, balance);

  const now = new Date();
  const budget: SessionBudget = {
    sessionId: args.sessionId,
    entityId: args.entityId,
    allocated: args.allocated,
    spent: 0,
    remaining: args.allocated,
    startedAt: now.toISOString(),
    expiresAt: args.expiresInHours
      ? new Date(now.getTime() + args.expiresInHours * 60 * 60 * 1000).toISOString()
      : undefined,
  };

  sessionBudgets.set(args.sessionId, budget);

  recordTransaction({
    type: "reserve",
    fromEntity: args.entityId,
    toEntity: `session:${args.sessionId}`,
    amount: args.allocated,
    metadata: { sessionId: args.sessionId },
  });

  return { success: true, budget };
}

async function spendSessionBudget(args: {
  sessionId: string;
  amount: number;
  action?: string;
}): Promise<{ success: boolean; budget?: SessionBudget; error?: string }> {
  const budget = sessionBudgets.get(args.sessionId);
  if (!budget) {
    return { success: false, error: "Session budget not found" };
  }

  if (budget.expiresAt && new Date(budget.expiresAt) < new Date()) {
    return { success: false, error: "Session budget expired" };
  }

  if (budget.remaining < args.amount) {
    return {
      success: false,
      error: `Insufficient session budget: ${budget.remaining} < ${args.amount}`
    };
  }

  budget.spent += args.amount;
  budget.remaining -= args.amount;
  sessionBudgets.set(args.sessionId, budget);

  // Update entity reserved balance
  const balance = getOrCreateBalance(budget.entityId);
  balance.reserved -= args.amount;
  balance.lastUpdated = new Date().toISOString();
  balances.set(budget.entityId, balance);

  recordTransaction({
    type: "discharge",
    fromEntity: `session:${args.sessionId}`,
    toEntity: "system",
    amount: args.amount,
    metadata: { action: args.action },
  });

  return { success: true, budget };
}

// ============================================================================
// MCP Server Setup
// ============================================================================

const server = new Server(
  {
    name: "web4-economy",
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
      name: "web4.io/atp/balance",
      description: "Query ATP/ADP balance for an entity",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: {
            type: "string",
            description: "Entity identifier",
          },
        },
        required: ["entityId"],
      },
    },
    {
      name: "web4.io/atp/transfer",
      description: "Transfer ATP between entities",
      inputSchema: {
        type: "object" as const,
        properties: {
          fromEntity: {
            type: "string",
            description: "Source entity",
          },
          toEntity: {
            type: "string",
            description: "Destination entity",
          },
          amount: {
            type: "number",
            description: "Amount to transfer",
          },
          memo: {
            type: "string",
            description: "Optional memo",
          },
        },
        required: ["fromEntity", "toEntity", "amount"],
      },
    },
    {
      name: "web4.io/atp/price",
      description: "Calculate action price using 3D pricing (trust, urgency, complexity)",
      inputSchema: {
        type: "object" as const,
        properties: {
          actionType: {
            type: "string",
            description: "Type of action (e.g., 'read:file', 'execute:command')",
          },
          trustLevel: {
            type: "number",
            description: "Trust level (0-1) for discount calculation",
          },
          urgency: {
            type: "string",
            enum: ["low", "normal", "high", "critical"],
            description: "Action urgency",
          },
          complexity: {
            type: "string",
            enum: ["simple", "moderate", "complex", "very-complex"],
            description: "Action complexity",
          },
        },
        required: ["actionType"],
      },
    },
    {
      name: "web4.io/atp/charge",
      description: "Charge ATP (add tokens, pay down debt)",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: {
            type: "string",
            description: "Entity to charge",
          },
          amount: {
            type: "number",
            description: "Amount to charge",
          },
          source: {
            type: "string",
            description: "Source of the charge (e.g., 'work:completed')",
          },
        },
        required: ["entityId", "amount"],
      },
    },
    {
      name: "web4.io/atp/discharge",
      description: "Discharge ATP (spend tokens, may create debt)",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: {
            type: "string",
            description: "Entity to discharge",
          },
          amount: {
            type: "number",
            description: "Amount to discharge",
          },
          reason: {
            type: "string",
            description: "Reason for discharge",
          },
        },
        required: ["entityId", "amount"],
      },
    },
    {
      name: "web4.io/atp/demurrage",
      description: "Apply demurrage (holding cost) to encourage circulation",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: {
            type: "string",
            description: "Entity to apply demurrage to",
          },
          rate: {
            type: "number",
            description: "Demurrage rate (default 0.01 = 1%)",
          },
        },
        required: ["entityId"],
      },
    },
    {
      name: "web4.io/atp/history",
      description: "Get transaction history",
      inputSchema: {
        type: "object" as const,
        properties: {
          entityId: {
            type: "string",
            description: "Entity to get history for",
          },
          limit: {
            type: "number",
            description: "Maximum transactions to return",
          },
          type: {
            type: "string",
            enum: ["transfer", "charge", "discharge", "demurrage", "reserve", "release"],
            description: "Filter by transaction type",
          },
          since: {
            type: "string",
            description: "ISO8601 timestamp to filter from",
          },
        },
        required: ["entityId"],
      },
    },
    {
      name: "web4.io/atp/budget",
      description: "Get or create session budget",
      inputSchema: {
        type: "object" as const,
        properties: {
          sessionId: {
            type: "string",
            description: "Session identifier",
          },
          entityId: {
            type: "string",
            description: "Entity (required when creating)",
          },
          allocated: {
            type: "number",
            description: "Amount to allocate (for creation)",
          },
          expiresInHours: {
            type: "number",
            description: "Hours until budget expires",
          },
          action: {
            type: "string",
            enum: ["get", "create", "spend"],
            description: "Budget action",
          },
          spendAmount: {
            type: "number",
            description: "Amount to spend (for spend action)",
          },
          spendAction: {
            type: "string",
            description: "Action being spent on",
          },
        },
        required: ["sessionId"],
      },
    },
  ],
}));

// Tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "web4.io/atp/balance": {
        const result = await getBalance(args as Parameters<typeof getBalance>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/atp/transfer": {
        const result = await transferATP(args as Parameters<typeof transferATP>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/atp/price": {
        const result = await getActionPrice(args as Parameters<typeof getActionPrice>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/atp/charge": {
        const result = await chargeATP(args as Parameters<typeof chargeATP>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/atp/discharge": {
        const result = await dischargeATP(args as Parameters<typeof dischargeATP>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/atp/demurrage": {
        const result = await applyDemurrage(args as Parameters<typeof applyDemurrage>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/atp/history": {
        const result = await getTransactionHistory(
          args as Parameters<typeof getTransactionHistory>[0]
        );
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/atp/budget": {
        const typedArgs = args as {
          sessionId: string;
          entityId?: string;
          allocated?: number;
          expiresInHours?: number;
          action?: "get" | "create" | "spend";
          spendAmount?: number;
          spendAction?: string;
        };

        const action = typedArgs.action ?? "get";

        if (action === "create") {
          if (!typedArgs.entityId || !typedArgs.allocated) {
            return {
              content: [
                {
                  type: "text" as const,
                  text: JSON.stringify({ error: "entityId and allocated required for create" }),
                },
              ],
              isError: true,
            };
          }
          const result = await createSessionBudget({
            sessionId: typedArgs.sessionId,
            entityId: typedArgs.entityId,
            allocated: typedArgs.allocated,
            expiresInHours: typedArgs.expiresInHours,
          });
          return {
            content: [
              {
                type: "text" as const,
                text: JSON.stringify(result, null, 2),
              },
            ],
          };
        } else if (action === "spend") {
          if (!typedArgs.spendAmount) {
            return {
              content: [
                {
                  type: "text" as const,
                  text: JSON.stringify({ error: "spendAmount required for spend action" }),
                },
              ],
              isError: true,
            };
          }
          const result = await spendSessionBudget({
            sessionId: typedArgs.sessionId,
            amount: typedArgs.spendAmount,
            action: typedArgs.spendAction,
          });
          return {
            content: [
              {
                type: "text" as const,
                text: JSON.stringify(result, null, 2),
              },
            ],
          };
        } else {
          const result = await getSessionBudget({ sessionId: typedArgs.sessionId });
          return {
            content: [
              {
                type: "text" as const,
                text: JSON.stringify(result, null, 2),
              },
            ],
          };
        }
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
      uri: "web4://economy/{entity_id}",
      name: "Entity Economy Profile",
      description: "Balance and transaction summary for an entity",
      mimeType: "application/json",
    },
  ],
}));

// Resource reading
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  const match = uri.match(/^web4:\/\/economy\/(.+)$/);
  if (!match) {
    throw new Error(`Invalid resource URI: ${uri}`);
  }

  const entityId = match[1];
  const balance = getOrCreateBalance(entityId);
  const recentTx = transactions
    .filter((tx) => tx.fromEntity === entityId || tx.toEntity === entityId)
    .slice(-10);

  // Find active session budgets
  const activeBudgets: SessionBudget[] = [];
  for (const [, budget] of sessionBudgets) {
    if (budget.entityId === entityId) {
      activeBudgets.push(budget);
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
            balance,
            recentTransactions: recentTx,
            activeBudgets,
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
  console.error("Web4 Economy MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
