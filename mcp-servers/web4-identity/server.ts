#!/usr/bin/env node
/**
 * Web4 Identity MCP Server
 *
 * Open Source (AGPL-3.0) - Part of Web4 Trust Infrastructure
 *
 * Provides LCT (Linked Context Token) identity operations for AI agents.
 *
 * Tools:
 *   - web4.io/identity/create   - Mint new LCT
 *   - web4.io/identity/verify   - Verify LCT signature
 *   - web4.io/identity/bind     - Bind to hardware
 *   - web4.io/identity/revoke   - Revoke identity
 *   - web4.io/identity/delegate - Create delegation
 *   - web4.io/identity/witness  - Record witnessing
 *   - web4.io/identity/chain    - Get witness chain
 *   - web4.io/identity/query    - Query identity details
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
// Types
// ============================================================================

interface LCT {
  id: string;
  type: "root" | "device" | "software" | "session" | "delegated";
  subject: string;
  issuer: string;
  issuedAt: string;
  expiresAt?: string;
  publicKey: string;
  hardwareBinding?: HardwareBinding;
  delegation?: DelegationInfo;
  revoked: boolean;
  revokedAt?: string;
  signature: string;
}

interface HardwareBinding {
  type: "tpm" | "secure-enclave" | "yubikey" | "software";
  deviceId: string;
  attestation?: string;
  boundAt: string;
}

interface DelegationInfo {
  parentLctId: string;
  scope: string[];
  constraints: Record<string, unknown>;
  delegatedAt: string;
}

interface WitnessRecord {
  id: string;
  lctId: string;
  witnessLctId: string;
  action: string;
  timestamp: string;
  signature: string;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// In-Memory State (would be backed by persistent storage in production)
// ============================================================================

const lcts = new Map<string, LCT>();
const witnessRecords = new Map<string, WitnessRecord[]>();

// ============================================================================
// Helper Functions
// ============================================================================

function generateId(prefix: string): string {
  return `${prefix}:${crypto.randomUUID()}`;
}

function generateKeyPair(): { publicKey: string; privateKey: string } {
  const { publicKey, privateKey } = crypto.generateKeyPairSync("ec", {
    namedCurve: "P-256",
  });
  return {
    publicKey: publicKey.export({ type: "spki", format: "pem" }) as string,
    privateKey: privateKey.export({ type: "pkcs8", format: "pem" }) as string,
  };
}

function signData(data: string, privateKey: string): string {
  const sign = crypto.createSign("SHA256");
  sign.update(data);
  return sign.sign(privateKey, "base64");
}

function verifySignature(data: string, signature: string, publicKey: string): boolean {
  try {
    const verify = crypto.createVerify("SHA256");
    verify.update(data);
    return verify.verify(publicKey, signature, "base64");
  } catch {
    return false;
  }
}

function createLctPayload(lct: Omit<LCT, "signature">): string {
  return JSON.stringify({
    id: lct.id,
    type: lct.type,
    subject: lct.subject,
    issuer: lct.issuer,
    issuedAt: lct.issuedAt,
    expiresAt: lct.expiresAt,
    publicKey: lct.publicKey,
    hardwareBinding: lct.hardwareBinding,
    delegation: lct.delegation,
  });
}

// ============================================================================
// Tool Implementations
// ============================================================================

async function createIdentity(args: {
  type: "root" | "device" | "software" | "session";
  subject: string;
  issuer?: string;
  expiresInDays?: number;
}): Promise<{ lct: LCT; privateKey: string }> {
  const { publicKey, privateKey } = generateKeyPair();
  const now = new Date();

  const lctData: Omit<LCT, "signature"> = {
    id: generateId("lct"),
    type: args.type,
    subject: args.subject,
    issuer: args.issuer || args.subject,
    issuedAt: now.toISOString(),
    expiresAt: args.expiresInDays
      ? new Date(now.getTime() + args.expiresInDays * 24 * 60 * 60 * 1000).toISOString()
      : undefined,
    publicKey,
    revoked: false,
  };

  const signature = signData(createLctPayload(lctData), privateKey);
  const lct: LCT = { ...lctData, signature };

  lcts.set(lct.id, lct);
  witnessRecords.set(lct.id, []);

  return { lct, privateKey };
}

async function verifyIdentity(args: { lctId: string }): Promise<{
  valid: boolean;
  lct?: LCT;
  errors: string[];
}> {
  const lct = lcts.get(args.lctId);
  const errors: string[] = [];

  if (!lct) {
    return { valid: false, errors: ["LCT not found"] };
  }

  if (lct.revoked) {
    errors.push(`LCT revoked at ${lct.revokedAt}`);
  }

  if (lct.expiresAt && new Date(lct.expiresAt) < new Date()) {
    errors.push(`LCT expired at ${lct.expiresAt}`);
  }

  const payload = createLctPayload(lct);
  if (!verifySignature(payload, lct.signature, lct.publicKey)) {
    errors.push("Invalid signature");
  }

  // Verify delegation chain if delegated
  if (lct.delegation) {
    const parentResult = await verifyIdentity({ lctId: lct.delegation.parentLctId });
    if (!parentResult.valid) {
      errors.push(`Parent LCT invalid: ${parentResult.errors.join(", ")}`);
    }
  }

  return {
    valid: errors.length === 0,
    lct,
    errors,
  };
}

async function bindHardware(args: {
  lctId: string;
  bindingType: "tpm" | "secure-enclave" | "yubikey" | "software";
  deviceId: string;
  attestation?: string;
}): Promise<{ success: boolean; binding?: HardwareBinding; error?: string }> {
  const lct = lcts.get(args.lctId);

  if (!lct) {
    return { success: false, error: "LCT not found" };
  }

  if (lct.hardwareBinding) {
    return { success: false, error: "LCT already bound to hardware" };
  }

  const binding: HardwareBinding = {
    type: args.bindingType,
    deviceId: args.deviceId,
    attestation: args.attestation,
    boundAt: new Date().toISOString(),
  };

  lct.hardwareBinding = binding;
  lcts.set(lct.id, lct);

  return { success: true, binding };
}

async function revokeIdentity(args: {
  lctId: string;
  reason?: string;
}): Promise<{ success: boolean; error?: string }> {
  const lct = lcts.get(args.lctId);

  if (!lct) {
    return { success: false, error: "LCT not found" };
  }

  if (lct.revoked) {
    return { success: false, error: "LCT already revoked" };
  }

  lct.revoked = true;
  lct.revokedAt = new Date().toISOString();
  lcts.set(lct.id, lct);

  // Also revoke any delegated LCTs
  for (const [, childLct] of lcts) {
    if (childLct.delegation?.parentLctId === args.lctId && !childLct.revoked) {
      await revokeIdentity({ lctId: childLct.id, reason: "Parent LCT revoked" });
    }
  }

  return { success: true };
}

async function delegateIdentity(args: {
  parentLctId: string;
  subject: string;
  scope: string[];
  constraints?: Record<string, unknown>;
  expiresInDays?: number;
}): Promise<{ lct: LCT; privateKey: string } | { error: string }> {
  const parentLct = lcts.get(args.parentLctId);

  if (!parentLct) {
    return { error: "Parent LCT not found" };
  }

  const parentVerify = await verifyIdentity({ lctId: args.parentLctId });
  if (!parentVerify.valid) {
    return { error: `Parent LCT invalid: ${parentVerify.errors.join(", ")}` };
  }

  const { publicKey, privateKey } = generateKeyPair();
  const now = new Date();

  const lctData: Omit<LCT, "signature"> = {
    id: generateId("lct"),
    type: "delegated",
    subject: args.subject,
    issuer: parentLct.subject,
    issuedAt: now.toISOString(),
    expiresAt: args.expiresInDays
      ? new Date(now.getTime() + args.expiresInDays * 24 * 60 * 60 * 1000).toISOString()
      : parentLct.expiresAt, // Inherit parent expiration if not specified
    publicKey,
    delegation: {
      parentLctId: args.parentLctId,
      scope: args.scope,
      constraints: args.constraints || {},
      delegatedAt: now.toISOString(),
    },
    revoked: false,
  };

  const signature = signData(createLctPayload(lctData), privateKey);
  const lct: LCT = { ...lctData, signature };

  lcts.set(lct.id, lct);
  witnessRecords.set(lct.id, []);

  return { lct, privateKey };
}

async function recordWitness(args: {
  lctId: string;
  witnessLctId: string;
  action: string;
  metadata?: Record<string, unknown>;
  privateKey: string;
}): Promise<{ record: WitnessRecord } | { error: string }> {
  const lct = lcts.get(args.lctId);
  const witnessLct = lcts.get(args.witnessLctId);

  if (!lct) {
    return { error: "Subject LCT not found" };
  }

  if (!witnessLct) {
    return { error: "Witness LCT not found" };
  }

  const witnessVerify = await verifyIdentity({ lctId: args.witnessLctId });
  if (!witnessVerify.valid) {
    return { error: `Witness LCT invalid: ${witnessVerify.errors.join(", ")}` };
  }

  const record: Omit<WitnessRecord, "signature"> = {
    id: generateId("witness"),
    lctId: args.lctId,
    witnessLctId: args.witnessLctId,
    action: args.action,
    timestamp: new Date().toISOString(),
    metadata: args.metadata,
  };

  const signature = signData(JSON.stringify(record), args.privateKey);
  const fullRecord: WitnessRecord = { ...record, signature };

  const records = witnessRecords.get(args.lctId) || [];
  records.push(fullRecord);
  witnessRecords.set(args.lctId, records);

  return { record: fullRecord };
}

async function getWitnessChain(args: {
  lctId: string;
  limit?: number;
}): Promise<{ chain: WitnessRecord[]; delegationChain: string[] }> {
  const records = witnessRecords.get(args.lctId) || [];
  const chain = args.limit ? records.slice(-args.limit) : records;

  // Build delegation chain
  const delegationChain: string[] = [args.lctId];
  let currentLct = lcts.get(args.lctId);

  while (currentLct?.delegation) {
    delegationChain.push(currentLct.delegation.parentLctId);
    currentLct = lcts.get(currentLct.delegation.parentLctId);
  }

  return { chain, delegationChain };
}

async function queryIdentity(args: {
  lctId?: string;
  subject?: string;
  type?: string;
  includeRevoked?: boolean;
}): Promise<{ results: LCT[] }> {
  const results: LCT[] = [];

  for (const [, lct] of lcts) {
    if (args.lctId && lct.id !== args.lctId) continue;
    if (args.subject && !lct.subject.includes(args.subject)) continue;
    if (args.type && lct.type !== args.type) continue;
    if (!args.includeRevoked && lct.revoked) continue;

    results.push(lct);
  }

  return { results };
}

// ============================================================================
// MCP Server Setup
// ============================================================================

const server = new Server(
  {
    name: "web4-identity",
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
      name: "web4.io/identity/create",
      description: "Mint a new Linked Context Token (LCT) identity",
      inputSchema: {
        type: "object" as const,
        properties: {
          type: {
            type: "string",
            enum: ["root", "device", "software", "session"],
            description: "Type of LCT to create",
          },
          subject: {
            type: "string",
            description: "Subject identifier (e.g., 'agent:claude-1', 'user:alice')",
          },
          issuer: {
            type: "string",
            description: "Issuer identifier (defaults to subject for self-issued)",
          },
          expiresInDays: {
            type: "number",
            description: "Days until expiration (optional)",
          },
        },
        required: ["type", "subject"],
      },
    },
    {
      name: "web4.io/identity/verify",
      description: "Verify an LCT's validity (signature, expiration, revocation, chain)",
      inputSchema: {
        type: "object" as const,
        properties: {
          lctId: {
            type: "string",
            description: "The LCT ID to verify",
          },
        },
        required: ["lctId"],
      },
    },
    {
      name: "web4.io/identity/bind",
      description: "Bind an LCT to hardware (TPM, Secure Enclave, YubiKey)",
      inputSchema: {
        type: "object" as const,
        properties: {
          lctId: {
            type: "string",
            description: "The LCT ID to bind",
          },
          bindingType: {
            type: "string",
            enum: ["tpm", "secure-enclave", "yubikey", "software"],
            description: "Type of hardware binding",
          },
          deviceId: {
            type: "string",
            description: "Hardware device identifier",
          },
          attestation: {
            type: "string",
            description: "Hardware attestation certificate (optional)",
          },
        },
        required: ["lctId", "bindingType", "deviceId"],
      },
    },
    {
      name: "web4.io/identity/revoke",
      description: "Revoke an LCT (also revokes all delegated children)",
      inputSchema: {
        type: "object" as const,
        properties: {
          lctId: {
            type: "string",
            description: "The LCT ID to revoke",
          },
          reason: {
            type: "string",
            description: "Reason for revocation",
          },
        },
        required: ["lctId"],
      },
    },
    {
      name: "web4.io/identity/delegate",
      description: "Create a delegated LCT with scoped authority",
      inputSchema: {
        type: "object" as const,
        properties: {
          parentLctId: {
            type: "string",
            description: "Parent LCT ID to delegate from",
          },
          subject: {
            type: "string",
            description: "Subject identifier for the new delegated LCT",
          },
          scope: {
            type: "array",
            items: { type: "string" },
            description: "Allowed scopes (e.g., ['read:code', 'write:docs'])",
          },
          constraints: {
            type: "object",
            description: "Additional constraints on the delegation",
          },
          expiresInDays: {
            type: "number",
            description: "Days until expiration (defaults to parent expiration)",
          },
        },
        required: ["parentLctId", "subject", "scope"],
      },
    },
    {
      name: "web4.io/identity/witness",
      description: "Record a witness attestation for an LCT's action",
      inputSchema: {
        type: "object" as const,
        properties: {
          lctId: {
            type: "string",
            description: "The LCT ID being witnessed",
          },
          witnessLctId: {
            type: "string",
            description: "The witnessing LCT ID",
          },
          action: {
            type: "string",
            description: "Action being witnessed",
          },
          metadata: {
            type: "object",
            description: "Additional metadata about the witnessed action",
          },
          privateKey: {
            type: "string",
            description: "Witness private key for signing",
          },
        },
        required: ["lctId", "witnessLctId", "action", "privateKey"],
      },
    },
    {
      name: "web4.io/identity/chain",
      description: "Get the witness chain and delegation chain for an LCT",
      inputSchema: {
        type: "object" as const,
        properties: {
          lctId: {
            type: "string",
            description: "The LCT ID",
          },
          limit: {
            type: "number",
            description: "Maximum number of witness records to return",
          },
        },
        required: ["lctId"],
      },
    },
    {
      name: "web4.io/identity/query",
      description: "Query identities by various criteria",
      inputSchema: {
        type: "object" as const,
        properties: {
          lctId: {
            type: "string",
            description: "Specific LCT ID to query",
          },
          subject: {
            type: "string",
            description: "Subject pattern to match",
          },
          type: {
            type: "string",
            enum: ["root", "device", "software", "session", "delegated"],
            description: "LCT type filter",
          },
          includeRevoked: {
            type: "boolean",
            description: "Include revoked LCTs in results",
          },
        },
      },
    },
  ],
}));

// Tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "web4.io/identity/create": {
        const result = await createIdentity(args as Parameters<typeof createIdentity>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/identity/verify": {
        const result = await verifyIdentity(args as Parameters<typeof verifyIdentity>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/identity/bind": {
        const result = await bindHardware(args as Parameters<typeof bindHardware>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/identity/revoke": {
        const result = await revokeIdentity(args as Parameters<typeof revokeIdentity>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/identity/delegate": {
        const result = await delegateIdentity(args as Parameters<typeof delegateIdentity>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/identity/witness": {
        const result = await recordWitness(args as Parameters<typeof recordWitness>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/identity/chain": {
        const result = await getWitnessChain(args as Parameters<typeof getWitnessChain>[0]);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "web4.io/identity/query": {
        const result = await queryIdentity(args as Parameters<typeof queryIdentity>[0]);
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
      uri: "web4://identity/{lct_id}",
      name: "LCT Identity Document",
      description: "Full LCT document including delegation chain and witness records",
      mimeType: "application/json",
    },
  ],
}));

// Resource reading
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  const match = uri.match(/^web4:\/\/identity\/(.+)$/);
  if (!match) {
    throw new Error(`Invalid resource URI: ${uri}`);
  }

  const lctId = match[1];
  const lct = lcts.get(lctId);

  if (!lct) {
    throw new Error(`LCT not found: ${lctId}`);
  }

  const verification = await verifyIdentity({ lctId });
  const chain = await getWitnessChain({ lctId });

  return {
    contents: [
      {
        uri,
        mimeType: "application/json",
        text: JSON.stringify(
          {
            lct,
            verification,
            witnessChain: chain.chain,
            delegationChain: chain.delegationChain,
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
  console.error("Web4 Identity MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
