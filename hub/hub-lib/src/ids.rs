// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! The two identifiers the hub used to call by one name (PRD_LCT_IDENTITY_CONVERGENCE, Slice A;
//! web4#875 H1).
//!
//! - [`HubMemberId`] — the hub's own UUID for a member: the stable membership and routing key,
//!   what the sealed channel authenticates against a pinned key, and what survives a key
//!   rotation. Historically named `member_lct_id` / `MY_LCT`. It is **membership evidence**, not
//!   the entity's Web4 presence.
//! - [`CanonicalLctId`] — the entity's canonical, key-derived Web4 presence id
//!   (`lct:web4:mb32:b…`, canon §2.3): what the registry keys on, and what MOVES when the binding
//!   key rotates.
//!
//! Both serialize exactly as before (`HubMemberId` as the bare UUID, `CanonicalLctId` as the
//! string), so this slice changes no wire format, no ledger event and no stored document. What
//! it changes is that code can no longer hand one where the other is meant without saying so:
//! there is deliberately no conversion between the two, no `From<Uuid>` into a member id, and no
//! way into a canonical id that skips validation (`TryFrom<String>`/`FromStr` run [`parse`]; the
//! only infallible conversion is OUT, to `String`). Every crossing in is a named call
//! ([`HubMemberId::from_uuid`], [`CanonicalLctId::parse`], [`CanonicalLctId::derive`]) that a
//! reader — and a grep — can find.
//!
//! [`parse`]: CanonicalLctId::parse
//!
//! The interchange the PRD names is refused by the COMPILER, not by convention. Each of these
//! fails to build (pinned as `compile_fail` doctests, so a later `From` impl that made one
//! compile would turn the doc build red):
//!
//! ```compile_fail
//! // a raw UUID does not silently become a member id
//! let m: hub_lib::ids::HubMemberId = uuid::Uuid::new_v4().into();
//! ```
//!
//! ```compile_fail
//! // a member id is not a canonical LCT
//! fn takes_presence(_: hub_lib::ids::CanonicalLctId) {}
//! takes_presence(hub_lib::ids::HubMemberId::from_uuid(uuid::Uuid::new_v4()));
//! ```
//!
//! ```compile_fail
//! // nor is any string: a canonical id is only reached through `parse` or `derive`
//! let c: hub_lib::ids::CanonicalLctId = String::from("lct:web4:mb32:b").into();
//! ```
//!
//! The explicit spellings do build:
//!
//! ```
//! let m = hub_lib::ids::HubMemberId::from_uuid(uuid::Uuid::new_v4());
//! let _raw: uuid::Uuid = m.as_uuid();
//! assert!(hub_lib::ids::CanonicalLctId::parse(&m.to_string()).is_err());
//! ```
//!
//! The derivation is web4-core's [`derive_lct_id`](web4_core::lct::derive_lct_id), the one
//! source; [`CanonicalLctId::parse`] accepts exactly the shape it produces. If the derivation
//! changes (web4#819 or a successor), those two are where it changes here.

use serde::{Deserialize, Serialize};
use std::fmt;
use uuid::Uuid;

/// The hub's membership/routing id for a member — not a canonical LCT. See the module doc.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(transparent)]
pub struct HubMemberId(Uuid);

impl HubMemberId {
    /// Name a hub member by its UUID. The explicit crossing from the raw wire/ledger form.
    pub const fn from_uuid(id: Uuid) -> Self {
        Self(id)
    }

    /// The raw UUID, for the wire/ledger boundary that still carries it (as `member_lct_id`).
    pub const fn as_uuid(&self) -> Uuid {
        self.0
    }
}

impl fmt::Display for HubMemberId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}

const CANONICAL_PREFIX: &str = "lct:web4:mb32:b";
/// sha256 is 32 bytes = 256 bits; RFC 4648 base32 without padding carries 5 bits per char.
const CANONICAL_BODY_LEN: usize = 52;

/// Why a string is not a canonical LCT id.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum NotCanonical {
    #[error("not a canonical LCT id: it does not start with `lct:web4:mb32:b` ({0:?})")]
    Prefix(String),
    #[error("not a canonical LCT id: the body is {0} characters, a sha256 in base32 is 52")]
    Length(usize),
    #[error("not a canonical LCT id: the body is not lowercase RFC 4648 base32 ({0:?})")]
    Charset(String),
}

/// An entity's canonical, key-derived Web4 presence id (`lct:web4:mb32:b…`). See the module doc.
#[derive(Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct CanonicalLctId(String);

