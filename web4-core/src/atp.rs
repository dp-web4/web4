// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! ATP/ADP — Allocation Transfer / Discharge Packets
//!
//! Bio-inspired energy metabolism for Web4 societies. ATP is a unit of
//! account (NOT currency) — each society reifies its own resources
//! (compute, attention, hardware, time) into ATP at policies it chooses.
//!
//! Key invariants:
//! - Conservation: sum(initial) == sum(final) + total_fees
//! - Two-state only: tokens exist as ATP or ADP, never both
//! - Pool-managed: exists in society pools, not per-entity wallets
//!
//! Reference: `web4-standard/core-spec/atp-adp-cycle.md`

use crate::error::{Result, Web4Error};
use serde::{Deserialize, Serialize};

/// ATP account — tracks available, locked (escrowed), and discharged tokens.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ATPAccount {
    /// Tokens available for transfer or locking
    pub available: f64,
    /// Tokens locked (escrowed for pending operations)
    pub locked: f64,
    /// Discharged tokens (spent — ADP)
    pub adp: f64,
    /// Initial balance at creation (for recharge calculations)
    pub initial_balance: f64,
}

impl ATPAccount {
    pub fn new(initial: f64) -> Self {
        Self {
            available: initial,
            locked: 0.0,
            adp: 0.0,
            initial_balance: initial,
        }
    }

    /// Total active ATP (available + locked). ADP is separate.
    pub fn total(&self) -> f64 {
        self.available + self.locked
    }

    /// Energy ratio: ATP / (ATP + ADP). High = earning, low = spending.
    /// Returns 0.5 (neutral) if both are zero.
    pub fn energy_ratio(&self) -> f64 {
        let total = self.total() + self.adp;
        if total == 0.0 {
            0.5
        } else {
            self.total() / total
        }
    }

    /// Lock tokens from available → locked (escrow for pending operation).
    pub fn lock(&mut self, amount: f64) -> Result<()> {
        if amount < 0.0 {
            return Err(Web4Error::InvalidInput("Lock amount must be non-negative".into()));
        }
        if self.available < amount {
            return Err(Web4Error::InvalidInput(format!(
                "Insufficient available ATP: {} < {}",
                self.available, amount
            )));
        }
        self.available -= amount;
        self.locked += amount;
        Ok(())
    }

    /// Commit locked tokens → ADP (discharge). Called on successful completion.
    pub fn commit(&mut self, amount: f64) -> Result<f64> {
        if amount < 0.0 {
            return Err(Web4Error::InvalidInput("Commit amount must be non-negative".into()));
        }
        let actual = amount.min(self.locked);
        self.locked -= actual;
        self.adp += actual;
        Ok(actual)
    }

    /// Rollback locked tokens → available. Called on failure/cancellation.
    pub fn rollback(&mut self, amount: f64) -> Result<f64> {
        if amount < 0.0 {
            return Err(Web4Error::InvalidInput("Rollback amount must be non-negative".into()));
        }
        let actual = amount.min(self.locked);
        self.locked -= actual;
        self.available += actual;
        Ok(actual)
    }

    /// Recharge: add ATP up to max_multiplier * initial_balance.
    /// Returns actual amount recharged.
    pub fn recharge(&mut self, rate: f64, max_multiplier: f64) -> f64 {
        let max_balance = self.initial_balance * max_multiplier;
        let raw_recharge = self.initial_balance * rate;
        let space = (max_balance - self.total()).max(0.0);
        let actual = raw_recharge.min(space);
        self.available += actual;
        actual
    }
}

impl Default for ATPAccount {
    fn default() -> Self {
        Self::new(100.0)
    }
}

/// Result of an ATP transfer between two accounts.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TransferResult {
    /// Fee charged (additive to sender, not deducted from amount)
    pub fee: f64,
    /// Sender's final available balance
    pub sender_balance: f64,
    /// Receiver's final available balance
    pub receiver_balance: f64,
    /// Amount actually credited to receiver (may be < amount if capped)
    pub actual_credit: f64,
    /// Amount returned to sender if receiver hit max_balance cap
    pub overflow: f64,
}

