/* @ts-self-types="./web4_trust_core.d.ts" */

import * as wasm from "./web4_trust_core_bg.wasm";
import { __wbg_set_wasm } from "./web4_trust_core_bg.js";
__wbg_set_wasm(wasm);
wasm.__wbindgen_start();
export {
    EntityTrust, T3Tensor, V3Tensor, WasmATPAccount, WasmR7Action, WasmRoleAssignment, WasmSociety, WasmSocietyRole, WasmTrustStore, init, version
} from "./web4_trust_core_bg.js";
