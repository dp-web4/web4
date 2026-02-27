#!/usr/bin/env python3
"""
Cross-language test vector validator for Web4.

Loads test vectors from JSON files and validates them against
pure-Python reference calculations. Any language implementation
that passes these vectors is interoperable.

Usage:
    python validate_vectors.py          # Run all vector suites
    python validate_vectors.py t3v3     # Run only T3V3 vectors
    python validate_vectors.py atp      # Run only ATP vectors
"""

import json
import math
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

passed = 0
failed = 0
errors = []


def check(condition, msg):
    global passed, failed, errors
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(msg)
        print(f"  FAIL: {msg}")


def approx(a, b, tol=0.0001):
    return abs(a - b) <= tol


# ── T3V3 Tensor Operations ──────────────────────────────────────────

def t3_composite(talent, training, temperament):
    """T3 composite: talent*0.4 + training*0.3 + temperament*0.3"""
    return talent * 0.4 + training * 0.3 + temperament * 0.3


def v3_composite(valuation, veracity, validity):
    """V3 composite: valuation*0.3 + veracity*0.35 + validity*0.35"""
    return valuation * 0.3 + veracity * 0.35 + validity * 0.35


def t3_update(initial, success, quality):
    """T3 update: delta = 0.02 * (quality - 0.5), dimension factors applied"""
    base_delta = 0.02 * (quality - 0.5)
    factors = {"talent": 1.0, "training": 0.8, "temperament": 0.6}
    result = {}
    for dim, factor in factors.items():
        delta = base_delta * factor
        new_val = max(0.0, min(1.0, initial[dim] + delta))
        result[dim] = new_val
    return result, base_delta, factors


def diminishing_returns(repeat_count, base_factor):
    """Diminishing returns: base^(n-1) for each repeat"""
    return [base_factor ** i for i in range(repeat_count)]


def trust_bridge(six_dim):
    """6-dim to 3-dim trust mapping"""
    primary_weight = 0.6
    secondary_weight = 1.0 / 3.0 * (1.0 - primary_weight)  # ~0.1333

    mapping = {
        "talent": ("competence", ["alignment", "witnesses", "lineage"]),
        "training": ("reliability", ["alignment", "witnesses", "lineage"]),
        "temperament": ("consistency", ["alignment", "witnesses", "lineage"]),
    }

    result = {}
    for out_dim, (primary, secondaries) in mapping.items():
        val = primary_weight * six_dim[primary]
        for sec in secondaries:
            val += secondary_weight * six_dim[sec]
        result[out_dim] = val
    return result


def mrh_trust_decay(base_trust, hops, decay_factor):
    """MRH trust decay: trust = base * decay^hop, 5+ = BEYOND = 0"""
    result = []
    for h in hops:
        if h >= 5:
            result.append(0.0)
        else:
            result.append(base_trust * (decay_factor ** h))
    return result


def coherence(t3_comp, v3_comp, energy_ratio):
    """Coherence = t3*0.4 + v3*0.3 + energy*0.3"""
    return t3_comp * 0.4 + v3_comp * 0.3 + energy_ratio * 0.3


