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
