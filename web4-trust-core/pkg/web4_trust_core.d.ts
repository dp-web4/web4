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

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly __wbg_entitytrust_free: (a: number, b: number) => void;
    readonly __wbg_t3tensor_free: (a: number, b: number) => void;
    readonly __wbg_v3tensor_free: (a: number, b: number) => void;
    readonly __wbg_wasmatpaccount_free: (a: number, b: number) => void;
    readonly __wbg_wasmr7action_free: (a: number, b: number) => void;
    readonly __wbg_wasmroleassignment_free: (a: number, b: number) => void;
    readonly __wbg_wasmsociety_free: (a: number, b: number) => void;
    readonly __wbg_wasmsocietyrole_free: (a: number, b: number) => void;
    readonly __wbg_wasmtruststore_free: (a: number, b: number) => void;
    readonly entitytrust_actionCount: (a: number) => bigint;
    readonly entitytrust_applyDecay: (a: number, b: number, c: number) => number;
    readonly entitytrust_daysSinceLastAction: (a: number) => number;
    readonly entitytrust_entityId: (a: number) => [number, number];
    readonly entitytrust_entityName: (a: number) => [number, number];
    readonly entitytrust_entityType: (a: number) => [number, number];
    readonly entitytrust_giveWitness: (a: number, b: number, c: number, d: number, e: number) => void;
    readonly entitytrust_hasWitnessed: (a: number) => any;
    readonly entitytrust_new: (a: number, b: number) => number;
    readonly entitytrust_receiveWitness: (a: number, b: number, c: number, d: number, e: number) => void;
    readonly entitytrust_successCount: (a: number) => bigint;
    readonly entitytrust_successRate: (a: number) => number;
    readonly entitytrust_t3Average: (a: number) => number;
    readonly entitytrust_talent: (a: number) => number;
    readonly entitytrust_temperament: (a: number) => number;
    readonly entitytrust_toJSON: (a: number) => any;
    readonly entitytrust_training: (a: number) => number;
    readonly entitytrust_trustLevel: (a: number) => [number, number];
    readonly entitytrust_updateFromOutcome: (a: number, b: number, c: number) => void;
    readonly entitytrust_v3Average: (a: number) => number;
    readonly entitytrust_validity: (a: number) => number;
    readonly entitytrust_valuation: (a: number) => number;
    readonly entitytrust_veracity: (a: number) => number;
    readonly entitytrust_witnessCount: (a: number) => bigint;
    readonly entitytrust_witnessedBy: (a: number) => any;
    readonly init: () => void;
    readonly t3tensor_applyDecay: (a: number, b: number, c: number) => number;
    readonly t3tensor_level: (a: number) => [number, number];
    readonly t3tensor_neutral: () => number;
    readonly t3tensor_new: (a: number, b: number, c: number) => number;
    readonly t3tensor_set_talent: (a: number, b: number) => void;
    readonly t3tensor_set_temperament: (a: number, b: number) => void;
    readonly t3tensor_set_training: (a: number, b: number) => void;
    readonly t3tensor_toJSON: (a: number) => any;
    readonly t3tensor_updateFromOutcome: (a: number, b: number, c: number) => void;
    readonly v3tensor_toJSON: (a: number) => any;
    readonly version: () => [number, number];
    readonly wasmatpaccount_commit: (a: number, b: number) => [number, number, number];
    readonly wasmatpaccount_energyRatio: (a: number) => number;
    readonly wasmatpaccount_lock: (a: number, b: number) => [number, number];
    readonly wasmatpaccount_new: (a: number) => number;
    readonly wasmatpaccount_recharge: (a: number, b: number, c: number) => number;
    readonly wasmatpaccount_rollback: (a: number, b: number) => [number, number, number];
    readonly wasmatpaccount_toJSON: (a: number) => any;
    readonly wasmatpaccount_total: (a: number) => number;
    readonly wasmr7action_actionId: (a: number) => [number, number];
    readonly wasmr7action_canonicalHash: (a: number) => [number, number];
    readonly wasmr7action_computeReputation: (a: number, b: number, c: number, d: number, e: number, f: number) => void;
    readonly wasmr7action_isR7: (a: number) => number;
    readonly wasmr7action_new: (a: number, b: number) => [number, number, number];
    readonly wasmr7action_status: (a: number) => [number, number];
    readonly wasmr7action_toJSON: (a: number) => [number, number, number, number];
    readonly wasmr7action_validate: (a: number) => any;
    readonly wasmroleassignment_addHolder: (a: number, b: number, c: number) => [number, number];
    readonly wasmroleassignment_fillingEntityLctId: (a: number) => [number, number];
    readonly wasmroleassignment_isAuthorized: (a: number, b: number, c: number) => [number, number, number];
    readonly wasmroleassignment_multiHolder: (a: number) => number;
    readonly wasmroleassignment_new: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number) => [number, number, number];
    readonly wasmroleassignment_roleLctId: (a: number) => [number, number];
    readonly wasmroleassignment_rotate: (a: number, b: number, c: number, d: number, e: number) => [number, number];
    readonly wasmsociety_addCitizen: (a: number, b: number, c: number) => [number, number];
    readonly wasmsociety_assignRole: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number, number, number];
    readonly wasmsociety_bootstrap: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
    readonly wasmsociety_goOperational: (a: number) => [number, number];
    readonly wasmsociety_hasRole: (a: number, b: number, c: number, d: number, e: number) => [number, number, number];
    readonly wasmsociety_lctId: (a: number) => [number, number];
    readonly wasmsociety_name: (a: number) => [number, number];
    readonly wasmsociety_state: (a: number) => [number, number];
    readonly wasmsociety_summary: (a: number) => any;
    readonly wasmsociety_validateMinimumViable: (a: number) => any;
    readonly wasmsocietyrole_baseMandatory: () => any;
    readonly wasmsocietyrole_description: (a: number) => [number, number];
    readonly wasmsocietyrole_isBaseMandatory: (a: number) => number;
    readonly wasmsocietyrole_name: (a: number) => [number, number];
    readonly wasmsocietyrole_new: (a: number, b: number) => [number, number, number];
    readonly wasmtruststore_count: (a: number) => number;
    readonly wasmtruststore_delete: (a: number, b: number, c: number) => [number, number, number];
    readonly wasmtruststore_exists: (a: number, b: number, c: number) => [number, number, number];
    readonly wasmtruststore_get: (a: number, b: number, c: number) => [number, number, number];
    readonly wasmtruststore_listEntities: (a: number) => [number, number, number];
    readonly wasmtruststore_new: () => number;
    readonly wasmtruststore_save: (a: number, b: number) => [number, number];
    readonly wasmtruststore_update: (a: number, b: number, c: number, d: number, e: number) => [number, number, number];
    readonly wasmtruststore_witness: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number, number];
    readonly t3tensor_average: (a: number) => number;
    readonly v3tensor_average: (a: number) => number;
    readonly v3tensor_neutral: () => number;
    readonly t3tensor_talent: (a: number) => number;
    readonly t3tensor_temperament: (a: number) => number;
    readonly t3tensor_training: (a: number) => number;
    readonly v3tensor_validity: (a: number) => number;
    readonly v3tensor_valuation: (a: number) => number;
    readonly v3tensor_veracity: (a: number) => number;
    readonly wasmatpaccount_adp: (a: number) => number;
    readonly wasmatpaccount_available: (a: number) => number;
    readonly wasmatpaccount_initialBalance: (a: number) => number;
    readonly wasmatpaccount_locked: (a: number) => number;
    readonly v3tensor_new: (a: number, b: number, c: number) => number;
    readonly __wbindgen_exn_store: (a: number) => void;
    readonly __externref_table_alloc: () => number;
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __externref_table_dealloc: (a: number) => void;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
