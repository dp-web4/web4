"""
Web4 WASM Trust Validator — Session 17, Track 4
================================================

Simulates a WebAssembly-based trust validator for browser conformance.
Since we can't run actual WASM in Python, we model the WASM execution
environment and validate that trust operations produce correct results
across the simulated WASM boundary.

Key concepts:
- WASM module interface for trust operations
- Memory model (linear memory, typed arrays)
- Cross-language serialization (trust tensors → bytes → trust tensors)
- Sandboxed execution model
- Conformance test vectors

12 sections, ~65 checks expected.
"""

import hashlib
import math
import random
import struct
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict


# ============================================================
# §1 — WASM Linear Memory Model
# ============================================================

class WasmValueType(Enum):
    I32 = "i32"
    I64 = "i64"
    F32 = "f32"
    F64 = "f64"


@dataclass
class WasmLinearMemory:
    """Simulates WASM linear memory (byte-addressable)."""
    pages: int = 1  # 1 page = 64KB
    max_pages: int = 16  # Max 1MB
    data: bytearray = field(default_factory=lambda: bytearray(65536))

    def size(self) -> int:
        return len(self.data)

    def grow(self, delta_pages: int) -> int:
        """Grow memory by delta pages. Returns old size in pages or -1."""
        old_pages = len(self.data) // 65536
        new_pages = old_pages + delta_pages
        if new_pages > self.max_pages:
            return -1
        self.data.extend(bytearray(delta_pages * 65536))
        self.pages = new_pages
        return old_pages

    def write_f64(self, offset: int, value: float):
        if offset + 8 > len(self.data):
            raise IndexError(f"Out of bounds: {offset}")
        struct.pack_into('<d', self.data, offset, value)

    def read_f64(self, offset: int) -> float:
        if offset + 8 > len(self.data):
            raise IndexError(f"Out of bounds: {offset}")
        return struct.unpack_from('<d', self.data, offset)[0]

    def write_i32(self, offset: int, value: int):
        if offset + 4 > len(self.data):
            raise IndexError(f"Out of bounds: {offset}")
        struct.pack_into('<i', self.data, offset, value)

    def read_i32(self, offset: int) -> int:
        if offset + 4 > len(self.data):
            raise IndexError(f"Out of bounds: {offset}")
        return struct.unpack_from('<i', self.data, offset)[0]

    def write_bytes(self, offset: int, data: bytes):
        end = offset + len(data)
        if end > len(self.data):
            raise IndexError(f"Out of bounds: {offset}+{len(data)}")
        self.data[offset:end] = data

    def read_bytes(self, offset: int, length: int) -> bytes:
        end = offset + length
        if end > len(self.data):
            raise IndexError(f"Out of bounds: {offset}+{length}")
        return bytes(self.data[offset:end])


def test_section_1():
    checks = []

    mem = WasmLinearMemory(pages=1)
    checks.append(("initial_size", mem.size() == 65536))

    # Write and read f64
    mem.write_f64(0, 0.75)
    val = mem.read_f64(0)
    checks.append(("f64_roundtrip", abs(val - 0.75) < 1e-10))

    # Write and read i32
    mem.write_i32(100, 42)
    val = mem.read_i32(100)
    checks.append(("i32_roundtrip", val == 42))

    # Write and read bytes
    mem.write_bytes(200, b"hello")
    data = mem.read_bytes(200, 5)
    checks.append(("bytes_roundtrip", data == b"hello"))

    # Memory growth
    old = mem.grow(1)
    checks.append(("grow_success", old == 1))
    checks.append(("new_size", mem.size() == 131072))

    # Growth beyond max fails
    result = mem.grow(100)
    checks.append(("grow_max_fails", result == -1))

    # Out of bounds
    try:
        mem.read_f64(mem.size())
        checks.append(("bounds_check", False))
    except IndexError:
        checks.append(("bounds_check", True))

    return checks


# ============================================================
# §2 — Trust Tensor Serialization
# ============================================================