/// Transfer ATP between two accounts.
///
/// Fee is additive to sender (sender pays amount + fee).
/// If max_balance is set, excess beyond receiver's cap overflows back to sender.
///
/// Conservation invariant: sender_deducted == actual_credit + fee + overflow
pub fn transfer(
    sender: &mut ATPAccount,
    receiver: &mut ATPAccount,
    amount: f64,
    fee_rate: f64,
    max_balance: Option<f64>,
) -> Result<TransferResult> {
    if amount < 0.0 {
        return Err(Web4Error::InvalidInput("Transfer amount must be non-negative".into()));
    }

    let fee = amount * fee_rate;
    let total_deduction = amount + fee;

    if sender.available < total_deduction {
        return Err(Web4Error::InvalidInput(format!(
            "Insufficient ATP: {} < {} (amount {} + fee {})",
            sender.available, total_deduction, amount, fee
        )));
    }

    let (actual_credit, overflow) = if let Some(max) = max_balance {
        let space = (max - receiver.available).max(0.0);
        let credit = amount.min(space);
        (credit, amount - credit)
    } else {
        (amount, 0.0)
    };

    sender.available -= total_deduction;
    sender.available += overflow; // return overflow
    receiver.available += actual_credit;

    Ok(TransferResult {
        fee,
        sender_balance: sender.available,
        receiver_balance: receiver.available,
        actual_credit,
        overflow,
    })
}

/// Sliding scale payment based on quality score.
///
/// Below zero_threshold: pays 0. Above full_threshold: pays full base_payment.
/// Between: linear interpolation.
pub fn sliding_scale(
    quality: f64,
    base_payment: f64,
    zero_threshold: f64,
    full_threshold: f64,
) -> f64 {
    if quality < zero_threshold {
        0.0
    } else if quality >= full_threshold {
        base_payment
    } else {
        base_payment * (quality - zero_threshold) / (full_threshold - zero_threshold)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_account_lifecycle() {
        let mut account = ATPAccount::new(100.0);
        assert_eq!(account.total(), 100.0);
        assert_eq!(account.energy_ratio(), 1.0); // all ATP, no ADP

        // Lock 30
        account.lock(30.0).unwrap();
        assert_eq!(account.available, 70.0);
        assert_eq!(account.locked, 30.0);
        assert_eq!(account.total(), 100.0);

        // Commit 20 (discharge to ADP)
        account.commit(20.0).unwrap();
        assert_eq!(account.locked, 10.0);
        assert_eq!(account.adp, 20.0);
        assert_eq!(account.total(), 80.0);

        // Energy ratio: 80 / (80 + 20) = 0.8
        assert!((account.energy_ratio() - 0.8).abs() < 1e-10);

        // Rollback remaining locked
        account.rollback(10.0).unwrap();
        assert_eq!(account.available, 80.0);
        assert_eq!(account.locked, 0.0);
    }

    #[test]
    fn test_transfer_conservation() {
        let mut sender = ATPAccount::new(100.0);
        let mut receiver = ATPAccount::new(50.0);

        let result = transfer(&mut sender, &mut receiver, 30.0, 0.05, None).unwrap();

        assert_eq!(result.fee, 1.5);
        assert_eq!(result.actual_credit, 30.0);
        assert_eq!(result.overflow, 0.0);
        assert_eq!(sender.available, 68.5); // 100 - 30 - 1.5
        assert_eq!(receiver.available, 80.0); // 50 + 30

        // Conservation: sender lost 31.5, receiver gained 30, fee = 1.5
        // 31.5 == 30 + 1.5 ✓
    }

    #[test]
    fn test_transfer_with_max_balance() {
        let mut sender = ATPAccount::new(100.0);
        let mut receiver = ATPAccount::new(90.0);

        // Receiver can only take 10 more (max_balance = 100)
        let result = transfer(&mut sender, &mut receiver, 30.0, 0.0, Some(100.0)).unwrap();

        assert_eq!(result.actual_credit, 10.0);
        assert_eq!(result.overflow, 20.0);
        assert_eq!(sender.available, 90.0); // 100 - 30 + 20 overflow
        assert_eq!(receiver.available, 100.0);
    }

    #[test]
    fn test_recharge() {
        let mut account = ATPAccount::new(100.0);
        account.available = 50.0; // spent some

        let recharged = account.recharge(0.1, 3.0);
        assert_eq!(recharged, 10.0); // 100 * 0.1 = 10, space = 300 - 50 = 250
        assert_eq!(account.available, 60.0);
    }

    #[test]
    fn test_sliding_scale() {
        assert_eq!(sliding_scale(0.1, 100.0, 0.3, 0.7), 0.0);
        assert!((sliding_scale(0.5, 100.0, 0.3, 0.7) - 50.0).abs() < 1e-10);
        assert_eq!(sliding_scale(0.8, 100.0, 0.3, 0.7), 100.0);
    }

    #[test]
    fn test_zero_balance_energy_ratio() {
        let account = ATPAccount::new(0.0);
        assert_eq!(account.energy_ratio(), 0.5); // neutral
    }

    #[test]
    fn test_insufficient_balance() {
        let mut sender = ATPAccount::new(10.0);
        let mut receiver = ATPAccount::new(0.0);
        let result = transfer(&mut sender, &mut receiver, 20.0, 0.0, None);
        assert!(result.is_err());
    }
}
