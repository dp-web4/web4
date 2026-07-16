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
    /// Society — a law-bearing collective that issues birth certificates and
    /// maintains an LCT registry (canon §2.3 lists `society` as a first-class
    /// entity type). Distinct from `Organization` for DISCRIMINATION, not trust:
    /// Phase-2 `society_conferred` provenance must check that the *conferring*
    /// entity is a society, which `Organization` cannot carry without conflation
    /// (HUB concord vote, 2026-07-10). Same coherence threshold as Organization —
    /// nothing reorders.
    Society,
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

    /// `legacy_alias` (canon lineage §2.3, migration case): a VERIFIABLE claim that
    /// this LCT continues a pre-LCT identity. `None` = no such claim (the common
    /// case). Re-derivable from recorded inputs, so the registry ingest checks it
    /// rather than trusting the publisher (F1). See [`LegacyAlias`].
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub legacy_alias: Option<LegacyAlias>,

    /// `attestations` (canon §2.3): signed witness statements about this LCT —
    /// the collection the birth-certificate validator consults. Default empty
    /// (an un-witnessed §3.2 bootstrap). See [`crate::attestation`].
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub attestations: Vec<crate::attestation::Attestation>,

    /// `birth_certificate` (canon §2.3/§4): present iff a society conferred
    /// citizenship on this entity. `None` = a Regular self-issued LCT (the honest
    /// default — society-conferred presence is proven, never assumed).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub birth_certificate: Option<crate::attestation::BirthCertificate>,
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

/// A canonical legacy-id derivation scheme (canon lineage §2.3, migration case).
/// The scheme lives HERE — in web4-core — so the producer (e.g. hestia's publish
/// path) and the verifier (the hub registry's ingest) recompute **byte-identical**
/// results; that shared derivation is the whole point, exactly the discipline
/// behind [`derive_lct_id`]. Inputs are recorded verbatim, so verification never
/// re-resolves anything — a later sovereign upgrade cannot retroactively break an
/// alias already recorded (HUB, hestia-lct-concord 2026-07-10).
///
/// `#[non_exhaustive]`: new legacy schemes are added here as more pre-LCT identity
/// spaces migrate, without breaking existing match sites.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "scheme", rename_all = "snake_case")]
#[non_exhaustive]
pub enum LegacyDerivation {
    /// hestia `member_lct`: `sha256(b"web4:member:" + plugin_id.trim() + sovereign)`,
    /// first 12 bytes lowercase-hex, prefixed `lct:web4:member:`. Mirrors
    /// `hestia::server::state::ServerState::member_lct` byte-for-byte (proven by a
    /// lockstep equivalence test in hestia).
    HestiaMember {
        plugin_id: String,
        sovereign: String,
    },
}

impl LegacyDerivation {
    /// Recompute the legacy id this scheme yields from its recorded inputs. MUST
    /// match the producing system byte-for-byte — that equality is what makes the
    /// alias a *checked fact* rather than a stored assertion (F1).
    pub fn derive(&self) -> String {
        match self {
            LegacyDerivation::HestiaMember { plugin_id, sovereign } => {
                let mut input = Vec::new();
                input.extend_from_slice(b"web4:member:");
                input.extend_from_slice(plugin_id.trim().as_bytes());
                input.extend_from_slice(sovereign.as_bytes());
                let digest = sha256(&input);
                let hex: String = digest[..12].iter().map(|b| format!("{:02x}", b)).collect();
                format!("lct:web4:member:{hex}")
            }
        }
    }

    /// Scheme-specific ingest invariant beyond re-derivation (pinned spec
    /// `registry-ingest-legacy-alias-spec` §3 invariant **(b)**): the recorded
    /// inputs must be well-formed independent of what they hash to. For
    /// `HestiaMember`, `plugin_id` MUST be non-empty after trim — an empty or
    /// whitespace-only plugin_id still `derive()`s a well-formed
    /// `lct:web4:member:<hex>`, so re-derivation alone (invariant (a)) would
    /// accept it; (b) rejects it at ingest. Exhaustive by scheme so a new
    /// derivation can't be added without deciding its input invariants.
    pub fn inputs_valid(&self) -> bool {
        match self {
            LegacyDerivation::HestiaMember { plugin_id, .. } => !plugin_id.trim().is_empty(),
        }
    }
}

/// A VERIFIABLE claim that this LCT continues a pre-LCT legacy identity — canon
/// lineage (§2.3) specialized for the migration case (a re-key would throw away
/// history worth keeping; an alias preserves continuity without a flag day). The
/// alias resolves *through* to this LCT and never mints a standalone registry
/// entry, so absence stays absent — the alias fabricates no presence.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LegacyAlias {
    /// The pre-LCT identifier this LCT continues (e.g. a hestia member label).
    pub legacy_id: String,
    /// How `legacy_id` was derived, inputs recorded verbatim for re-verification.
    pub derivation: LegacyDerivation,
}

