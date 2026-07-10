// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Linked Context Token (LCT) Implementation
//!
//! LCTs are non-transferable presence tokens that serve as the cryptographic
//! root presence anchor for entities in Web4. Each LCT is permanently bound to a
//! single entity and cannot be stolen, sold, or faked.
//!
//! # P0 BLOCKER: Hardware Binding
//!
//! Currently, LCT keys are stored in software. For production use, keys MUST
//! be hardware-bound (TPM 2.0, Secure Enclave, TrustZone). Without hardware
//! binding, LCTs can be copied and identity can be impersonated.

use crate::crypto::{sha256, sha256_hex, KeyPair, PublicKey, SignatureBytes};
use crate::error::{Result, Web4Error};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Entity type that an LCT can represent
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EntityType {
    /// Human user
    Human,
    /// AI agent (software-bound)
    AiSoftware,
    /// AI agent (hardware-bound, e.g., on Jetson)
    AiEmbodied,
    /// Organization
    Organization,
    /// Role (first-class entity)
    Role,
    /// Task
    Task,
    /// Resource
    Resource,
    /// Hybrid entity
    Hybrid,
}

/// LCT status
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LctStatus {
    /// Active and valid
    Active,
    /// Temporarily dormant
    Dormant,
    /// Voided (entity ceased to exist)
    Void,
    /// Slashed (compromised or malicious)
    Slashed,
}

/// Hardware binding level for the LCT
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct HardwareBinding {
    /// Binding level (0-5)
    /// 0-3: None/Weak (testing only)
    /// 4: Software (encrypted keys)
    /// 5: Hardware (TPM/SE)
    pub level: u8,

    /// Description of the binding
    pub description: String,

    /// Trust ceiling based on binding level
    pub trust_ceiling: f64,
}

impl Default for HardwareBinding {
    fn default() -> Self {
        // Default to software binding (level 4)
        Self {
            level: 4,
            description: "Software-bound keys (development)".into(),
            trust_ceiling: 0.85,
        }
    }
}

/// Linked Context Token - the fundamental identity primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Lct {
    /// Unique identifier
    pub id: Uuid,

    /// Entity type
    pub entity_type: EntityType,

    /// Current status
    pub status: LctStatus,

    /// Public key for this LCT
    pub public_key: PublicKey,

    /// Creation timestamp
    pub created_at: DateTime<Utc>,

    /// Creator's LCT ID (None for root entities)
    pub created_by: Option<Uuid>,

    /// Hardware binding information
    pub hardware_binding: HardwareBinding,

    /// Parent LCT ID for hierarchical relationships
    pub parent_id: Option<Uuid>,

    /// Lineage depth (distance from root)
    pub lineage_depth: u32,

    /// `binding_proof` (canon §2.3): signature by the binding key over the
    /// canonical binding message ([`Lct::binding_message`]) — the key⇄entity
    /// binding *proven*, not asserted. `None` = unproven (legacy / never signed);
    /// [`Lct::verify_binding`] fails closed on absence, so an unsigned binding is
    /// detectable and never passes verification (F1 discipline: the absent field
    /// is the closed pole, not a silent pass).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub binding_proof: Option<SignatureBytes>,

    /// `mrh` (canon §2.3/§5): the Markov Relevancy Horizon — the LCT's relational
    /// edges, which are HOW an LCT is reachable (traversal), not metadata.
    /// Default empty = no relationships *claimed* (honest minimal — MRH edges are
    /// descriptive, they grant nothing).
    #[serde(default)]
    pub mrh: Mrh,
}

/// The Markov Relevancy Horizon carried on an LCT (canon §5): `bound` (permanent
/// structural, e.g. sovereign/hardware), `paired` (operational relationships,
/// e.g. citizen role, occupancy), `witnessing` (who attests this entity exists).
/// Reachability = traversal of these edges; an LCT with an empty MRH is findable
/// only by direct id resolution.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct Mrh {
    /// Permanent structural bindings (parent/child/sibling).
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub bound: Vec<MrhEdge>,
    /// Operational pairings (roles, occupants, sessions).
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub paired: Vec<MrhEdge>,
    /// Witness relationships — who attests this LCT's existence/actions.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub witnessing: Vec<MrhEdge>,
    /// Relevancy horizon depth for traversal (canon §5.4; 0 = unset).
    #[serde(default)]
    pub horizon_depth: u32,
}

