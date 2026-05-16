/* tslint:disable */
/* eslint-disable */

/**
 * WASM-exposed EntityTrust
 */
export class EntityTrust {
    free(): void;
    [Symbol.dispose](): void;
    /**
     * Apply decay
     */
    applyDecay(days_inactive: number, decay_rate: number): boolean;
    /**
     * Days since last action
     */
    daysSinceLastAction(): number;
    /**
     * Give witness event
     */
    giveWitness(target_id: string, success: boolean, magnitude: number): void;
    constructor(entity_id: string);
    /**
     * Receive witness event
     */
    receiveWitness(witness_id: string, success: boolean, magnitude: number): void;
    /**
     * Success rate
     */
    successRate(): number;
    /**
     * Get T3 average
     */
    t3Average(): number;
    /**
     * Convert to JSON object
     */
    toJSON(): any;
    /**
     * Get trust level
     */
    trustLevel(): string;
    /**
     * Update from action outcome
     */
    updateFromOutcome(success: boolean, magnitude: number): void;
    /**
     * Get V3 average
     */
    v3Average(): number;
    readonly actionCount: bigint;
    readonly entityId: string;
    readonly entityName: string;
    readonly entityType: string;
    readonly hasWitnessed: Array<any>;
    readonly successCount: bigint;
    readonly talent: number;
    readonly temperament: number;
    readonly training: number;
    readonly validity: number;
    readonly valuation: number;
    readonly veracity: number;
    readonly witnessCount: bigint;
    readonly witnessedBy: Array<any>;
}

/**
 * WASM-exposed T3 Trust Tensor (Talent/Training/Temperament)
 */
export class T3Tensor {
    free(): void;
    [Symbol.dispose](): void;
    /**
     * Apply temporal decay
     */
    applyDecay(days_inactive: number, decay_rate: number): boolean;
    /**
     * Calculate average trust score
     */
    average(): number;
    /**
     * Get trust level as string
     */
    level(): string;
    /**
     * Create a neutral tensor (all 0.5)
     */
    static neutral(): T3Tensor;
    /**
     * Create a new T3 tensor with specified values
     */
    constructor(talent: number, training: number, temperament: number);
    /**
     * Convert to JSON object
     */
    toJSON(): any;
    /**
     * Update from action outcome
     */
    updateFromOutcome(success: boolean, magnitude: number): void;
    talent: number;
    temperament: number;
    training: number;
}

/**
 * WASM-exposed V3 Value Tensor (Valuation/Veracity/Validity)
 */
export class V3Tensor {
    free(): void;
    [Symbol.dispose](): void;
    average(): number;
    static neutral(): V3Tensor;
    constructor(valuation: number, veracity: number, validity: number);
    toJSON(): any;
    readonly validity: number;
    readonly valuation: number;
    readonly veracity: number;
}

/**
 * WASM-exposed ATPAccount — bio-inspired energy metabolism.
 */
export class WasmATPAccount {
    free(): void;
    [Symbol.dispose](): void;
    /**
     * Commit locked tokens to ADP (discharge on success).
     */
    commit(amount: number): number;
    /**
     * Energy ratio: ATP / (ATP + ADP). High = earning, low = spending.
     */
    energyRatio(): number;
    /**
     * Lock tokens from available to escrow.
     */
    lock(amount: number): void;
    /**
     * Create a new ATP account with the given initial balance.
     */
    constructor(initial: number);
    /**
     * Recharge ATP up to max_multiplier * initial_balance.
     * Returns actual amount recharged.
     */
    recharge(rate: number, max_multiplier: number): number;
    /**
     * Rollback locked tokens back to available (on failure/cancel).
     */
    rollback(amount: number): number;
    /**
     * Convert to JSON object.
     */
    toJSON(): any;
    /**
     * Total active ATP (available + locked).
     */
    total(): number;
    /**
     * Discharged tokens (ADP).
     */
    readonly adp: number;
    /**
     * Available ATP.
     */
    readonly available: number;
    /**
     * Initial balance.
     */
    readonly initialBalance: number;
    /**
     * Locked (escrowed) ATP.
     */
    readonly locked: number;
}

/**
 * WASM-exposed R7Action — the complete R6/R7 action framework.
 *
 * R7 actions are constructed from a JSON string containing rules, role,
 * request, reference, and resource fields. This keeps the TypeScript API
 * clean while preserving the full Rust type structure.
 */
export class WasmR7Action {
    free(): void;
    [Symbol.dispose](): void;
    /**
     * Compute the canonical hash for chain integrity.
     */
    canonicalHash(): string;
    /**
     * Compute reputation delta from a quality score (makes this an R7 action).
     *
     * quality: 0.0 to 1.0. Below 0.5 = negative, above 0.5 = positive.
     */
    computeReputation(quality: number, rule_triggered: string, reason: string): void;
    /**
     * Whether this is an R7 action (has reputation tracking).
     */
    isR7(): boolean;
    /**
     * Create a new R7 action from a JSON configuration string.
     *
     * Expected JSON shape:
     * ```json
     * {
     *   "rules": { "law_hash": "sha256:...", "society": "lct:...",
     *              "constraints": [], "permissions": ["*"], "prohibitions": [] },
     *   "role": { "actor_lct": "lct:...", "role_lct": "lct:...", "paired_at": "..." },
     *   "request": { "action": "file_write", "target": "...", "parameters": {},
     *                "atp_stake": 10.0, "nonce": "...", "constraints": {} },
     *   "reference": { "precedents": [], "mrh_depth": 3, "relevant_entities": [],
     *                  "witnesses": [] },
     *   "resource": { "required_atp": 5.0, "available_atp": 100.0, "compute": {},
     *                 "escrow_amount": 5.0, "escrow_condition": "result_verified" }
     * }
     * ```
     */
    constructor(config_json: string);
    /**
     * Convert the full action to a JSON string.
     */
    toJSON(): string;
    /**
     * Validate the action before execution.
     * Returns a JS array of error strings (empty = valid).
     */
    validate(): Array<any>;
    /**
     * The unique action ID.
     */
    readonly actionId: string;
    /**
     * Current action status as string.
     */
    readonly status: string;
}