impl CanonicalLctId {
    /// Accept a string only if it has exactly the derived shape. A UUID, a member name or a
    /// legacy label is refused: those resolve TO a canonical id (Slice B); they never ARE one.
    pub fn parse(s: &str) -> Result<Self, NotCanonical> {
        let body = s.strip_prefix(CANONICAL_PREFIX).ok_or_else(|| NotCanonical::Prefix(s.to_string()))?;
        if body.len() != CANONICAL_BODY_LEN {
            return Err(NotCanonical::Length(body.len()));
        }
        if !body.bytes().all(|b| b.is_ascii_lowercase() || (b'2'..=b'7').contains(&b)) {
            return Err(NotCanonical::Charset(body.to_string()));
        }
        Ok(Self(s.to_string()))
    }

    /// The canonical id a binding public key derives to.
    pub fn derive(key: &web4_core::crypto::PublicKey) -> Self {
        Self(web4_core::lct::derive_lct_id(key))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for CanonicalLctId {
    type Error = NotCanonical;
    fn try_from(s: String) -> Result<Self, Self::Error> {
        Self::parse(&s)
    }
}

impl From<CanonicalLctId> for String {
    fn from(id: CanonicalLctId) -> String {
        id.0
    }
}

impl std::str::FromStr for CanonicalLctId {
    type Err = NotCanonical;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::parse(s)
    }
}

impl fmt::Display for CanonicalLctId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::borrow::Borrow<str> for CanonicalLctId {
    /// Lets a registry keyed by `CanonicalLctId` be looked up by `&str` — a lookup by a string
    /// that is not canonical simply finds nothing, which is the registry's closed pole.
    fn borrow(&self) -> &str {
        &self.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use web4_core::crypto::KeyPair;

    #[test]
    fn derive_matches_web4_core_and_parses_back() {
        let k = KeyPair::generate().verifying_key();
        let id = CanonicalLctId::derive(&k);
        assert_eq!(id.as_str(), web4_core::lct::derive_lct_id(&k));
        assert_eq!(CanonicalLctId::parse(id.as_str()).unwrap(), id);
    }

    /// The interchange this slice exists to stop: a member UUID is never a canonical LCT.
    #[test]
    fn a_member_uuid_is_not_a_canonical_lct() {
        let member = Uuid::new_v4();
        assert!(matches!(CanonicalLctId::parse(&member.to_string()), Err(NotCanonical::Prefix(_))));
        assert!(matches!(CanonicalLctId::parse(&format!("lct:{member}")), Err(NotCanonical::Prefix(_))));
        assert!(CanonicalLctId::parse("hub-being").is_err(), "a roster name resolves to an id; it is not one");
    }

    #[test]
    fn only_the_exact_derived_shape_parses() {
        let good = CanonicalLctId::derive(&KeyPair::generate().verifying_key()).as_str().to_string();
        assert!(matches!(CanonicalLctId::parse(&good[..good.len() - 1]), Err(NotCanonical::Length(51))));
        assert!(matches!(CanonicalLctId::parse(&format!("{good}a")), Err(NotCanonical::Length(53))));
        let upper = format!("{CANONICAL_PREFIX}{}", good[CANONICAL_PREFIX.len()..].to_uppercase());
        assert!(matches!(CanonicalLctId::parse(&upper), Err(NotCanonical::Charset(_))));
        let digit = format!("{}1", &good[..good.len() - 1]); // '1' is not in the base32 alphabet
        assert!(matches!(CanonicalLctId::parse(&digit), Err(NotCanonical::Charset(_))));
    }

    /// No wire change: both serialize exactly as their raw forms did, and deserializing a
    /// canonical id runs the same validation as parse.
    #[test]
    fn the_wire_form_is_unchanged_and_validated() {
        let u = Uuid::new_v4();
        assert_eq!(serde_json::to_string(&HubMemberId::from_uuid(u)).unwrap(), serde_json::to_string(&u).unwrap());
        let back: HubMemberId = serde_json::from_str(&serde_json::to_string(&u).unwrap()).unwrap();
        assert_eq!(back.as_uuid(), u);

        let id = CanonicalLctId::derive(&KeyPair::generate().verifying_key());
        assert_eq!(serde_json::to_string(&id).unwrap(), serde_json::to_string(id.as_str()).unwrap());
        let ok: CanonicalLctId = serde_json::from_str(&serde_json::to_string(id.as_str()).unwrap()).unwrap();
        assert_eq!(ok, id);
        assert!(serde_json::from_str::<CanonicalLctId>(&serde_json::to_string(&u.to_string()).unwrap()).is_err(),
            "a UUID string must not deserialize into a canonical id");
    }

    /// A registry keyed by CanonicalLctId still answers a `&str` lookup.
    #[test]
    fn a_registry_keyed_by_canonical_id_answers_str_lookups() {
        let id = CanonicalLctId::derive(&KeyPair::generate().verifying_key());
        let mut m = std::collections::BTreeMap::new();
        m.insert(id.clone(), 1);
        assert_eq!(m.get(id.as_str()), Some(&1));
        assert_eq!(m.get("lct:web4:mb32:bnot-there"), None);
    }
}