impl LegacyAlias {
    /// `true` iff the alias satisfies BOTH pinned ingest invariants: **(a)**
    /// `legacy_id` re-derives from the recorded inputs, and **(b)** the inputs are
    /// well-formed ([`LegacyDerivation::inputs_valid`]). The registry's
    /// fail-closed ingest rejects the publish when this is `false` — a forged,
    /// drifted, or degenerate-input alias never enters the registry.
    pub fn verify(&self) -> bool {
        self.derivation.inputs_valid() && self.derivation.derive() == self.legacy_id
    }
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
    ///
    /// The timestamp is rendered with [`SecondsFormat::AutoSi`] + `use_z=true`,
    /// so the message bytes are **byte-identical to the wire form** serde writes
    /// (`…Z`, not `+00:00`). A non-chrono verifier that reconstructs this message
    /// from the document's own `created_at` string gets the exact bytes that were
    /// signed — the cross-implementation contract (HUB #499 blocker 2). Changing
    /// this rendering after any document is signed requires a `v1`→`v2` bump.
    pub fn binding_message(&self) -> Vec<u8> {
        let entity_type = serde_json::to_string(&self.entity_type)
            .unwrap_or_default()
            .trim_matches('"')
            .to_string();
        format!(
            "web4:lct:binding:v1\n{}\n{}\n{}",
            self.lct_id(),
            entity_type,
            self.created_at.to_rfc3339_opts(chrono::SecondsFormat::AutoSi, true)
        )
        .into_bytes()
    }