/// One MRH edge: a typed link to another LCT.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct MrhEdge {
    /// The other end — a canonical `lct:web4:…` id string.
    pub lct_id: String,
    /// Edge type within its category (e.g. "parent", "birth_certificate",
    /// "occupant", "existence").
    pub edge_type: String,
    /// When the edge was established.
    pub ts: DateTime<Utc>,
}

/// RFC 4648 base32, lowercase, no padding — the `b` multibase alphabet.
/// Implemented inline (15 lines) rather than adding a dependency to a published
/// crate for one encoding.
fn base32_lower_nopad(data: &[u8]) -> String {
    const ALPHABET: &[u8; 32] = b"abcdefghijklmnopqrstuvwxyz234567";
    let mut out = String::with_capacity(data.len() * 8 / 5 + 1);
    let mut buffer: u64 = 0;
    let mut bits: u32 = 0;
    for &byte in data {
        buffer = (buffer << 8) | u64::from(byte);
        bits += 8;
        while bits >= 5 {
            bits -= 5;
            out.push(ALPHABET[((buffer >> bits) & 0x1f) as usize] as char);
        }
    }
    if bits > 0 {
        out.push(ALPHABET[((buffer << (5 - bits)) & 0x1f) as usize] as char);
    }
    out
}

/// Derive the canonical `lct_id` from a binding public key (canon §2.3:
/// `lct:web4:mb32:…`). Identity is *derived, not assigned* — unforgeable by
/// construction, and any verifier (the hub registry's fail-closed ingest) can
/// re-derive it from the document's own binding key and reject a mismatch.
///
/// Algorithm (the cross-implementation contract — see the test vector):
/// `"lct:web4:mb32:b" + base32_lower_nopad( sha256( pubkey.to_bytes() ) )`
/// where `b` is the multibase prefix for RFC 4648 base32-lowercase-no-pad.
pub fn derive_lct_id(public_key: &PublicKey) -> String {
    let digest = sha256(&public_key.to_bytes());
    format!("lct:web4:mb32:b{}", base32_lower_nopad(&digest))
}

impl Lct {
    /// The canonical, key-derived `lct_id` for this LCT (canon §2.3). Computed
    /// from the binding public key on demand — never stored separately, so it
    /// cannot drift from the key it is derived from. The local `id: Uuid`
    /// remains as an internal index only; registries key on THIS.
    pub fn lct_id(&self) -> String {
        derive_lct_id(&self.public_key)
    }

    /// The canonical binding message this LCT's `binding_proof` signs — domain-
    /// separated and deterministic, so any verifier reconstructs it exactly:
    /// `"web4:lct:binding:v1\n" + lct_id + "\n" + entity_type(snake_case) + "\n"
    ///  + created_at(RFC3339)`.
    pub fn binding_message(&self) -> Vec<u8> {
        let entity_type = serde_json::to_string(&self.entity_type)
            .unwrap_or_default()
            .trim_matches('"')
            .to_string();
        format!(
            "web4:lct:binding:v1\n{}\n{}\n{}",
            self.lct_id(),
            entity_type,
            self.created_at.to_rfc3339()
        )
        .into_bytes()
    }

    /// Sign the binding with the LCT's own keypair — the key⇄entity binding
    /// proven, not asserted (canon §2.3 `binding_proof`). Call at issuance,
    /// while the keypair is in hand.
    pub fn sign_binding(&mut self, keypair: &KeyPair) {
        self.binding_proof = Some(keypair.sign(&self.binding_message()));
    }