/**
 * WASM-exposed RoleAssignment — binds a role to its LCT and tracks filling entity.
 */
export class WasmRoleAssignment {
    free(): void;
    [Symbol.dispose](): void;
    /**
     * Add an additional holder (committee/federation pattern).
     */
    addHolder(entity_lct_id: string): void;
    /**
     * Check if an entity is authorized to act in this role.
     */
    isAuthorized(entity_lct_id: string): boolean;
    /**
     * Create a new role assignment.
     *
     * Arguments are UUID strings (will be parsed).
     */
    constructor(role_name: string, role_lct_id: string, filling_entity_lct_id: string, assigned_by: string);
    /**
     * Rotate the filling entity. The role-LCT stays the same.
     */
    rotate(new_entity_lct_id: string, rotated_by: string): void;
    /**
     * The filling entity's LCT ID.
     */
    readonly fillingEntityLctId: string;
    /**
     * Whether this role supports multiple holders.
     */
    readonly multiHolder: boolean;
    /**
     * The role's LCT ID.
     */
    readonly roleLctId: string;
}

/**
 * WASM-exposed Society — self-sovereign organizational unit.
 */
export class WasmSociety {
    private constructor();
    free(): void;
    [Symbol.dispose](): void;
    /**
     * Add a citizen to the society.
     */
    addCitizen(entity_lct_id: string): void;
    /**
     * Assign a role to an entity. Only Sovereign or Administrator can assign.
     * Returns the role's LCT ID.
     */
    assignRole(role_name: string, entity_lct_id: string, assigned_by: string): string;
    /**
     * Bootstrap a new society. Returns the society with all 7 base-mandatory
     * roles assigned to the founder.
     */
    static bootstrap(name: string, charter_hash: string, founder_lct_id: string): WasmSociety;
    /**
     * Transition to Operational state (all mandatory roles must be filled).
     */
    goOperational(): void;
    /**
     * Check if an entity holds a specific role.
     */
    hasRole(entity_lct_id: string, role_name: string): boolean;
    /**
     * Get a JSON summary of the society state.
     */
    summary(): any;
    /**
     * Validate minimum viable society requirements.
     * Returns null on success, or a JSON array of error strings on failure.
     */
    validateMinimumViable(): any;
    /**
     * Society's LCT ID.
     */
    readonly lctId: string;
    /**
     * Society name.
     */
    readonly name: string;
    /**
     * Current metabolic state as string.
     */
    readonly state: string;
}

/**
 * WASM-exposed SocietyRole enum.
 *
 * Represents one of the 7 base-mandatory roles, 2 context-mandatory roles,
 * or a custom role. Use the static methods to enumerate roles.
 */
export class WasmSocietyRole {
    free(): void;
    [Symbol.dispose](): void;
    /**
     * Returns the 7 base-mandatory roles as a JS array of WasmSocietyRole.
     */
    static baseMandatory(): Array<any>;
    /**
     * Human-readable description of this role's responsibility.
     */
    description(): string;
    /**
     * Whether this is a base-mandatory role.
     */
    isBaseMandatory(): boolean;
    /**
     * Role name as string.
     */
    name(): string;
    /**
     * Create a role by name. Valid names: sovereign, law_oracle, policy_entity,
     * treasurer, administrator, archivist, citizen, witness, auditor,
     * or "custom:<name>" for custom roles.
     */
    constructor(name: string);
}

/**
 * WASM-exposed TrustStore (in-memory only for WASM)
 */
export class WasmTrustStore {
    free(): void;
    [Symbol.dispose](): void;
    /**
     * Get entity count
     */
    count(): number;
    /**
     * Delete entity
     */
    delete(entity_id: string): boolean;
    /**
     * Check if entity exists
     */
    exists(entity_id: string): boolean;
    /**
     * Get entity trust
     */
    get(entity_id: string): EntityTrust;
    /**
     * List entities
     */
    listEntities(): Array<any>;
    constructor();
    /**
     * Save entity trust
     */
    save(trust: EntityTrust): void;
    /**
     * Update entity from outcome
     */
    update(entity_id: string, success: boolean, magnitude: number): EntityTrust;
    /**
     * Witness event
     */
    witness(witness_id: string, target_id: string, success: boolean, magnitude: number): Array<any>;
}

/**
 * Initialize the WASM module (called automatically)
 */
export function init(): void;

/**
 * Get version string
 */
export function version(): string;