    /// Sign the binding with the LCT's own keypair — the key⇄entity binding
    /// proven, not asserted (canon §2.3 `binding_proof`). Call at issuance,
    /// while the keypair is in hand.
    ///
    /// **Debug-asserts the keypair binds this LCT's own public key** — signing
    /// with a foreign key would mint a binding that `verify_binding` then rejects,
    /// a caller error worth catching at the source (HUB #499 non-blocking nit;
    /// `RoleEntity::issue` is correct, but other constructors hand out the keypair
    /// and could be miswired). Debug-only: release builds still produce the (self-
    /// detectably invalid) proof rather than panicking in production.
    pub fn sign_binding(&mut self, keypair: &KeyPair) {
        debug_assert_eq!(
            keypair.verifying_key(),
            self.public_key,
            "sign_binding: keypair must bind this LCT's own public key"
        );
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

    /// `true` iff this LCT is a valid **birth certificate** (canon §4.2 / §11.2) —
    /// a society-conferred citizen, COSE-verified. Fail-closed on every clause:
    ///
    /// 1. a `birth_certificate` section is present,
    /// 2. ≥3 **distinct** birth witnesses (structural quorum),
    /// 3. exactly one **permanent** `birth_certificate` pairing in `mrh.paired`,
    /// 4. every birth witness has an `Existence` attestation in `attestations`
    ///    whose signature verifies against that witness's bound public key.
    ///
    /// `resolve_witness_pubkey` maps a witness LCT id → its bound key (the
    /// verifier's registry lookup). A witness whose key does not resolve, or
    /// whose signature fails, fails the whole certificate — a quorum you cannot
    /// verify is not a quorum. `None` from the resolver ⇒ reject (never skip).
    ///
    /// Absence of a `birth_certificate` returns `false` (a Regular LCT is not a
    /// birth certificate); use [`Lct::is_self_issued`] to distinguish "no cert"
    /// from "invalid cert".
    pub fn verify_birth_certificate<F>(&self, resolve_witness_pubkey: F) -> bool
    where
        F: Fn(&str) -> Option<PublicKey>,
    {
        let Some(bc) = &self.birth_certificate else {
            return false;
        };
        if !bc.quorum_structurally_ok() {
            return false;
        }
        // Exactly one permanent birth_certificate pairing (§4.2 clause 2).
        let citizen_pairings = self
            .mrh
            .paired
            .iter()
            .filter(|e| e.edge_type == "birth_certificate")
            .count();
        if citizen_pairings != 1 {
            return false;
        }
        // Every distinct witness must have a signature-valid Existence attestation.
        let subject = self.lct_id();
        let mut seen = std::collections::BTreeSet::new();
        for witness in bc.birth_witnesses.iter().filter(|w| seen.insert(*w)) {
            let Some(pubkey) = resolve_witness_pubkey(witness) else {
                return false; // unresolvable witness → cannot verify → reject
            };
            let attested = self.attestations.iter().any(|a| {
                a.witness == *witness
                    && a.attestation_type == crate::attestation::AttestationType::Existence
                    && a.verify(&subject, &pubkey)
            });
            if !attested {
                return false;
            }
        }
        true
    }

    /// `true` for a Regular self-issued LCT — no birth certificate (canon §4.3).
    /// The honest default state; the complement of "carries a (valid) birth cert".
    pub fn is_self_issued(&self) -> bool {
        self.birth_certificate.is_none()
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
            legacy_alias: None,
            attestations: Vec::new(),
            birth_certificate: None,
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
            legacy_alias: None,
            attestations: Vec::new(),
            birth_certificate: None,
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
            EntityType::Society => 0.5,      // same prior as Organization — no reorder
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
            legacy_alias: None,
            attestations: Vec::new(),
            birth_certificate: None,
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
        // The PINNED literal — NOT recomputed from the same primitives under test
        // (that would be a tautology that survives any consistent derivation drift).
        // Independently re-derived on HUB from the [7u8;32] seed and confirmed
        // byte-identical (#499). A foreign implementation asserts against THIS
        // string; if this line ever has to change, the derivation changed and every
        // registry key breaks — bump the id-prefix version instead of editing it.
        assert_eq!(
            id,
            "lct:web4:mb32:b72asyextvngonlc5w2nmguxza3frweppip5thyss5577kurghceq"
        );
        // different key → different id
        let kp2 = KeyPair::from_secret_bytes(&[8u8; 32]);
        assert_ne!(id, derive_lct_id(&kp2.verifying_key()));
    }

    #[test]
    fn legacy_alias_verifies_by_rederivation_and_rejects_forgery() {
        let sovereign = "lct:web4:hestia:sovereign:phase1-placeholder";
        let good = LegacyAlias {
            derivation: LegacyDerivation::HestiaMember {
                plugin_id: "claude-code".into(),
                sovereign: sovereign.into(),
            },
            legacy_id: LegacyDerivation::HestiaMember {
                plugin_id: "claude-code".into(),
                sovereign: sovereign.into(),
            }
            .derive(),
        };
        assert!(good.verify(), "honest alias re-derives");
        // forged: legacy_id claims a different member than the inputs yield
        let forged = LegacyAlias {
            legacy_id: "lct:web4:member:deadbeefdeadbeefdeadbeef".into(),
            derivation: LegacyDerivation::HestiaMember {
                plugin_id: "claude-code".into(),
                sovereign: sovereign.into(),
            },
        };
        assert!(!forged.verify(), "a claimed id that doesn't re-derive is rejected (F1)");
    }

    #[test]
    fn verify_enforces_invariant_b_nonempty_plugin_id() {
        // Invariant (b): an empty / whitespace-only plugin_id STILL derives a
        // well-formed lct:web4:member:<hex>, so re-derivation (a) alone would
        // accept it. verify() must reject it. Spec §3 (b).
        for pid in ["", "   ", "\t\n"] {
            let sovereign = "lct:web4:hestia:sovereign:phase1-placeholder";
            let derivation = LegacyDerivation::HestiaMember {
                plugin_id: pid.into(),
                sovereign: sovereign.into(),
            };
            // self-consistent: legacy_id IS what the (degenerate) inputs derive
            let alias = LegacyAlias {
                legacy_id: derivation.derive(),
                derivation: LegacyDerivation::HestiaMember {
                    plugin_id: pid.into(),
                    sovereign: sovereign.into(),
                },
            };
            assert!(
                alias.derivation.derive() == alias.legacy_id,
                "invariant (a) holds for the degenerate input"
            );
            assert!(
                !alias.verify(),
                "empty-after-trim plugin_id ({pid:?}) must be rejected by invariant (b)"
            );
            assert!(!alias.derivation.inputs_valid());
        }
    }

    #[test]
    fn hestia_member_derivation_pinned_vector() {
        // PINNED literal — the cross-implementation contract with hestia's
        // member_lct. hestia has a lockstep test asserting member_lct("claude-code")
        // under this sovereign equals THIS string; if this line must change, the
        // two implementations diverged — reconcile, don't edit.
        let id = LegacyDerivation::HestiaMember {
            plugin_id: "claude-code".into(),
            sovereign: "lct:web4:hestia:sovereign:phase1-placeholder".into(),
        }
        .derive();
        assert!(id.starts_with("lct:web4:member:"));
        assert_eq!(id.len(), "lct:web4:member:".len() + 24, "12 bytes → 24 hex chars");
        // trim invariance: the producer trims plugin_id
        let padded = LegacyDerivation::HestiaMember {
            plugin_id: "  claude-code  ".into(),
            sovereign: "lct:web4:hestia:sovereign:phase1-placeholder".into(),
        }
        .derive();
        assert_eq!(id, padded, "plugin_id is trimmed before hashing (mirrors member_lct)");
    }

    #[test]
    fn lct_with_legacy_alias_roundtrips_and_defaults_none() {
        let (mut lct, _kp) = Lct::new(EntityType::AiSoftware, None);
        assert!(lct.legacy_alias.is_none(), "no alias claim by default");
        lct.legacy_alias = Some(LegacyAlias {
            legacy_id: LegacyDerivation::HestiaMember {
                plugin_id: "alice".into(),
                sovereign: "s".into(),
            }
            .derive(),
            derivation: LegacyDerivation::HestiaMember {
                plugin_id: "alice".into(),
                sovereign: "s".into(),
            },
        });
        let restored: Lct = serde_json::from_str(&serde_json::to_string(&lct).unwrap()).unwrap();
        assert!(restored.legacy_alias.as_ref().unwrap().verify());
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
        // The threat model is a maliciously-constructed document, not a self-
        // inflicted miswiring — so build the foreign-signed proof DIRECTLY (bypass
        // sign_binding, which now debug-asserts against exactly this mistake). What
        // must hold regardless of provenance: verify_binding checks against the
        // LCT's OWN key, so a proof by any other key is rejected.
        let (mut lct, _kp) = Lct::new(EntityType::Role, None);
        let foreign = KeyPair::generate();
        lct.binding_proof = Some(foreign.sign(&lct.binding_message()));
        assert!(!lct.verify_binding(), "proof must verify against the LCT's OWN key");
    }

    #[test]
    fn signed_lct_json_roundtrip_verifies_from_wire_timestamp() {
        // The REGISTRY INGEST PATH (HUB #499): a signed LCT serialized to JSON and
        // back must still verify — proving binding_message reconstructed from the
        // document's own `created_at` WIRE string (…Z) is byte-identical to what was
        // signed. This is what breaks if to_rfc3339() (+00:00) diverges from serde.
        let (mut lct, kp) = Lct::new(EntityType::Role, None);
        lct.sign_binding(&kp);
        let json = serde_json::to_string(&lct).unwrap();
        let restored: Lct = serde_json::from_str(&json).unwrap();
        assert!(
            restored.verify_binding(),
            "signed LCT must verify after a JSON roundtrip (message == wire bytes)"
        );
    }

    #[test]
    fn birth_certificate_validates_fail_closed_end_to_end() {
        use crate::attestation::{Attestation, AttestationType, BirthCertificate, BirthContext};
        let (mut lct, kp) = Lct::new(EntityType::AiSoftware, None);
        lct.sign_binding(&kp);
        let subject = lct.lct_id();

        // Three distinct witnesses, each signs an Existence attestation.
        let w: Vec<_> = (0..3).map(|_| KeyPair::generate()).collect();
        let wid: Vec<String> = (0..3).map(|i| format!("lct:web4:witness:{i}")).collect();
        let ts = lct.created_at;
        for i in 0..3 {
            lct.attestations.push(Attestation::sign(&subject, wid[i].clone(), AttestationType::Existence, ts, &w[i]));
        }
        lct.birth_certificate = Some(BirthCertificate {
            issuing_society: "lct:web4:society:hub".into(),
            citizen_role: "lct:web4:role:citizen".into(),
            birth_witnesses: wid.clone(),
            birth_timestamp: ts,
            birth_context: Some(BirthContext::Ecosystem),
            genesis_block_hash: None,
        });
        // The permanent citizen pairing (§4.2 clause 2).
        lct.mrh.paired.push(MrhEdge {
            lct_id: "lct:web4:role:citizen".into(),
            edge_type: "birth_certificate".into(),
            ts,
        });

        let resolver = |id: &str| wid.iter().position(|x| x == id).map(|i| w[i].verifying_key());
        assert!(lct.verify_birth_certificate(resolver), "well-formed cert verifies");
        assert!(!lct.is_self_issued());

        // Fail-closed mutations, each independently:
        // (a) a witness key that doesn't resolve → reject
        assert!(!lct.verify_birth_certificate(|_| None));
        // (b) drop below quorum
        let mut two = lct.clone();
        two.birth_certificate.as_mut().unwrap().birth_witnesses.truncate(2);
        assert!(!two.verify_birth_certificate(resolver));
        // (c) tamper an attestation ts → its signature no longer verifies
        let mut tampered = lct.clone();
        tampered.attestations[0].ts = ts + chrono::Duration::seconds(1);
        assert!(!tampered.verify_birth_certificate(resolver));
        // (d) missing the permanent pairing → reject
        let mut nopair = lct.clone();
        nopair.mrh.paired.clear();
        assert!(!nopair.verify_birth_certificate(resolver));
        // (e) no birth_certificate at all → false AND is_self_issued true
        let mut regular = lct.clone();
        regular.birth_certificate = None;
        assert!(!regular.verify_birth_certificate(resolver));
        assert!(regular.is_self_issued());
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