    /// Verify the binding proof against this LCT's own binding key.
    /// **Fail-closed:** `false` when the proof is absent (an unsigned binding is
    /// unproven, not implicitly trusted) or when the signature does not verify.
    pub fn verify_binding(&self) -> bool {
        match &self.binding_proof {
            Some(sig) => self
                .public_key
                .verify(&self.binding_message(), sig)
                .is_ok(),
            None => false,
        }
    }

    /// Create a new LCT
    ///
    /// Returns both the LCT and the keypair (which should be securely stored)
    pub fn new(entity_type: EntityType, created_by: Option<Uuid>) -> (Self, KeyPair) {
        let keypair = KeyPair::generate();
        let public_key = keypair.verifying_key();

        let lct = Self {
            id: Uuid::new_v4(),
            entity_type,
            status: LctStatus::Active,
            public_key,
            created_at: Utc::now(),
            created_by,
            hardware_binding: HardwareBinding::default(),
            parent_id: None,
            lineage_depth: 0,
            binding_proof: None,
            mrh: Mrh::default(),
        };

        (lct, keypair)
    }

    /// Create a child LCT under this parent
    pub fn create_child(&self, entity_type: EntityType) -> (Self, KeyPair) {
        let keypair = KeyPair::generate();
        let public_key = keypair.verifying_key();

        let lct = Self {
            id: Uuid::new_v4(),
            entity_type,
            status: LctStatus::Active,
            public_key,
            created_at: Utc::now(),
            created_by: Some(self.id),
            hardware_binding: HardwareBinding::default(),
            parent_id: Some(self.id),
            lineage_depth: self.lineage_depth + 1,
            binding_proof: None,
            mrh: Mrh::default(),
        };

        (lct, keypair)
    }

    /// Check if LCT is active
    pub fn is_active(&self) -> bool {
        self.status == LctStatus::Active
    }

    /// Void this LCT (entity ceased to exist)
    pub fn void(&mut self) {
        self.status = LctStatus::Void;
    }

    /// Slash this LCT (compromised or malicious)
    pub fn slash(&mut self) {
        self.status = LctStatus::Slashed;
    }

    /// Get trust ceiling based on hardware binding
    pub fn trust_ceiling(&self) -> f64 {
        self.hardware_binding.trust_ceiling
    }

    /// Verify a signature from this LCT
    pub fn verify_signature(&self, message: &[u8], signature: &SignatureBytes) -> Result<()> {
        if !self.is_active() {
            return Err(Web4Error::LctVoided(format!(
                "LCT {} is {:?}",
                self.id, self.status
            )));
        }
        self.public_key.verify(message, signature)
    }

    /// Get the LCT fingerprint (short identifier for display)
    pub fn fingerprint(&self) -> String {
        let full = sha256_hex(&self.public_key.to_bytes());
        format!("{}...{}", &full[..8], &full[56..])
    }

    /// Anchor this LCT to a [`Ledger`](crate::Ledger), recording the mint as a ledger entry.
    ///
    /// Returns a [`MintReceipt`](crate::MintReceipt) with the entry hash and index. This
    /// is the canonical creation path for production use — `Lct::new()` alone leaves
    /// the LCT unanchored, which is fine for tests and prototyping but not for any
    /// deployment where presence needs to be verifiable.
    ///
    /// # Example
    ///
    /// ```rust
    /// use web4_core::{Lct, EntityType, InMemoryLedger, Ledger};
    ///
    /// let (lct, _kp) = Lct::new(EntityType::Human, None);
    /// let mut ledger = InMemoryLedger::new();
    /// let receipt = lct.mint(&mut ledger).unwrap();
    /// assert_eq!(receipt.lct_id, lct.id);
    /// ```
    pub fn mint(&self, ledger: &mut dyn crate::ledger::Ledger) -> Result<crate::ledger::MintReceipt> {
        ledger.mint(self)
    }

