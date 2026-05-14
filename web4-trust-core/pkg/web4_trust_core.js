/* @ts-self-types="./web4_trust_core.d.ts" */

/**
 * WASM-exposed EntityTrust
 */
export class EntityTrust {
    static __wrap(ptr) {
        ptr = ptr >>> 0;
        const obj = Object.create(EntityTrust.prototype);
        obj.__wbg_ptr = ptr;
        EntityTrustFinalization.register(obj, obj.__wbg_ptr, obj);
        return obj;
    }
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        EntityTrustFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_entitytrust_free(ptr, 0);
    }
    /**
     * @returns {bigint}
     */
    get actionCount() {
        const ret = wasm.entitytrust_actionCount(this.__wbg_ptr);
        return BigInt.asUintN(64, ret);
    }
    /**
     * Apply decay
     * @param {number} days_inactive
     * @param {number} decay_rate
     * @returns {boolean}
     */
    applyDecay(days_inactive, decay_rate) {
        const ret = wasm.entitytrust_applyDecay(this.__wbg_ptr, days_inactive, decay_rate);
        return ret !== 0;
    }
    /**
     * Days since last action
     * @returns {number}
     */
    daysSinceLastAction() {
        const ret = wasm.entitytrust_daysSinceLastAction(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {string}
     */
    get entityId() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.entitytrust_entityId(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * @returns {string}
     */
    get entityName() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.entitytrust_entityName(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * @returns {string}
     */
    get entityType() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.entitytrust_entityType(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Give witness event
     * @param {string} target_id
     * @param {boolean} success
     * @param {number} magnitude
     */
    giveWitness(target_id, success, magnitude) {
        const ptr0 = passStringToWasm0(target_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        wasm.entitytrust_giveWitness(this.__wbg_ptr, ptr0, len0, success, magnitude);
    }
    /**
     * @returns {Array<any>}
     */
    get hasWitnessed() {
        const ret = wasm.entitytrust_hasWitnessed(this.__wbg_ptr);
        return ret;
    }
    /**
     * @param {string} entity_id
     */
    constructor(entity_id) {
        const ptr0 = passStringToWasm0(entity_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.entitytrust_new(ptr0, len0);
        this.__wbg_ptr = ret >>> 0;
        EntityTrustFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * Receive witness event
     * @param {string} witness_id
     * @param {boolean} success
     * @param {number} magnitude
     */
    receiveWitness(witness_id, success, magnitude) {
        const ptr0 = passStringToWasm0(witness_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        wasm.entitytrust_receiveWitness(this.__wbg_ptr, ptr0, len0, success, magnitude);
    }
    /**
     * @returns {bigint}
     */
    get successCount() {
        const ret = wasm.entitytrust_successCount(this.__wbg_ptr);
        return BigInt.asUintN(64, ret);
    }
    /**
     * Success rate
     * @returns {number}
     */
    successRate() {
        const ret = wasm.entitytrust_successRate(this.__wbg_ptr);
        return ret;
    }
    /**
     * Get T3 average
     * @returns {number}
     */
    t3Average() {
        const ret = wasm.entitytrust_t3Average(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get talent() {
        const ret = wasm.entitytrust_talent(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get temperament() {
        const ret = wasm.entitytrust_temperament(this.__wbg_ptr);
        return ret;
    }
    /**
     * Convert to JSON object
     * @returns {any}
     */
    toJSON() {
        const ret = wasm.entitytrust_toJSON(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get training() {
        const ret = wasm.entitytrust_training(this.__wbg_ptr);
        return ret;
    }
    /**
     * Get trust level
     * @returns {string}
     */
    trustLevel() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.entitytrust_trustLevel(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Update from action outcome
     * @param {boolean} success
     * @param {number} magnitude
     */
    updateFromOutcome(success, magnitude) {
        wasm.entitytrust_updateFromOutcome(this.__wbg_ptr, success, magnitude);
    }
    /**
     * Get V3 average
     * @returns {number}
     */
    v3Average() {
        const ret = wasm.entitytrust_v3Average(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get validity() {
        const ret = wasm.entitytrust_validity(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get valuation() {
        const ret = wasm.entitytrust_valuation(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get veracity() {
        const ret = wasm.entitytrust_veracity(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {bigint}
     */
    get witnessCount() {
        const ret = wasm.entitytrust_witnessCount(this.__wbg_ptr);
        return BigInt.asUintN(64, ret);
    }
    /**
     * @returns {Array<any>}
     */
    get witnessedBy() {
        const ret = wasm.entitytrust_witnessedBy(this.__wbg_ptr);
        return ret;
    }
}
if (Symbol.dispose) EntityTrust.prototype[Symbol.dispose] = EntityTrust.prototype.free;

/**
 * WASM-exposed T3 Trust Tensor (Talent/Training/Temperament)
 */
export class T3Tensor {
    static __wrap(ptr) {
        ptr = ptr >>> 0;
        const obj = Object.create(T3Tensor.prototype);
        obj.__wbg_ptr = ptr;
        T3TensorFinalization.register(obj, obj.__wbg_ptr, obj);
        return obj;
    }
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        T3TensorFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_t3tensor_free(ptr, 0);
    }
    /**
     * Apply temporal decay
     * @param {number} days_inactive
     * @param {number} decay_rate
     * @returns {boolean}
     */
    applyDecay(days_inactive, decay_rate) {
        const ret = wasm.t3tensor_applyDecay(this.__wbg_ptr, days_inactive, decay_rate);
        return ret !== 0;
    }
    /**
     * Calculate average trust score
     * @returns {number}
     */
    average() {
        const ret = wasm.entitytrust_t3Average(this.__wbg_ptr);
        return ret;
    }
    /**
     * Get trust level as string
     * @returns {string}
     */
    level() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.t3tensor_level(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Create a neutral tensor (all 0.5)
     * @returns {T3Tensor}
     */
    static neutral() {
        const ret = wasm.t3tensor_neutral();
        return T3Tensor.__wrap(ret);
    }
    /**
     * Create a new T3 tensor with specified values
     * @param {number} talent
     * @param {number} training
     * @param {number} temperament
     */
    constructor(talent, training, temperament) {
        const ret = wasm.t3tensor_new(talent, training, temperament);
        this.__wbg_ptr = ret >>> 0;
        T3TensorFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * @param {number} value
     */
    set talent(value) {
        wasm.t3tensor_set_talent(this.__wbg_ptr, value);
    }
    /**
     * @param {number} value
     */
    set temperament(value) {
        wasm.t3tensor_set_temperament(this.__wbg_ptr, value);
    }
    /**
     * @param {number} value
     */
    set training(value) {
        wasm.t3tensor_set_training(this.__wbg_ptr, value);
    }
    /**
     * @returns {number}
     */
    get talent() {
        const ret = wasm.entitytrust_talent(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get temperament() {
        const ret = wasm.entitytrust_temperament(this.__wbg_ptr);
        return ret;
    }
    /**
     * Convert to JSON object
     * @returns {any}
     */
    toJSON() {
        const ret = wasm.t3tensor_toJSON(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get training() {
        const ret = wasm.entitytrust_training(this.__wbg_ptr);
        return ret;
    }
    /**
     * Update from action outcome
     * @param {boolean} success
     * @param {number} magnitude
     */
    updateFromOutcome(success, magnitude) {
        wasm.t3tensor_updateFromOutcome(this.__wbg_ptr, success, magnitude);
    }
}
if (Symbol.dispose) T3Tensor.prototype[Symbol.dispose] = T3Tensor.prototype.free;

/**
 * WASM-exposed V3 Value Tensor (Valuation/Veracity/Validity)
 */
export class V3Tensor {
    static __wrap(ptr) {
        ptr = ptr >>> 0;
        const obj = Object.create(V3Tensor.prototype);
        obj.__wbg_ptr = ptr;
        V3TensorFinalization.register(obj, obj.__wbg_ptr, obj);
        return obj;
    }
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        V3TensorFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_v3tensor_free(ptr, 0);
    }
    /**
     * @returns {number}
     */
    average() {
        const ret = wasm.entitytrust_t3Average(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {V3Tensor}
     */
    static neutral() {
        const ret = wasm.t3tensor_neutral();
        return V3Tensor.__wrap(ret);
    }
    /**
     * @param {number} valuation
     * @param {number} veracity
     * @param {number} validity
     */
    constructor(valuation, veracity, validity) {
        const ret = wasm.t3tensor_new(valuation, veracity, validity);
        this.__wbg_ptr = ret >>> 0;
        V3TensorFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * @returns {any}
     */
    toJSON() {
        const ret = wasm.v3tensor_toJSON(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get validity() {
        const ret = wasm.entitytrust_temperament(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get valuation() {
        const ret = wasm.entitytrust_talent(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get veracity() {
        const ret = wasm.entitytrust_training(this.__wbg_ptr);
        return ret;
    }
}
if (Symbol.dispose) V3Tensor.prototype[Symbol.dispose] = V3Tensor.prototype.free;

/**
 * WASM-exposed ATPAccount — bio-inspired energy metabolism.
 */
export class WasmATPAccount {
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WasmATPAccountFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wasmatpaccount_free(ptr, 0);
    }
    /**
     * Discharged tokens (ADP).
     * @returns {number}
     */
    get adp() {
        const ret = wasm.entitytrust_temperament(this.__wbg_ptr);
        return ret;
    }
    /**
     * Available ATP.
     * @returns {number}
     */
    get available() {
        const ret = wasm.entitytrust_talent(this.__wbg_ptr);
        return ret;
    }
    /**
     * Commit locked tokens to ADP (discharge on success).
     * @param {number} amount
     * @returns {number}
     */
    commit(amount) {
        const ret = wasm.wasmatpaccount_commit(this.__wbg_ptr, amount);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0];
    }
    /**
     * Energy ratio: ATP / (ATP + ADP). High = earning, low = spending.
     * @returns {number}
     */
    energyRatio() {
        const ret = wasm.wasmatpaccount_energyRatio(this.__wbg_ptr);
        return ret;
    }
    /**
     * Initial balance.
     * @returns {number}
     */
    get initialBalance() {
        const ret = wasm.entitytrust_valuation(this.__wbg_ptr);
        return ret;
    }
    /**
     * Lock tokens from available to escrow.
     * @param {number} amount
     */
    lock(amount) {
        const ret = wasm.wasmatpaccount_lock(this.__wbg_ptr, amount);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Locked (escrowed) ATP.
     * @returns {number}
     */
    get locked() {
        const ret = wasm.entitytrust_training(this.__wbg_ptr);
        return ret;
    }
    /**
     * Create a new ATP account with the given initial balance.
     * @param {number} initial
     */
    constructor(initial) {
        const ret = wasm.wasmatpaccount_new(initial);
        this.__wbg_ptr = ret >>> 0;
        WasmATPAccountFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * Recharge ATP up to max_multiplier * initial_balance.
     * Returns actual amount recharged.
     * @param {number} rate
     * @param {number} max_multiplier
     * @returns {number}
     */
    recharge(rate, max_multiplier) {
        const ret = wasm.wasmatpaccount_recharge(this.__wbg_ptr, rate, max_multiplier);
        return ret;
    }
    /**
     * Rollback locked tokens back to available (on failure/cancel).
     * @param {number} amount
     * @returns {number}
     */
    rollback(amount) {
        const ret = wasm.wasmatpaccount_rollback(this.__wbg_ptr, amount);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0];
    }
    /**
     * Convert to JSON object.
     * @returns {any}
     */
    toJSON() {
        const ret = wasm.wasmatpaccount_toJSON(this.__wbg_ptr);
        return ret;
    }
    /**
     * Total active ATP (available + locked).
     * @returns {number}
     */
    total() {
        const ret = wasm.wasmatpaccount_total(this.__wbg_ptr);
        return ret;
    }
}
if (Symbol.dispose) WasmATPAccount.prototype[Symbol.dispose] = WasmATPAccount.prototype.free;

/**
 * WASM-exposed R7Action — the complete R6/R7 action framework.
 *
 * R7 actions are constructed from a JSON string containing rules, role,
 * request, reference, and resource fields. This keeps the TypeScript API
 * clean while preserving the full Rust type structure.
 */
export class WasmR7Action {
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WasmR7ActionFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wasmr7action_free(ptr, 0);
    }
    /**
     * The unique action ID.
     * @returns {string}
     */
    get actionId() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmr7action_actionId(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Compute the canonical hash for chain integrity.
     * @returns {string}
     */
    canonicalHash() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmr7action_canonicalHash(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Compute reputation delta from a quality score (makes this an R7 action).
     *
     * quality: 0.0 to 1.0. Below 0.5 = negative, above 0.5 = positive.
     * @param {number} quality
     * @param {string} rule_triggered
     * @param {string} reason
     */
    computeReputation(quality, rule_triggered, reason) {
        const ptr0 = passStringToWasm0(rule_triggered, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(reason, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        wasm.wasmr7action_computeReputation(this.__wbg_ptr, quality, ptr0, len0, ptr1, len1);
    }
    /**
     * Whether this is an R7 action (has reputation tracking).
     * @returns {boolean}
     */
    isR7() {
        const ret = wasm.wasmr7action_isR7(this.__wbg_ptr);
        return ret !== 0;
    }
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
     * @param {string} config_json
     */
    constructor(config_json) {
        const ptr0 = passStringToWasm0(config_json, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmr7action_new(ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        this.__wbg_ptr = ret[0] >>> 0;
        WasmR7ActionFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * Current action status as string.
     * @returns {string}
     */
    get status() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmr7action_status(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Convert the full action to a JSON string.
     * @returns {string}
     */
    toJSON() {
        let deferred2_0;
        let deferred2_1;
        try {
            const ret = wasm.wasmr7action_toJSON(this.__wbg_ptr);
            var ptr1 = ret[0];
            var len1 = ret[1];
            if (ret[3]) {
                ptr1 = 0; len1 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred2_0 = ptr1;
            deferred2_1 = len1;
            return getStringFromWasm0(ptr1, len1);
        } finally {
            wasm.__wbindgen_free(deferred2_0, deferred2_1, 1);
        }
    }
    /**
     * Validate the action before execution.
     * Returns a JS array of error strings (empty = valid).
     * @returns {Array<any>}
     */
    validate() {
        const ret = wasm.wasmr7action_validate(this.__wbg_ptr);
        return ret;
    }
}
if (Symbol.dispose) WasmR7Action.prototype[Symbol.dispose] = WasmR7Action.prototype.free;

/**
 * WASM-exposed RoleAssignment — binds a role to its LCT and tracks filling entity.
 */
export class WasmRoleAssignment {
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WasmRoleAssignmentFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wasmroleassignment_free(ptr, 0);
    }
    /**
     * Add an additional holder (committee/federation pattern).
     * @param {string} entity_lct_id
     */
    addHolder(entity_lct_id) {
        const ptr0 = passStringToWasm0(entity_lct_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmroleassignment_addHolder(this.__wbg_ptr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * The filling entity's LCT ID.
     * @returns {string}
     */
    get fillingEntityLctId() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmroleassignment_fillingEntityLctId(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Check if an entity is authorized to act in this role.
     * @param {string} entity_lct_id
     * @returns {boolean}
     */
    isAuthorized(entity_lct_id) {
        const ptr0 = passStringToWasm0(entity_lct_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmroleassignment_isAuthorized(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * Whether this role supports multiple holders.
     * @returns {boolean}
     */
    get multiHolder() {
        const ret = wasm.wasmroleassignment_multiHolder(this.__wbg_ptr);
        return ret !== 0;
    }
    /**
     * Create a new role assignment.
     *
     * Arguments are UUID strings (will be parsed).
     * @param {string} role_name
     * @param {string} role_lct_id
     * @param {string} filling_entity_lct_id
     * @param {string} assigned_by
     */
    constructor(role_name, role_lct_id, filling_entity_lct_id, assigned_by) {
        const ptr0 = passStringToWasm0(role_name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(role_lct_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ptr2 = passStringToWasm0(filling_entity_lct_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len2 = WASM_VECTOR_LEN;
        const ptr3 = passStringToWasm0(assigned_by, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len3 = WASM_VECTOR_LEN;
        const ret = wasm.wasmroleassignment_new(ptr0, len0, ptr1, len1, ptr2, len2, ptr3, len3);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        this.__wbg_ptr = ret[0] >>> 0;
        WasmRoleAssignmentFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * The role's LCT ID.
     * @returns {string}
     */
    get roleLctId() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmroleassignment_roleLctId(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Rotate the filling entity. The role-LCT stays the same.
     * @param {string} new_entity_lct_id
     * @param {string} rotated_by
     */
    rotate(new_entity_lct_id, rotated_by) {
        const ptr0 = passStringToWasm0(new_entity_lct_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(rotated_by, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmroleassignment_rotate(this.__wbg_ptr, ptr0, len0, ptr1, len1);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
}
if (Symbol.dispose) WasmRoleAssignment.prototype[Symbol.dispose] = WasmRoleAssignment.prototype.free;

/**
 * WASM-exposed Society — self-sovereign organizational unit.
 */
export class WasmSociety {
    static __wrap(ptr) {
        ptr = ptr >>> 0;
        const obj = Object.create(WasmSociety.prototype);
        obj.__wbg_ptr = ptr;
        WasmSocietyFinalization.register(obj, obj.__wbg_ptr, obj);
        return obj;
    }
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WasmSocietyFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wasmsociety_free(ptr, 0);
    }
    /**
     * Add a citizen to the society.
     * @param {string} entity_lct_id
     */
    addCitizen(entity_lct_id) {
        const ptr0 = passStringToWasm0(entity_lct_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsociety_addCitizen(this.__wbg_ptr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Assign a role to an entity. Only Sovereign or Administrator can assign.
     * Returns the role's LCT ID.
     * @param {string} role_name
     * @param {string} entity_lct_id
     * @param {string} assigned_by
     * @returns {string}
     */
    assignRole(role_name, entity_lct_id, assigned_by) {
        let deferred5_0;
        let deferred5_1;
        try {
            const ptr0 = passStringToWasm0(role_name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len0 = WASM_VECTOR_LEN;
            const ptr1 = passStringToWasm0(entity_lct_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            const ptr2 = passStringToWasm0(assigned_by, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len2 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsociety_assignRole(this.__wbg_ptr, ptr0, len0, ptr1, len1, ptr2, len2);
            var ptr4 = ret[0];
            var len4 = ret[1];
            if (ret[3]) {
                ptr4 = 0; len4 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred5_0 = ptr4;
            deferred5_1 = len4;
            return getStringFromWasm0(ptr4, len4);
        } finally {
            wasm.__wbindgen_free(deferred5_0, deferred5_1, 1);
        }
    }
    /**
     * Bootstrap a new society. Returns the society with all 7 base-mandatory
     * roles assigned to the founder.
     * @param {string} name
     * @param {string} charter_hash
     * @param {string} founder_lct_id
     * @returns {WasmSociety}
     */
    static bootstrap(name, charter_hash, founder_lct_id) {
        const ptr0 = passStringToWasm0(name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(charter_hash, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ptr2 = passStringToWasm0(founder_lct_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len2 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsociety_bootstrap(ptr0, len0, ptr1, len1, ptr2, len2);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return WasmSociety.__wrap(ret[0]);
    }
    /**
     * Transition to Operational state (all mandatory roles must be filled).
     */
    goOperational() {
        const ret = wasm.wasmsociety_goOperational(this.__wbg_ptr);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Check if an entity holds a specific role.
     * @param {string} entity_lct_id
     * @param {string} role_name
     * @returns {boolean}
     */
    hasRole(entity_lct_id, role_name) {
        const ptr0 = passStringToWasm0(entity_lct_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(role_name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsociety_hasRole(this.__wbg_ptr, ptr0, len0, ptr1, len1);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * Society's LCT ID.
     * @returns {string}
     */
    get lctId() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmsociety_lctId(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Society name.
     * @returns {string}
     */
    get name() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmsociety_name(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Current metabolic state as string.
     * @returns {string}
     */
    get state() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmsociety_state(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Get a JSON summary of the society state.
     * @returns {any}
     */
    summary() {
        const ret = wasm.wasmsociety_summary(this.__wbg_ptr);
        return ret;
    }
    /**
     * Validate minimum viable society requirements.
     * Returns null on success, or a JSON array of error strings on failure.
     * @returns {any}
     */
    validateMinimumViable() {
        const ret = wasm.wasmsociety_validateMinimumViable(this.__wbg_ptr);
        return ret;
    }
}
if (Symbol.dispose) WasmSociety.prototype[Symbol.dispose] = WasmSociety.prototype.free;

/**
 * WASM-exposed SocietyRole enum.
 *
 * Represents one of the 7 base-mandatory roles, 2 context-mandatory roles,
 * or a custom role. Use the static methods to enumerate roles.
 */
export class WasmSocietyRole {
    static __wrap(ptr) {
        ptr = ptr >>> 0;
        const obj = Object.create(WasmSocietyRole.prototype);
        obj.__wbg_ptr = ptr;
        WasmSocietyRoleFinalization.register(obj, obj.__wbg_ptr, obj);
        return obj;
    }
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WasmSocietyRoleFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wasmsocietyrole_free(ptr, 0);
    }
    /**
     * Returns the 7 base-mandatory roles as a JS array of WasmSocietyRole.
     * @returns {Array<any>}
     */
    static baseMandatory() {
        const ret = wasm.wasmsocietyrole_baseMandatory();
        return ret;
    }
    /**
     * Human-readable description of this role's responsibility.
     * @returns {string}
     */
    description() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmsocietyrole_description(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Whether this is a base-mandatory role.
     * @returns {boolean}
     */
    isBaseMandatory() {
        const ret = wasm.wasmsocietyrole_isBaseMandatory(this.__wbg_ptr);
        return ret !== 0;
    }
    /**
     * Role name as string.
     * @returns {string}
     */
    name() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmsocietyrole_name(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Create a role by name. Valid names: sovereign, law_oracle, policy_entity,
     * treasurer, administrator, archivist, citizen, witness, auditor,
     * or "custom:<name>" for custom roles.
     * @param {string} name
     */
    constructor(name) {
        const ptr0 = passStringToWasm0(name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsocietyrole_new(ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        this.__wbg_ptr = ret[0] >>> 0;
        WasmSocietyRoleFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
}
if (Symbol.dispose) WasmSocietyRole.prototype[Symbol.dispose] = WasmSocietyRole.prototype.free;

/**
 * WASM-exposed TrustStore (in-memory only for WASM)
 */
export class WasmTrustStore {
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WasmTrustStoreFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wasmtruststore_free(ptr, 0);
    }
    /**
     * Get entity count
     * @returns {number}
     */
    count() {
        const ret = wasm.wasmtruststore_count(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * Delete entity
     * @param {string} entity_id
     * @returns {boolean}
     */
    delete(entity_id) {
        const ptr0 = passStringToWasm0(entity_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmtruststore_delete(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * Check if entity exists
     * @param {string} entity_id
     * @returns {boolean}
     */
    exists(entity_id) {
        const ptr0 = passStringToWasm0(entity_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmtruststore_exists(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * Get entity trust
     * @param {string} entity_id
     * @returns {EntityTrust}
     */
    get(entity_id) {
        const ptr0 = passStringToWasm0(entity_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmtruststore_get(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return EntityTrust.__wrap(ret[0]);
    }
    /**
     * List entities
     * @returns {Array<any>}
     */
    listEntities() {
        const ret = wasm.wasmtruststore_listEntities(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    constructor() {
        const ret = wasm.wasmtruststore_new();
        this.__wbg_ptr = ret >>> 0;
        WasmTrustStoreFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * Save entity trust
     * @param {EntityTrust} trust
     */
    save(trust) {
        _assertClass(trust, EntityTrust);
        const ret = wasm.wasmtruststore_save(this.__wbg_ptr, trust.__wbg_ptr);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Update entity from outcome
     * @param {string} entity_id
     * @param {boolean} success
     * @param {number} magnitude
     * @returns {EntityTrust}
     */
    update(entity_id, success, magnitude) {
        const ptr0 = passStringToWasm0(entity_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmtruststore_update(this.__wbg_ptr, ptr0, len0, success, magnitude);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return EntityTrust.__wrap(ret[0]);
    }
    /**
     * Witness event
     * @param {string} witness_id
     * @param {string} target_id
     * @param {boolean} success
     * @param {number} magnitude
     * @returns {Array<any>}
     */
    witness(witness_id, target_id, success, magnitude) {
        const ptr0 = passStringToWasm0(witness_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(target_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmtruststore_witness(this.__wbg_ptr, ptr0, len0, ptr1, len1, success, magnitude);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
}
if (Symbol.dispose) WasmTrustStore.prototype[Symbol.dispose] = WasmTrustStore.prototype.free;

/**
 * Initialize the WASM module (called automatically)
 */
export function init() {
    wasm.init();
}

/**
 * Get version string
 * @returns {string}
 */
export function version() {
    let deferred1_0;
    let deferred1_1;
    try {
        const ret = wasm.version();
        deferred1_0 = ret[0];
        deferred1_1 = ret[1];
        return getStringFromWasm0(ret[0], ret[1]);
    } finally {
        wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
    }
}

function __wbg_get_imports() {
    const import0 = {
        __proto__: null,
        __wbg___wbindgen_throw_be289d5034ed271b: function(arg0, arg1) {
            throw new Error(getStringFromWasm0(arg0, arg1));
        },
        __wbg_entitytrust_new: function(arg0) {
            const ret = EntityTrust.__wrap(arg0);
            return ret;
        },
        __wbg_getRandomValues_9b655bdd369112f2: function() { return handleError(function (arg0, arg1) {
            globalThis.crypto.getRandomValues(getArrayU8FromWasm0(arg0, arg1));
        }, arguments); },
        __wbg_getTime_1e3cd1391c5c3995: function(arg0) {
            const ret = arg0.getTime();
            return ret;
        },
        __wbg_new_0_73afc35eb544e539: function() {
            const ret = new Date();
            return ret;
        },
        __wbg_new_361308b2356cecd0: function() {
            const ret = new Object();
            return ret;
        },
        __wbg_new_3eb36ae241fe6f44: function() {
            const ret = new Array();
            return ret;
        },
        __wbg_push_8ffdcb2063340ba5: function(arg0, arg1) {
            const ret = arg0.push(arg1);
            return ret;
        },
        __wbg_set_6cb8631f80447a67: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = Reflect.set(arg0, arg1, arg2);
            return ret;
        }, arguments); },
        __wbg_wasmsocietyrole_new: function(arg0) {
            const ret = WasmSocietyRole.__wrap(arg0);
            return ret;
        },
        __wbindgen_cast_0000000000000001: function(arg0) {
            // Cast intrinsic for `F64 -> Externref`.
            const ret = arg0;
            return ret;
        },
        __wbindgen_cast_0000000000000002: function(arg0, arg1) {
            // Cast intrinsic for `Ref(String) -> Externref`.
            const ret = getStringFromWasm0(arg0, arg1);
            return ret;
        },
        __wbindgen_init_externref_table: function() {
            const table = wasm.__wbindgen_externrefs;
            const offset = table.grow(4);
            table.set(0, undefined);
            table.set(offset + 0, undefined);
            table.set(offset + 1, null);
            table.set(offset + 2, true);
            table.set(offset + 3, false);
        },
    };
    return {
        __proto__: null,
        "./web4_trust_core_bg.js": import0,
    };
}

const EntityTrustFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_entitytrust_free(ptr >>> 0, 1));
const T3TensorFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_t3tensor_free(ptr >>> 0, 1));
const V3TensorFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_v3tensor_free(ptr >>> 0, 1));
const WasmATPAccountFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wasmatpaccount_free(ptr >>> 0, 1));
const WasmR7ActionFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wasmr7action_free(ptr >>> 0, 1));
const WasmRoleAssignmentFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wasmroleassignment_free(ptr >>> 0, 1));
const WasmSocietyFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wasmsociety_free(ptr >>> 0, 1));
const WasmSocietyRoleFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wasmsocietyrole_free(ptr >>> 0, 1));
const WasmTrustStoreFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wasmtruststore_free(ptr >>> 0, 1));

function addToExternrefTable0(obj) {
    const idx = wasm.__externref_table_alloc();
    wasm.__wbindgen_externrefs.set(idx, obj);
    return idx;
}

function _assertClass(instance, klass) {
    if (!(instance instanceof klass)) {
        throw new Error(`expected instance of ${klass.name}`);
    }
}

function getArrayU8FromWasm0(ptr, len) {
    ptr = ptr >>> 0;
    return getUint8ArrayMemory0().subarray(ptr / 1, ptr / 1 + len);
}

function getStringFromWasm0(ptr, len) {
    ptr = ptr >>> 0;
    return decodeText(ptr, len);
}

let cachedUint8ArrayMemory0 = null;
function getUint8ArrayMemory0() {
    if (cachedUint8ArrayMemory0 === null || cachedUint8ArrayMemory0.byteLength === 0) {
        cachedUint8ArrayMemory0 = new Uint8Array(wasm.memory.buffer);
    }
    return cachedUint8ArrayMemory0;
}

function handleError(f, args) {
    try {
        return f.apply(this, args);
    } catch (e) {
        const idx = addToExternrefTable0(e);
        wasm.__wbindgen_exn_store(idx);
    }
}

function passStringToWasm0(arg, malloc, realloc) {
    if (realloc === undefined) {
        const buf = cachedTextEncoder.encode(arg);
        const ptr = malloc(buf.length, 1) >>> 0;
        getUint8ArrayMemory0().subarray(ptr, ptr + buf.length).set(buf);
        WASM_VECTOR_LEN = buf.length;
        return ptr;
    }

    let len = arg.length;
    let ptr = malloc(len, 1) >>> 0;

    const mem = getUint8ArrayMemory0();

    let offset = 0;

    for (; offset < len; offset++) {
        const code = arg.charCodeAt(offset);
        if (code > 0x7F) break;
        mem[ptr + offset] = code;
    }
    if (offset !== len) {
        if (offset !== 0) {
            arg = arg.slice(offset);
        }
        ptr = realloc(ptr, len, len = offset + arg.length * 3, 1) >>> 0;
        const view = getUint8ArrayMemory0().subarray(ptr + offset, ptr + len);
        const ret = cachedTextEncoder.encodeInto(arg, view);

        offset += ret.written;
        ptr = realloc(ptr, len, offset, 1) >>> 0;
    }

    WASM_VECTOR_LEN = offset;
    return ptr;
}

function takeFromExternrefTable0(idx) {
    const value = wasm.__wbindgen_externrefs.get(idx);
    wasm.__externref_table_dealloc(idx);
    return value;
}

let cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
cachedTextDecoder.decode();
const MAX_SAFARI_DECODE_BYTES = 2146435072;
let numBytesDecoded = 0;
function decodeText(ptr, len) {
    numBytesDecoded += len;
    if (numBytesDecoded >= MAX_SAFARI_DECODE_BYTES) {
        cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
        cachedTextDecoder.decode();
        numBytesDecoded = len;
    }
    return cachedTextDecoder.decode(getUint8ArrayMemory0().subarray(ptr, ptr + len));
}

const cachedTextEncoder = new TextEncoder();

if (!('encodeInto' in cachedTextEncoder)) {
    cachedTextEncoder.encodeInto = function (arg, view) {
        const buf = cachedTextEncoder.encode(arg);
        view.set(buf);
        return {
            read: arg.length,
            written: buf.length
        };
    };
}

let WASM_VECTOR_LEN = 0;

let wasmModule, wasm;
function __wbg_finalize_init(instance, module) {
    wasm = instance.exports;
    wasmModule = module;
    cachedUint8ArrayMemory0 = null;
    wasm.__wbindgen_start();
    return wasm;
}

async function __wbg_load(module, imports) {
    if (typeof Response === 'function' && module instanceof Response) {
        if (typeof WebAssembly.instantiateStreaming === 'function') {
            try {
                return await WebAssembly.instantiateStreaming(module, imports);
            } catch (e) {
                const validResponse = module.ok && expectedResponseType(module.type);

                if (validResponse && module.headers.get('Content-Type') !== 'application/wasm') {
                    console.warn("`WebAssembly.instantiateStreaming` failed because your server does not serve Wasm with `application/wasm` MIME type. Falling back to `WebAssembly.instantiate` which is slower. Original error:\n", e);

                } else { throw e; }
            }
        }

        const bytes = await module.arrayBuffer();
        return await WebAssembly.instantiate(bytes, imports);
    } else {
        const instance = await WebAssembly.instantiate(module, imports);

        if (instance instanceof WebAssembly.Instance) {
            return { instance, module };
        } else {
            return instance;
        }
    }

    function expectedResponseType(type) {
        switch (type) {
            case 'basic': case 'cors': case 'default': return true;
        }
        return false;
    }
}

function initSync(module) {
    if (wasm !== undefined) return wasm;


    if (module !== undefined) {
        if (Object.getPrototypeOf(module) === Object.prototype) {
            ({module} = module)
        } else {
            console.warn('using deprecated parameters for `initSync()`; pass a single object instead')
        }
    }

    const imports = __wbg_get_imports();
    if (!(module instanceof WebAssembly.Module)) {
        module = new WebAssembly.Module(module);
    }
    const instance = new WebAssembly.Instance(module, imports);
    return __wbg_finalize_init(instance, module);
}

async function __wbg_init(module_or_path) {
    if (wasm !== undefined) return wasm;


    if (module_or_path !== undefined) {
        if (Object.getPrototypeOf(module_or_path) === Object.prototype) {
            ({module_or_path} = module_or_path)
        } else {
            console.warn('using deprecated parameters for the initialization function; pass a single object instead')
        }
    }

    if (module_or_path === undefined) {
        module_or_path = new URL('web4_trust_core_bg.wasm', import.meta.url);
    }
    const imports = __wbg_get_imports();

    if (typeof module_or_path === 'string' || (typeof Request === 'function' && module_or_path instanceof Request) || (typeof URL === 'function' && module_or_path instanceof URL)) {
        module_or_path = fetch(module_or_path);
    }

    const { instance, module } = await __wbg_load(await module_or_path, imports);

    return __wbg_finalize_init(instance, module);
}

export { initSync, __wbg_init as default };