def validate_t3v3():
    """Validate T3V3 tensor operation test vectors."""
    print("\n═══ T3V3 Tensor Operations ═══")
    path = os.path.join(SCRIPT_DIR, "t3v3", "tensor-operations.json")
    with open(path) as f:
        data = json.load(f)

    for vec in data["vectors"]:
        vid = vec["id"]
        desc = vec["description"]
        op = vec["operation"]
        inp = vec["input"]
        exp = vec["expected"]
        tol = vec.get("tolerance", 0.0001)
        print(f"\n  [{vid}] {desc}")

        if op == "t3_composite":
            result = t3_composite(inp["talent"], inp["training"], inp["temperament"])
            check(approx(result, exp["composite"], tol),
                  f"{vid}: T3 composite {result} != {exp['composite']}")

        elif op == "v3_composite":
            result = v3_composite(inp["valuation"], inp["veracity"], inp["validity"])
            check(approx(result, exp["composite"], tol),
                  f"{vid}: V3 composite {result} != {exp['composite']}")

        elif op == "t3_update":
            result, base_delta, factors = t3_update(inp["initial"], inp["success"], inp["quality"])
            if "base_delta" in exp:
                check(approx(base_delta, exp["base_delta"], tol),
                      f"{vid}: base_delta {base_delta} != {exp['base_delta']}")
            if "talent" in exp:
                check(approx(result["talent"], exp["talent"], tol),
                      f"{vid}: talent {result['talent']} != {exp['talent']}")
                check(approx(result["training"], exp["training"], tol),
                      f"{vid}: training {result['training']} != {exp['training']}")
                check(approx(result["temperament"], exp["temperament"], tol),
                      f"{vid}: temperament {result['temperament']} != {exp['temperament']}")
            if "talent_clamped_at" in exp:
                check(result["talent"] >= exp["talent_clamped_at"],
                      f"{vid}: talent {result['talent']} below clamp {exp['talent_clamped_at']}")
                check(result["training"] >= exp["training_clamped_at"],
                      f"{vid}: training below clamp")
                check(result["temperament"] >= exp["temperament_clamped_at"],
                      f"{vid}: temperament below clamp")
            if "talent_max" in exp:
                check(result["talent"] <= exp["talent_max"],
                      f"{vid}: talent {result['talent']} above max {exp['talent_max']}")
                check(result["training"] <= exp["training_max"],
                      f"{vid}: training above max")
                check(result["temperament"] <= exp["temperament_max"],
                      f"{vid}: temperament above max")

        elif op == "diminishing_returns":
            result = diminishing_returns(inp["repeat_count"], inp["base_factor"])
            for i, (r, e) in enumerate(zip(result, exp["factors"])):
                check(approx(r, e, tol),
                      f"{vid}: factor[{i}] {r} != {e}")

        elif op == "trust_bridge":
            result = trust_bridge(inp["six_dim"])
            check(approx(result["talent"], exp["talent"], tol),
                  f"{vid}: talent bridge {result['talent']} != {exp['talent']}")
            check(approx(result["training"], exp["training"], tol),
                  f"{vid}: training bridge {result['training']} != {exp['training']}")
            check(approx(result["temperament"], exp["temperament"], tol),
                  f"{vid}: temperament bridge {result['temperament']} != {exp['temperament']}")

        elif op == "mrh_trust_decay":
            result = mrh_trust_decay(inp["base_trust"], inp["hops"], inp["decay_factor"])
            for i, (r, e) in enumerate(zip(result, exp["trust_per_hop"])):
                check(approx(r, e, tol),
                      f"{vid}: hop[{i}] trust {r} != {e}")

        elif op == "coherence":
            result = coherence(inp["t3_composite"], inp["v3_composite"], inp["energy_ratio"])
            check(approx(result, exp["coherence"], tol),
                  f"{vid}: coherence {result} != {exp['coherence']}")

        else:
            print(f"  SKIP: unknown operation '{op}'")


# ── ATP Transfer Operations ──────────────────────────────────────────

def atp_transfer(sender_bal, receiver_bal, amount, fee_rate):
    """Basic ATP transfer with fee."""
    fee = amount * fee_rate
    sender_bal -= (amount + fee)
    receiver_bal += amount
    return sender_bal, receiver_bal, fee


def atp_transfer_capped(sender_bal, receiver_bal, amount, fee_rate, max_balance):
    """ATP transfer with MAX_BALANCE cap and overflow return."""
    fee = amount * fee_rate
    sender_bal -= (amount + fee)
    actual_credit = max(0.0, min(amount, max_balance - receiver_bal))
    overflow = amount - actual_credit
    receiver_bal += actual_credit
    sender_bal += overflow
    return sender_bal, receiver_bal, fee, actual_credit, overflow


def sliding_scale(quality, base_payment, zero_threshold, full_threshold):
    """Sliding scale payment based on quality.

    Continuous piecewise: 0 below zero, linear ramp to base in [zero,full],
    flat base_payment above full. No discontinuity at threshold.
    Quality incentive above full_threshold comes from T3 reputation, not payment.
    """
    if quality < zero_threshold:
        return 0.0
    elif quality <= full_threshold:
        scale = (quality - zero_threshold) / (full_threshold - zero_threshold)
        return base_payment * scale
    else:
        return base_payment