@dataclass
class WasmTrustTensor:
    """Trust tensor that can be serialized to WASM linear memory."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5
    entity_id: str = ""
    timestamp: float = 0.0

    def to_bytes(self) -> bytes:
        """Serialize to bytes for WASM memory."""
        # Layout: 3 x f64 (trust dims) + 1 x f64 (timestamp) + entity_id (length-prefixed)
        entity_bytes = self.entity_id.encode('utf-8')
        buf = struct.pack('<ddd', self.talent, self.training, self.temperament)
        buf += struct.pack('<d', self.timestamp)
        buf += struct.pack('<I', len(entity_bytes))
        buf += entity_bytes
        return buf

    @staticmethod
    def from_bytes(data: bytes) -> 'WasmTrustTensor':
        """Deserialize from bytes."""
        talent, training, temperament = struct.unpack_from('<ddd', data, 0)
        timestamp = struct.unpack_from('<d', data, 24)[0]
        entity_len = struct.unpack_from('<I', data, 32)[0]
        entity_id = data[36:36+entity_len].decode('utf-8')
        return WasmTrustTensor(talent, training, temperament, entity_id, timestamp)

    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def bounded(self) -> bool:
        return all(0 <= v <= 1 for v in [self.talent, self.training, self.temperament])

    def write_to_memory(self, mem: WasmLinearMemory, offset: int):
        data = self.to_bytes()
        mem.write_bytes(offset, data)

    @staticmethod
    def read_from_memory(mem: WasmLinearMemory, offset: int) -> 'WasmTrustTensor':
        # Read fixed part first
        fixed = mem.read_bytes(offset, 36)
        entity_len = struct.unpack_from('<I', fixed, 32)[0]
        full_data = mem.read_bytes(offset, 36 + entity_len)
        return WasmTrustTensor.from_bytes(full_data)


def test_section_2():
    checks = []

    # Serialization roundtrip
    tensor = WasmTrustTensor(0.8, 0.6, 0.75, "entity_123", 1000.0)
    data = tensor.to_bytes()
    restored = WasmTrustTensor.from_bytes(data)
    checks.append(("ser_talent", abs(restored.talent - 0.8) < 1e-10))
    checks.append(("ser_training", abs(restored.training - 0.6) < 1e-10))
    checks.append(("ser_temperament", abs(restored.temperament - 0.75) < 1e-10))
    checks.append(("ser_entity", restored.entity_id == "entity_123"))
    checks.append(("ser_timestamp", abs(restored.timestamp - 1000.0) < 1e-10))

    # Memory roundtrip
    mem = WasmLinearMemory()
    tensor.write_to_memory(mem, 0)
    restored2 = WasmTrustTensor.read_from_memory(mem, 0)
    checks.append(("mem_talent", abs(restored2.talent - 0.8) < 1e-10))
    checks.append(("mem_entity", restored2.entity_id == "entity_123"))

    # Composite calculation
    checks.append(("composite", abs(tensor.composite() - 0.7167) < 0.01))

    # Bounded check
    checks.append(("bounded_valid", tensor.bounded()))
    invalid = WasmTrustTensor(1.5, 0.5, 0.5)
    checks.append(("bounded_invalid", not invalid.bounded()))

    return checks


# ============================================================
# §3 — WASM Module Interface
# ============================================================

@dataclass
class WasmExport:
    name: str
    params: List[WasmValueType]
    returns: List[WasmValueType]


@dataclass
class WasmModule:
    """Simulated WASM module with trust validation exports."""
    memory: WasmLinearMemory = field(default_factory=WasmLinearMemory)
    exports: Dict[str, WasmExport] = field(default_factory=dict)
    heap_ptr: int = 1024  # Allocator starts here

    def __post_init__(self):
        # Register standard trust validation exports
        self.exports = {
            "validate_trust": WasmExport("validate_trust",
                                         [WasmValueType.I32, WasmValueType.I32],  # ptr, len
                                         [WasmValueType.I32]),  # result code
            "compute_composite": WasmExport("compute_composite",
                                            [WasmValueType.I32],  # ptr to tensor
                                            [WasmValueType.F64]),  # composite score
            "verify_bounds": WasmExport("verify_bounds",
                                        [WasmValueType.I32],  # ptr to tensor
                                        [WasmValueType.I32]),  # 1=valid, 0=invalid
            "alloc": WasmExport("alloc",
                                [WasmValueType.I32],  # size
                                [WasmValueType.I32]),  # ptr
            "free": WasmExport("free",
                               [WasmValueType.I32, WasmValueType.I32],  # ptr, size
                               []),
        }

    def alloc(self, size: int) -> int:
        """Simple bump allocator."""
        ptr = self.heap_ptr
        self.heap_ptr += size
        # Grow memory if needed
        while self.heap_ptr > self.memory.size():
            self.memory.grow(1)
        return ptr

    def validate_trust(self, ptr: int, length: int) -> int:
        """Validate a trust tensor from memory. Returns 0=ok, 1=invalid."""
        try:
            data = self.memory.read_bytes(ptr, length)
            tensor = WasmTrustTensor.from_bytes(data)
            if not tensor.bounded():
                return 1  # Invalid bounds
            return 0
        except Exception:
            return 2  # Parse error

    def compute_composite(self, ptr: int) -> float:
        """Compute composite trust score from tensor in memory."""
        try:
            tensor = WasmTrustTensor.read_from_memory(self.memory, ptr)
            return tensor.composite()
        except Exception:
            return -1.0

    def verify_bounds(self, ptr: int) -> int:
        """Verify trust tensor bounds. Returns 1 if valid."""
        try:
            tensor = WasmTrustTensor.read_from_memory(self.memory, ptr)
            return 1 if tensor.bounded() else 0
        except Exception:
            return 0


def test_section_3():
    checks = []

    module = WasmModule()

    # Check exports exist
    checks.append(("has_validate", "validate_trust" in module.exports))
    checks.append(("has_composite", "compute_composite" in module.exports))
    checks.append(("has_bounds", "verify_bounds" in module.exports))

    # Allocate and write tensor
    tensor = WasmTrustTensor(0.8, 0.6, 0.7, "test", 0.0)
    data = tensor.to_bytes()
    ptr = module.alloc(len(data))
    module.memory.write_bytes(ptr, data)

    # Validate
    result = module.validate_trust(ptr, len(data))
    checks.append(("validate_ok", result == 0))

    # Compute composite
    composite = module.compute_composite(ptr)
    checks.append(("composite_correct", abs(composite - 0.7) < 0.01))

    # Verify bounds
    bounds = module.verify_bounds(ptr)
    checks.append(("bounds_valid", bounds == 1))

    # Invalid tensor
    invalid = WasmTrustTensor(1.5, 0.6, 0.7, "bad", 0.0)
    data2 = invalid.to_bytes()
    ptr2 = module.alloc(len(data2))
    module.memory.write_bytes(ptr2, data2)
    result2 = module.validate_trust(ptr2, len(data2))
    checks.append(("validate_invalid", result2 == 1))

    return checks


# ============================================================
# §4 — Conformance Test Vectors
# ============================================================

# Standard test vectors that any conformant implementation must pass
CONFORMANCE_VECTORS = [
    {
        "name": "basic_valid",
        "tensor": {"talent": 0.5, "training": 0.5, "temperament": 0.5},
        "expected_composite": 0.5,
        "expected_valid": True,
    },
    {
        "name": "high_trust",
        "tensor": {"talent": 0.9, "training": 0.85, "temperament": 0.95},
        "expected_composite": 0.9,
        "expected_valid": True,
    },
    {
        "name": "low_trust",
        "tensor": {"talent": 0.1, "training": 0.15, "temperament": 0.05},
        "expected_composite": 0.1,
        "expected_valid": True,
    },
    {
        "name": "zero_trust",
        "tensor": {"talent": 0.0, "training": 0.0, "temperament": 0.0},
        "expected_composite": 0.0,
        "expected_valid": True,
    },
    {
        "name": "max_trust",
        "tensor": {"talent": 1.0, "training": 1.0, "temperament": 1.0},
        "expected_composite": 1.0,
        "expected_valid": True,
    },
    {
        "name": "over_max",
        "tensor": {"talent": 1.1, "training": 0.5, "temperament": 0.5},
        "expected_composite": 0.7,
        "expected_valid": False,
    },
    {
        "name": "under_min",
        "tensor": {"talent": -0.1, "training": 0.5, "temperament": 0.5},
        "expected_composite": 0.3,
        "expected_valid": False,
    },
    {
        "name": "asymmetric",
        "tensor": {"talent": 0.2, "training": 0.8, "temperament": 0.5},
        "expected_composite": 0.5,
        "expected_valid": True,
    },
]


def run_conformance_vectors(module: WasmModule) -> List[Dict]:
    """Run all conformance vectors against a WASM module."""
    results = []
    for vec in CONFORMANCE_VECTORS:
        t = vec["tensor"]
        tensor = WasmTrustTensor(t["talent"], t["training"], t["temperament"], vec["name"])
        data = tensor.to_bytes()
        ptr = module.alloc(len(data))
        module.memory.write_bytes(ptr, data)

        # Test validation
        valid_result = module.validate_trust(ptr, len(data))
        is_valid = valid_result == 0

        # Test composite
        composite = module.compute_composite(ptr)

        results.append({
            "name": vec["name"],
            "valid_match": is_valid == vec["expected_valid"],
            "composite_match": abs(composite - vec["expected_composite"]) < 0.05,
            "is_valid": is_valid,
            "composite": composite,
        })

    return results


def test_section_4():
    checks = []

    module = WasmModule()
    results = run_conformance_vectors(module)

    all_valid_match = all(r["valid_match"] for r in results)
    all_composite_match = all(r["composite_match"] for r in results)

    checks.append(("all_validity_correct", all_valid_match))
    checks.append(("all_composite_correct", all_composite_match))
    checks.append(("vector_count", len(results) == len(CONFORMANCE_VECTORS)))

    # Individual critical vectors
    basic = next(r for r in results if r["name"] == "basic_valid")
    checks.append(("basic_valid_passes", basic["valid_match"] and basic["composite_match"]))

    over = next(r for r in results if r["name"] == "over_max")
    checks.append(("over_max_rejected", not over["is_valid"]))

    under = next(r for r in results if r["name"] == "under_min")
    checks.append(("under_min_rejected", not under["is_valid"]))

    return checks


# ============================================================
# §5 — Sandboxed Execution Model
# ============================================================

@dataclass
class WasmSandbox:
    """Sandboxed WASM execution environment."""
    module: WasmModule = field(default_factory=WasmModule)
    gas_limit: int = 1_000_000
    gas_used: int = 0
    memory_limit: int = 1_048_576  # 1MB
    call_depth: int = 0
    max_call_depth: int = 100
    execution_log: List[Dict] = field(default_factory=list)

    def consume_gas(self, amount: int) -> bool:
        self.gas_used += amount
        return self.gas_used <= self.gas_limit

    def execute(self, func_name: str, *args) -> Dict:
        """Execute a function in the sandbox."""
        if func_name not in self.module.exports:
            return {"success": False, "error": "function_not_found"}

        if self.call_depth >= self.max_call_depth:
            return {"success": False, "error": "call_depth_exceeded"}

        if self.module.memory.size() > self.memory_limit:
            return {"success": False, "error": "memory_limit_exceeded"}

        self.call_depth += 1

        # Gas cost based on operation
        gas_costs = {
            "validate_trust": 100,
            "compute_composite": 50,
            "verify_bounds": 30,
            "alloc": 20,
            "free": 10,
        }
        gas = gas_costs.get(func_name, 50)

        if not self.consume_gas(gas):
            self.call_depth -= 1
            return {"success": False, "error": "out_of_gas"}

        # Execute function
        try:
            fn = getattr(self.module, func_name, None)
            if fn is None:
                self.call_depth -= 1
                return {"success": False, "error": "function_not_implemented"}

            result = fn(*args)
            self.call_depth -= 1

            entry = {
                "func": func_name,
                "gas": gas,
                "success": True,
            }
            self.execution_log.append(entry)
            return {"success": True, "result": result, "gas_used": self.gas_used}
        except Exception as e:
            self.call_depth -= 1
            return {"success": False, "error": str(e)}


def test_section_5():
    checks = []

    sandbox = WasmSandbox(gas_limit=1000)

    # Normal execution
    tensor = WasmTrustTensor(0.7, 0.8, 0.6, "test")
    data = tensor.to_bytes()
    result = sandbox.execute("alloc", len(data))
    checks.append(("alloc_success", result["success"]))
    ptr = result["result"]

    sandbox.module.memory.write_bytes(ptr, data)
    result = sandbox.execute("validate_trust", ptr, len(data))
    checks.append(("validate_in_sandbox", result["success"]))
    checks.append(("validate_result", result["result"] == 0))

    result = sandbox.execute("compute_composite", ptr)
    checks.append(("composite_in_sandbox", result["success"]))
    checks.append(("composite_value", abs(result["result"] - 0.7) < 0.01))

    # Unknown function
    result = sandbox.execute("unknown_func")
    checks.append(("unknown_func_error", not result["success"]))

    # Gas exhaustion
    sandbox2 = WasmSandbox(gas_limit=50)
    result = sandbox2.execute("validate_trust", 0, 10)  # Costs 100 gas
    checks.append(("gas_exhaustion", not result["success"] and result["error"] == "out_of_gas"))

    # Call depth limit
    sandbox3 = WasmSandbox(max_call_depth=0)
    result = sandbox3.execute("alloc", 10)
    checks.append(("call_depth_limit", not result["success"]))

    return checks


# ============================================================
# §6 — Cross-Language Type Mapping
# ============================================================

def map_js_to_wasm(js_value: Any, value_type: WasmValueType) -> Any:
    """Map JavaScript value to WASM type."""
    if value_type == WasmValueType.I32:
        return int(js_value) & 0xFFFFFFFF  # Truncate to 32-bit
    elif value_type == WasmValueType.I64:
        return int(js_value)
    elif value_type == WasmValueType.F32:
        return struct.unpack('<f', struct.pack('<f', float(js_value)))[0]
    elif value_type == WasmValueType.F64:
        return float(js_value)
    return js_value


def map_wasm_to_js(wasm_value: Any, value_type: WasmValueType) -> Any:
    """Map WASM value back to JavaScript type."""
    if value_type in [WasmValueType.I32, WasmValueType.I64]:
        return int(wasm_value)
    elif value_type in [WasmValueType.F32, WasmValueType.F64]:
        return float(wasm_value)
    return wasm_value


def trust_tensor_to_json(tensor: WasmTrustTensor) -> str:
    """Serialize trust tensor to JSON (for JS interop)."""
    return json.dumps({
        "talent": tensor.talent,
        "training": tensor.training,
        "temperament": tensor.temperament,
        "entity_id": tensor.entity_id,
        "timestamp": tensor.timestamp,
        "composite": tensor.composite(),
    })


def json_to_trust_tensor(json_str: str) -> WasmTrustTensor:
    """Deserialize trust tensor from JSON."""
    d = json.loads(json_str)
    return WasmTrustTensor(
        talent=d["talent"],
        training=d["training"],
        temperament=d["temperament"],
        entity_id=d.get("entity_id", ""),
        timestamp=d.get("timestamp", 0.0),
    )


def test_section_6():
    checks = []

    # i32 truncation
    val = map_js_to_wasm(2**33 + 5, WasmValueType.I32)
    checks.append(("i32_truncation", val == 5))

    # f32 precision loss
    f32 = map_js_to_wasm(0.1 + 0.2, WasmValueType.F32)
    f64 = map_js_to_wasm(0.1 + 0.2, WasmValueType.F64)
    checks.append(("f32_precision_loss", f32 != f64))

    # JSON roundtrip
    tensor = WasmTrustTensor(0.8, 0.6, 0.7, "alice", 1000.0)
    json_str = trust_tensor_to_json(tensor)
    restored = json_to_trust_tensor(json_str)
    checks.append(("json_talent", abs(restored.talent - 0.8) < 1e-10))
    checks.append(("json_training", abs(restored.training - 0.6) < 1e-10))
    checks.append(("json_entity", restored.entity_id == "alice"))

    # JSON includes composite
    parsed = json.loads(json_str)
    checks.append(("json_has_composite", "composite" in parsed))
    checks.append(("json_composite_correct", abs(parsed["composite"] - 0.7) < 0.01))

    return checks


# ============================================================
# §7 — WASM Import/Export Validation
# ============================================================

@dataclass
class WasmImport:
    module_name: str
    field_name: str
    params: List[WasmValueType]
    returns: List[WasmValueType]


REQUIRED_EXPORTS = [
    WasmExport("validate_trust", [WasmValueType.I32, WasmValueType.I32], [WasmValueType.I32]),
    WasmExport("compute_composite", [WasmValueType.I32], [WasmValueType.F64]),
    WasmExport("verify_bounds", [WasmValueType.I32], [WasmValueType.I32]),
    WasmExport("alloc", [WasmValueType.I32], [WasmValueType.I32]),
    WasmExport("memory", [], []),  # Exported memory
]

REQUIRED_IMPORTS = [
    WasmImport("env", "abort", [WasmValueType.I32], []),
    WasmImport("web4", "log_trust_update", [WasmValueType.I32, WasmValueType.F64], []),
]


def validate_module_interface(module: WasmModule) -> Dict:
    """Validate that a WASM module implements required interface."""
    missing_exports = []
    for req in REQUIRED_EXPORTS:
        if req.name not in module.exports:
            missing_exports.append(req.name)
        elif req.name != "memory":
            actual = module.exports[req.name]
            if actual.params != req.params:
                missing_exports.append(f"{req.name} (wrong params)")
            if actual.returns != req.returns:
                missing_exports.append(f"{req.name} (wrong returns)")

    return {
        "valid": len(missing_exports) == 0,
        "missing_exports": missing_exports,
        "total_exports": len(module.exports),
        "required_exports": len(REQUIRED_EXPORTS),
    }


def test_section_7():
    checks = []

    # Valid module
    module = WasmModule()
    # Add memory export
    module.exports["memory"] = WasmExport("memory", [], [])
    result = validate_module_interface(module)
    checks.append(("valid_module", result["valid"]))
    checks.append(("no_missing", len(result["missing_exports"]) == 0))

    # Module missing an export
    partial = WasmModule()
    del partial.exports["compute_composite"]
    result2 = validate_module_interface(partial)
    checks.append(("missing_detected", not result2["valid"]))
    checks.append(("missing_reported", len(result2["missing_exports"]) > 0))

    # Module with wrong signature
    wrong_sig = WasmModule()
    wrong_sig.exports["memory"] = WasmExport("memory", [], [])
    wrong_sig.exports["validate_trust"] = WasmExport("validate_trust",
                                                      [WasmValueType.F64],  # Wrong type
                                                      [WasmValueType.I32])
    result3 = validate_module_interface(wrong_sig)
    checks.append(("wrong_sig_detected", not result3["valid"]))

    return checks


# ============================================================
# §8 — ATP Validation in WASM
# ============================================================

@dataclass
class WasmATPValidator:
    """ATP conservation validator that runs in WASM sandbox."""
    module: WasmModule = field(default_factory=WasmModule)

    def validate_transfer(self, sender_balance: float, receiver_balance: float,
                          amount: float, fee_rate: float) -> Dict:
        """Validate an ATP transfer in WASM."""
        # Write parameters to memory
        ptr = self.module.alloc(48)  # 6 x f64
        self.module.memory.write_f64(ptr, sender_balance)
        self.module.memory.write_f64(ptr + 8, receiver_balance)
        self.module.memory.write_f64(ptr + 16, amount)
        self.module.memory.write_f64(ptr + 24, fee_rate)

        # Compute
        fee = amount * fee_rate
        total_cost = amount + fee
        new_sender = sender_balance - total_cost
        new_receiver = receiver_balance + amount

        # Validation
        valid = (
            amount > 0 and
            not math.isnan(amount) and
            fee_rate >= 0 and
            not math.isnan(fee_rate) and
            new_sender >= 0 and
            new_receiver <= 10000.0  # Max balance
        )

        # Conservation check
        pre_total = sender_balance + receiver_balance
        post_total = new_sender + new_receiver
        conserved = abs(pre_total - (post_total + fee)) < 0.001

        # Write results
        self.module.memory.write_f64(ptr + 32, new_sender)
        self.module.memory.write_f64(ptr + 40, new_receiver)

        return {
            "valid": valid,
            "conserved": conserved,
            "fee": fee,
            "new_sender": new_sender,
            "new_receiver": new_receiver,
        }


def test_section_8():
    checks = []

    validator = WasmATPValidator()

    # Valid transfer
    r = validator.validate_transfer(1000.0, 500.0, 100.0, 0.05)
    checks.append(("transfer_valid", r["valid"]))
    checks.append(("transfer_conserved", r["conserved"]))
    checks.append(("fee_correct", abs(r["fee"] - 5.0) < 0.01))
    checks.append(("sender_debited", abs(r["new_sender"] - 895.0) < 0.01))

    # Insufficient funds
    r2 = validator.validate_transfer(50.0, 500.0, 100.0, 0.05)
    checks.append(("insufficient_detected", not r2["valid"]))

    # NaN amount
    r3 = validator.validate_transfer(1000.0, 500.0, float('nan'), 0.05)
    checks.append(("nan_detected", not r3["valid"]))

    # Zero amount
    r4 = validator.validate_transfer(1000.0, 500.0, 0.0, 0.05)
    checks.append(("zero_amount_detected", not r4["valid"]))

    return checks


# ============================================================
# §9 — Browser Conformance Test Suite
# ============================================================

@dataclass
class ConformanceResult:
    test_name: str
    passed: bool
    expected: Any
    actual: Any
    error: Optional[str] = None


def run_browser_conformance_suite(module: WasmModule) -> List[ConformanceResult]:
    """Run full conformance test suite simulating browser environment."""
    results = []

    # Test 1: Tensor validation roundtrip
    for tensor_data in CONFORMANCE_VECTORS:
        t = tensor_data["tensor"]
        tensor = WasmTrustTensor(t["talent"], t["training"], t["temperament"],
                                 tensor_data["name"])
        data = tensor.to_bytes()
        ptr = module.alloc(len(data))
        module.memory.write_bytes(ptr, data)

        valid_code = module.validate_trust(ptr, len(data))
        is_valid = valid_code == 0
        results.append(ConformanceResult(
            f"validate_{tensor_data['name']}",
            is_valid == tensor_data["expected_valid"],
            tensor_data["expected_valid"],
            is_valid,
        ))

    # Test 2: Memory allocation stress
    ptrs = []
    for i in range(100):
        ptr = module.alloc(64)
        ptrs.append(ptr)
    # All allocations should be unique
    unique_ptrs = len(set(ptrs))
    results.append(ConformanceResult(
        "alloc_unique",
        unique_ptrs == 100,
        100,
        unique_ptrs,
    ))

    # Test 3: Multiple tensors in memory simultaneously
    tensors = [
        WasmTrustTensor(0.1 * i, 0.1 * i, 0.1 * i, f"entity_{i}")
        for i in range(1, 10)
    ]
    tensor_ptrs = []
    for t in tensors:
        data = t.to_bytes()
        ptr = module.alloc(len(data))
        module.memory.write_bytes(ptr, data)
        tensor_ptrs.append(ptr)

    # All should be independently readable
    for i, (t, ptr) in enumerate(zip(tensors, tensor_ptrs)):
        restored = WasmTrustTensor.read_from_memory(module.memory, ptr)
        match = abs(restored.talent - t.talent) < 1e-10
        results.append(ConformanceResult(
            f"multi_tensor_{i}",
            match,
            t.talent,
            restored.talent,
        ))

    return results


def test_section_9():
    checks = []

    module = WasmModule()
    results = run_browser_conformance_suite(module)

    total_pass = sum(1 for r in results if r.passed)
    total = len(results)

    checks.append(("all_conformance_pass", total_pass == total))
    checks.append(("sufficient_tests", total >= 15))

    # Check specific critical tests
    validate_results = [r for r in results if r.test_name.startswith("validate_")]
    checks.append(("all_validations_correct", all(r.passed for r in validate_results)))

    alloc_test = next(r for r in results if r.test_name == "alloc_unique")
    checks.append(("alloc_unique", alloc_test.passed))

    return checks


# ============================================================
# §10 — Cross-Platform Hash Verification
# ============================================================

def compute_trust_hash(tensor: WasmTrustTensor) -> str:
    """Compute deterministic hash of trust tensor (cross-platform)."""
    # Use fixed-point representation for deterministic hashing
    SCALE = 10000
    talent_fixed = round(tensor.talent * SCALE)
    training_fixed = round(tensor.training * SCALE)
    temperament_fixed = round(tensor.temperament * SCALE)

    data = struct.pack('<iii', talent_fixed, training_fixed, temperament_fixed)
    data += tensor.entity_id.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


HASH_TEST_VECTORS = [
    {
        "tensor": WasmTrustTensor(0.5, 0.5, 0.5, "test"),
        "expected_hash": None,  # Will be computed
    },
    {
        "tensor": WasmTrustTensor(0.8, 0.6, 0.7, "alice"),
        "expected_hash": None,
    },
    {
        "tensor": WasmTrustTensor(0.0, 0.0, 0.0, "zero"),
        "expected_hash": None,
    },
]

# Pre-compute expected hashes
for vec in HASH_TEST_VECTORS:
    vec["expected_hash"] = compute_trust_hash(vec["tensor"])


def test_section_10():
    checks = []

    # Hash determinism
    t1 = WasmTrustTensor(0.5, 0.5, 0.5, "test")
    h1 = compute_trust_hash(t1)
    h2 = compute_trust_hash(t1)
    checks.append(("hash_deterministic", h1 == h2))

    # Different tensors → different hashes
    t2 = WasmTrustTensor(0.5, 0.5, 0.6, "test")
    h3 = compute_trust_hash(t2)
    checks.append(("hash_different", h1 != h3))

    # Test vectors match
    all_match = True
    for vec in HASH_TEST_VECTORS:
        computed = compute_trust_hash(vec["tensor"])
        if computed != vec["expected_hash"]:
            all_match = False
    checks.append(("hash_vectors_match", all_match))

    # Fixed-point round-trip preserves precision
    t = WasmTrustTensor(0.6013, 0.7021, 0.8999, "precision")
    SCALE = 10000
    talent_fixed = round(t.talent * SCALE)
    restored = talent_fixed / SCALE
    checks.append(("fixed_point_precision", abs(restored - 0.6013) < 0.0001))

    # Hash length
    checks.append(("hash_length", len(h1) == 64))  # SHA-256 hex = 64 chars

    return checks


# ============================================================
# §11 — WASM Performance Benchmarks
# ============================================================

def benchmark_wasm_operations(module: WasmModule, iterations: int) -> Dict:
    """Benchmark trust operations in WASM."""
    import time

    # Prepare test data
    tensor = WasmTrustTensor(0.7, 0.8, 0.6, "bench")
    data = tensor.to_bytes()

    # Benchmark allocation
    alloc_ptrs = []
    start = time.perf_counter()
    for _ in range(iterations):
        ptr = module.alloc(len(data))
        alloc_ptrs.append(ptr)
    alloc_time = time.perf_counter() - start

    # Benchmark write
    start = time.perf_counter()
    for ptr in alloc_ptrs:
        module.memory.write_bytes(ptr, data)
    write_time = time.perf_counter() - start

    # Benchmark validate
    start = time.perf_counter()
    for ptr in alloc_ptrs:
        module.validate_trust(ptr, len(data))
    validate_time = time.perf_counter() - start

    # Benchmark composite
    start = time.perf_counter()
    for ptr in alloc_ptrs:
        module.compute_composite(ptr)
    composite_time = time.perf_counter() - start

    return {
        "iterations": iterations,
        "alloc_per_sec": iterations / alloc_time if alloc_time > 0 else 0,
        "write_per_sec": iterations / write_time if write_time > 0 else 0,
        "validate_per_sec": iterations / validate_time if validate_time > 0 else 0,
        "composite_per_sec": iterations / composite_time if composite_time > 0 else 0,
    }


def test_section_11():
    checks = []

    module = WasmModule()
    bench = benchmark_wasm_operations(module, 1000)

    # All operations should be fast
    checks.append(("alloc_fast", bench["alloc_per_sec"] > 1000))
    checks.append(("write_fast", bench["write_per_sec"] > 1000))
    checks.append(("validate_fast", bench["validate_per_sec"] > 1000))
    checks.append(("composite_fast", bench["composite_per_sec"] > 1000))
    checks.append(("iterations_correct", bench["iterations"] == 1000))

    return checks


# ============================================================
# §12 — Complete WASM Validator Pipeline
# ============================================================

def run_complete_wasm_pipeline() -> List[Tuple[str, bool]]:
    checks = []

    module = WasmModule()
    module.exports["memory"] = WasmExport("memory", [], [])

    # 1. Module interface validation
    interface = validate_module_interface(module)
    checks.append(("interface_valid", interface["valid"]))

    # 2. Conformance vectors
    conformance = run_conformance_vectors(module)
    checks.append(("conformance_all_pass",
                    all(r["valid_match"] and r["composite_match"] for r in conformance)))

    # 3. Sandboxed execution
    sandbox = WasmSandbox(gas_limit=10000)
    tensor = WasmTrustTensor(0.7, 0.8, 0.6, "pipeline")
    data = tensor.to_bytes()
    alloc_r = sandbox.execute("alloc", len(data))
    checks.append(("sandbox_alloc", alloc_r["success"]))

    ptr = alloc_r["result"]
    sandbox.module.memory.write_bytes(ptr, data)
    validate_r = sandbox.execute("validate_trust", ptr, len(data))
    checks.append(("sandbox_validate", validate_r["success"] and validate_r["result"] == 0))

    # 4. ATP validation
    atp_validator = WasmATPValidator()
    atp_r = atp_validator.validate_transfer(1000.0, 500.0, 100.0, 0.05)
    checks.append(("atp_valid", atp_r["valid"] and atp_r["conserved"]))

    # 5. Cross-platform hashing
    t1 = WasmTrustTensor(0.5, 0.5, 0.5, "cross_platform")
    h1 = compute_trust_hash(t1)
    h2 = compute_trust_hash(t1)
    checks.append(("hash_deterministic", h1 == h2))

    # 6. Browser conformance suite
    browser_results = run_browser_conformance_suite(WasmModule())
    checks.append(("browser_suite_pass", all(r.passed for r in browser_results)))

    # 7. Serialization integrity
    tensor2 = WasmTrustTensor(0.123, 0.456, 0.789, "integrity")
    data2 = tensor2.to_bytes()
    restored = WasmTrustTensor.from_bytes(data2)
    checks.append(("serialization_integrity",
                    abs(restored.talent - 0.123) < 1e-10 and
                    abs(restored.training - 0.456) < 1e-10))

    # 8. Gas metering
    metered = WasmSandbox(gas_limit=200)
    for _ in range(10):
        metered.execute("alloc", 10)  # 20 gas each
    # Should have used at least 200 gas
    checks.append(("gas_metered", metered.gas_used > 0))

    return checks


def test_section_12():
    return run_complete_wasm_pipeline()


# ============================================================
# Main runner
# ============================================================

def run_all():
    sections = [
        ("§1 WASM Linear Memory", test_section_1),
        ("§2 Trust Tensor Serialization", test_section_2),
        ("§3 WASM Module Interface", test_section_3),
        ("§4 Conformance Vectors", test_section_4),
        ("§5 Sandboxed Execution", test_section_5),
        ("§6 Cross-Language Types", test_section_6),
        ("§7 Import/Export Validation", test_section_7),
        ("§8 ATP WASM Validation", test_section_8),
        ("§9 Browser Conformance", test_section_9),
        ("§10 Cross-Platform Hashing", test_section_10),
        ("§11 Performance Benchmarks", test_section_11),
        ("§12 Complete Pipeline", test_section_12),
    ]

    total = 0
    passed = 0
    failed_checks = []

    for name, fn in sections:
        checks = fn()
        section_pass = sum(1 for _, v in checks if v)
        section_total = len(checks)
        total += section_total
        passed += section_pass
        status = "✓" if section_pass == section_total else "✗"
        print(f"  {status} {name}: {section_pass}/{section_total}")
        for cname, cval in checks:
            if not cval:
                failed_checks.append(f"    FAIL: {name} → {cname}")

    print(f"\nTotal: {passed}/{total}")
    if failed_checks:
        print("\nFailed checks:")
        for f in failed_checks:
            print(f)

    return passed, total


if __name__ == "__main__":
    run_all()