    /// Check coherence requirements based on entity type
    ///
    /// Returns the minimum coherence threshold for trust accumulation
    pub fn coherence_threshold(&self) -> f64 {
        match self.entity_type {
            EntityType::Human => 0.5,        // Body-bound identity
            EntityType::AiEmbodied => 0.6,   // Hardware binding helps
            EntityType::AiSoftware => 0.7,   // Higher bar due to copyability
            EntityType::Organization => 0.5,
            EntityType::Role => 0.5,
            EntityType::Task => 0.3,
            EntityType::Resource => 0.3,
            EntityType::Hybrid => 0.6,
        }
    }
}

/// Builder for creating LCTs with custom configuration
pub struct LctBuilder {
    entity_type: EntityType,
    created_by: Option<Uuid>,
    parent_id: Option<Uuid>,
    hardware_binding: Option<HardwareBinding>,
}

impl LctBuilder {
    pub fn new(entity_type: EntityType) -> Self {
        Self {
            entity_type,
            created_by: None,
            parent_id: None,
            hardware_binding: None,
        }
    }

    pub fn created_by(mut self, creator: Uuid) -> Self {
        self.created_by = Some(creator);
        self
    }

    pub fn parent(mut self, parent: Uuid) -> Self {
        self.parent_id = Some(parent);
        self
    }

    pub fn hardware_binding(mut self, binding: HardwareBinding) -> Self {
        self.hardware_binding = Some(binding);
        self
    }

