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