def energy_ratio(atp, adp):
    """Energy ratio = atp / (atp + adp), default 0.5 for zero/zero."""
    total = atp + adp
    if total == 0:
        return 0.5
    return atp / total


def recharge(current, initial, rate, max_multiplier):
    """Recharge: add initial*rate, cap at initial*multiplier."""
    max_bal = initial * max_multiplier
    amount = min(initial * rate, max_bal - current)
    amount = max(0.0, amount)
    return current + amount, amount, amount < initial * rate


def validate_atp():
    """Validate ATP transfer operation test vectors."""
    print("\n═══ ATP Transfer Operations ═══")
    path = os.path.join(SCRIPT_DIR, "atp", "transfer-operations.json")
    with open(path) as f:
        data = json.load(f)

    for vec in data["vectors"]:
        vid = vec["id"]
        desc = vec["description"]
        op = vec["operation"]
        inp = vec["input"]
        exp = vec["expected"]
        tol = vec.get("tolerance", 0.0001)
        print(f"\n  [{vid}] {desc}")

        if op == "transfer":
            s, r, fee = atp_transfer(
                inp["sender_balance"], inp["receiver_balance"],
                inp["amount"], inp["fee_rate"])
            check(approx(fee, exp["fee"], tol), f"{vid}: fee {fee} != {exp['fee']}")
            check(approx(s, exp["sender_balance"], tol),
                  f"{vid}: sender {s} != {exp['sender_balance']}")
            check(approx(r, exp["receiver_balance"], tol),
                  f"{vid}: receiver {r} != {exp['receiver_balance']}")

        elif op == "transfer_capped":
            s, r, fee, actual, overflow = atp_transfer_capped(
                inp["sender_balance"], inp["receiver_balance"],
                inp["amount"], inp["fee_rate"], inp["max_balance"])
            check(approx(fee, exp["fee"], tol), f"{vid}: fee {fee} != {exp['fee']}")
            check(approx(actual, exp["actual_credit"], tol),
                  f"{vid}: actual_credit {actual} != {exp['actual_credit']}")
            check(approx(overflow, exp["overflow"], tol),
                  f"{vid}: overflow {overflow} != {exp['overflow']}")
            check(approx(s, exp["sender_balance"], tol),
                  f"{vid}: sender {s} != {exp['sender_balance']}")
            check(approx(r, exp["receiver_balance"], tol),
                  f"{vid}: receiver {r} != {exp['receiver_balance']}")

        elif op == "conservation_check":
            balances = list(inp["initial_balances"])
            total_fees = 0.0
            per_fees = []
            for t in inp["transfers"]:
                amount = t["amount"]
                fee = amount * inp["fee_rate"]
                per_fees.append(fee)
                total_fees += fee
                balances[t["from"]] -= (amount + fee)
                balances[t["to"]] += amount
            final_total = sum(balances)
            check(approx(final_total, exp["final_total"], tol),
                  f"{vid}: final_total {final_total} != {exp['final_total']}")
            check(approx(total_fees, exp["total_fees"], tol),
                  f"{vid}: total_fees {total_fees} != {exp['total_fees']}")
            check(approx(exp["initial_total"], final_total + total_fees, tol),
                  f"{vid}: conservation violated: {exp['initial_total']} != {final_total} + {total_fees}")

        elif op == "sliding_scale":
            result = sliding_scale(
                inp["quality"], inp["base_payment"],
                inp["zero_threshold"], inp["full_threshold"])
            check(approx(result, exp["payment"], tol),
                  f"{vid}: payment {result} != {exp['payment']}")

        elif op == "lock_lifecycle":
            bal = inp["initial_balance"]
            lock_amt = inp["lock_amount"]
            # After lock
            avail = bal - lock_amt
            locked = lock_amt
            check(approx(avail, exp["after_lock"]["available"], tol),
                  f"{vid}: lock available {avail} != {exp['after_lock']['available']}")
            check(approx(locked, exp["after_lock"]["locked"], tol),
                  f"{vid}: lock locked {locked} != {exp['after_lock']['locked']}")
            check(approx(avail + locked, exp["after_lock"]["total"], tol),
                  f"{vid}: lock total != {exp['after_lock']['total']}")
            # After commit
            committed = locked
            locked_after_commit = 0.0
            check(approx(avail, exp["after_commit"]["available"], tol),
                  f"{vid}: commit available")
            check(approx(locked_after_commit, exp["after_commit"]["locked"], tol),
                  f"{vid}: commit locked")
            check(approx(avail, exp["after_commit"]["total"], tol),
                  f"{vid}: commit total {avail} != {exp['after_commit']['total']}")
            # After rollback instead
            rollback_avail = bal
            check(approx(rollback_avail, exp["after_rollback_instead"]["available"], tol),
                  f"{vid}: rollback available")
            check(approx(rollback_avail, exp["after_rollback_instead"]["total"], tol),
                  f"{vid}: rollback total")

        elif op == "recharge":
            if "current_balance" in inp:
                new_bal, amount, capped = recharge(
                    inp["current_balance"], inp["initial_balance"],
                    inp["recharge_rate"], inp["max_recharge_multiplier"])
                check(approx(amount, exp["recharge_amount"], tol),
                      f"{vid}: recharge_amount {amount} != {exp['recharge_amount']}")
                check(approx(new_bal, exp["new_balance"], tol),
                      f"{vid}: new_balance {new_bal} != {exp['new_balance']}")
                if "capped" in exp:
                    check(capped == exp["capped"],
                          f"{vid}: capped {capped} != {exp['capped']}")

        elif op == "sybil_cost":
            n = inp["num_identities"]
            hw = inp["hardware_cost_per_identity"]
            stake = inp["atp_stake_per_identity"]
            fee_rate = inp["transfer_fee_rate"]
            setup = n * (hw + stake)
            circular_loss = n * stake * fee_rate
            check(approx(setup, exp["total_setup_cost"], tol),
                  f"{vid}: setup cost {setup} != {exp['total_setup_cost']}")
            check(approx(setup / n, exp["per_identity_cost"], tol),
                  f"{vid}: per identity cost")
            check(approx(circular_loss, exp["circular_flow_loss_per_cycle"], tol),
                  f"{vid}: circular loss {circular_loss} != {exp['circular_flow_loss_per_cycle']}")

        elif op == "energy_ratio":
            if "atp_balance" in inp:
                result = energy_ratio(inp["atp_balance"], inp["adp_accumulated"])
                check(approx(result, exp["energy_ratio"], tol),
                      f"{vid}: energy_ratio {result} != {exp['energy_ratio']}")
            elif "cases" in inp:
                for i, case in enumerate(inp["cases"]):
                    result = energy_ratio(case["atp"], case["adp"])
                    check(approx(result, exp["ratios"][i], tol),
                          f"{vid}: case[{i}] ratio {result} != {exp['ratios'][i]}")

        elif op == "fee_sensitivity":
            for i, rate in enumerate(inp["fee_rates"]):
                fee = inp["amount"] * rate
                net = inp["amount"]  # receiver gets full amount
                total_cost = inp["amount"] + fee  # sender pays amount + fee
                check(approx(fee, exp["fees"][i], tol),
                      f"{vid}: fee[{i}] {fee} != {exp['fees'][i]}")
                check(approx(total_cost, exp["total_sender_costs"][i], tol),
                      f"{vid}: total_cost[{i}] {total_cost} != {exp['total_sender_costs'][i]}")

        elif op == "settlement":
            for i, q in enumerate(inp["quality_scores"]):
                result = sliding_scale(
                    q, inp["task_payment"],
                    inp["zero_threshold"], inp["full_threshold"])
                check(approx(result, exp["payments"][i], tol),
                      f"{vid}: settlement[{i}] q={q} payment {result} != {exp['payments'][i]}")

        else:
            print(f"  SKIP: unknown operation '{op}'")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    global passed, failed, errors
    suites = sys.argv[1:] if len(sys.argv) > 1 else ["t3v3", "atp"]

    print("╔══════════════════════════════════════════════════════════╗")
    print("║         Web4 Cross-Language Test Vector Validator       ║")
    print("╚══════════════════════════════════════════════════════════╝")

    if "t3v3" in suites:
        validate_t3v3()
    if "atp" in suites:
        validate_atp()

    print(f"\n{'═' * 58}")
    print(f"  Results: {passed} passed, {failed} failed")
    if errors:
        print(f"\n  Failures:")
        for e in errors:
            print(f"    - {e}")
    print(f"{'═' * 58}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