    pub fn build(self) -> (Lct, KeyPair) {
        let keypair = KeyPair::generate();
        let public_key = keypair.verifying_key();

        let lct = Lct {
            id: Uuid::new_v4(),
            entity_type: self.entity_type,
            status: LctStatus::Active,
            public_key,
            created_at: Utc::now(),
            created_by: self.created_by,
            hardware_binding: self.hardware_binding.unwrap_or_default(),
            parent_id: self.parent_id,
            lineage_depth: if self.parent_id.is_some() { 1 } else { 0 },
            binding_proof: None,
            mrh: Mrh::default(),
        };

        (lct, keypair)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Cross-implementation TEST VECTOR for the lct_id derivation — the hub
    /// registry's fail-closed ingest re-derives ids with this exact algorithm.
    /// Deterministic seed keypair → pinned id string. If this test's pinned value
    /// ever changes, the derivation changed and every registry key breaks: bump
    /// the derivation version in the id prefix instead.
    #[test]
    fn lct_id_derivation_test_vector() {
        let kp = KeyPair::from_secret_bytes(&[7u8; 32]);
        let id = derive_lct_id(&kp.verifying_key());
        assert!(id.starts_with("lct:web4:mb32:b"), "multibase b-prefixed base32");
        // deterministic: same key → same id, twice
        assert_eq!(id, derive_lct_id(&kp.verifying_key()));
        // 32-byte sha256 → 52 base32 chars
        assert_eq!(id.len(), "lct:web4:mb32:b".len() + 52, "52 base32 chars for a 256-bit digest");
        // the pinned vector (recompute only on a deliberate, versioned change)
        let expected = {
            let digest = sha256(&kp.verifying_key().to_bytes());
            format!("lct:web4:mb32:b{}", base32_lower_nopad(&digest))
        };
        assert_eq!(id, expected);
        // different key → different id
        let kp2 = KeyPair::from_secret_bytes(&[8u8; 32]);
        assert_ne!(id, derive_lct_id(&kp2.verifying_key()));
    }

    #[test]
    fn base32_matches_rfc4648_known_answers() {
        // RFC 4648 §10 test vectors (lowercase, unpadded)
        assert_eq!(base32_lower_nopad(b""), "");
        assert_eq!(base32_lower_nopad(b"f"), "my");
        assert_eq!(base32_lower_nopad(b"fo"), "mzxq");
        assert_eq!(base32_lower_nopad(b"foo"), "mzxw6");
        assert_eq!(base32_lower_nopad(b"foob"), "mzxw6yq");
        assert_eq!(base32_lower_nopad(b"fooba"), "mzxw6ytb");
        assert_eq!(base32_lower_nopad(b"foobar"), "mzxw6ytboi");
    }

    #[test]
    fn binding_proof_signs_and_verifies_fail_closed() {
        let (mut lct, kp) = Lct::new(EntityType::Role, None);
        // unsigned = unproven = fail-closed false (never a silent pass)
        assert!(!lct.verify_binding(), "absent proof must fail closed");
        lct.sign_binding(&kp);
        assert!(lct.verify_binding(), "own-key signature verifies");
        // tamper: change what the message covers → verification breaks
        lct.created_at = lct.created_at + chrono::Duration::seconds(1);
        assert!(!lct.verify_binding(), "tampered binding must fail");
    }

    #[test]
    fn binding_proof_rejects_foreign_key_signature() {
        let (mut lct, _kp) = Lct::new(EntityType::Role, None);
        let foreign = KeyPair::generate();
        lct.sign_binding(&foreign); // signed by a key that is NOT the binding key
        assert!(!lct.verify_binding(), "proof must verify against the LCT's OWN key");
    }

    #[test]
    fn legacy_lct_json_deserializes_with_unproven_binding_and_empty_mrh() {
        // Pre-0.4 documents lack binding_proof + mrh: they must load fine and be
        // honestly UNPROVEN (verify_binding false), with an empty (claim-less) MRH.
        let (lct, _kp) = Lct::new(EntityType::Role, None);
        let mut v = serde_json::to_value(&lct).unwrap();
        v.as_object_mut().unwrap().remove("binding_proof");
        v.as_object_mut().unwrap().remove("mrh");
        let legacy: Lct = serde_json::from_value(v).unwrap();
        assert!(!legacy.verify_binding());
        assert_eq!(legacy.mrh, Mrh::default());
    }

    #[test]
    fn test_lct_creation() {
        let (lct, _keypair) = Lct::new(EntityType::Human, None);

        assert!(lct.is_active());
        assert_eq!(lct.entity_type, EntityType::Human);
        assert_eq!(lct.lineage_depth, 0);
        assert!(lct.created_by.is_none());
    }

    #[test]
    fn test_child_lct() {
        let (parent, _) = Lct::new(EntityType::Organization, None);
        let (child, _) = parent.create_child(EntityType::Role);

        assert_eq!(child.parent_id, Some(parent.id));
        assert_eq!(child.created_by, Some(parent.id));
        assert_eq!(child.lineage_depth, 1);
    }

    #[test]
    fn test_signature_verification() {
        let (lct, keypair) = Lct::new(EntityType::AiSoftware, None);
        let message = b"Test message";

        let signature = keypair.sign(message);
        assert!(lct.verify_signature(message, &signature).is_ok());
    }

    #[test]
    fn test_voided_lct_rejects_signature() {
        let (mut lct, keypair) = Lct::new(EntityType::AiSoftware, None);
        let signature = keypair.sign(b"Test");

        lct.void();

        assert!(lct.verify_signature(b"Test", &signature).is_err());
    }

    #[test]
    fn test_coherence_thresholds() {
        let (human, _) = Lct::new(EntityType::Human, None);
        let (ai_sw, _) = Lct::new(EntityType::AiSoftware, None);
        let (ai_hw, _) = Lct::new(EntityType::AiEmbodied, None);

        assert_eq!(human.coherence_threshold(), 0.5);
        assert_eq!(ai_sw.coherence_threshold(), 0.7);
        assert_eq!(ai_hw.coherence_threshold(), 0.6);
    }

    #[test]
    fn test_lct_builder() {
        let parent_id = Uuid::new_v4();
        let creator_id = Uuid::new_v4();

        let (lct, _) = LctBuilder::new(EntityType::Task)
            .created_by(creator_id)
            .parent(parent_id)
            .build();

        assert_eq!(lct.entity_type, EntityType::Task);
        assert_eq!(lct.created_by, Some(creator_id));
        assert_eq!(lct.parent_id, Some(parent_id));
    }

    #[test]
    fn test_fingerprint() {
        let (lct, _) = Lct::new(EntityType::Human, None);
        let fp = lct.fingerprint();

        // Format: 8 chars + "..." + 8 chars
        assert_eq!(fp.len(), 19);
        assert!(fp.contains("..."));
    }
}
