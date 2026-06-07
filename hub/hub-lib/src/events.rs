// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Chapter event types.
//!
//! These are the *domain* events a chapter records — distinct from
//! `web4_core::ledger::LedgerEvent` which is about LCT anchoring (mint /
//! status-change). The hub's ChapterLedger records the chapter's social
//! and governance actions on top of (and alongside) any LCT anchoring
//! that web4-core handles.
//!
//! Each event variant captures who/what/when for one consequential
//! chapter action. The Sovereign signs Genesis. Subsequent events are
//! signed by the actor whose LCT id is named in the enclosing
//! `LedgerEntry::actor_lct_id`.
//!
//! Reusing `web4_core::role::SocietyRole` for the RoleAssigned variant —
//! no hub-side redefinition.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use web4_core::role::SocietyRole;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ChapterEvent {
    /// First entry in any chapter ledger. Established at chapter init.
    Genesis {
        chapter_name: String,
        charter_hash: String,
        founding_sovereign_lct_id: Uuid,
        created_at: DateTime<Utc>,
    },

    /// A member's LCT was registered as a chapter Citizen.
    MemberAdded {
        member_lct_id: Uuid,
        added_by: Uuid,
        member_name: Option<String>,
    },

    /// A member's Citizen status was revoked.
    MemberRemoved {
        member_lct_id: Uuid,
        removed_by: Uuid,
        reason: Option<String>,
    },

    /// A role assignment was changed.
    RoleAssigned {
        role: SocietyRole,
        role_lct_id: Uuid,
        assigned_to: Uuid,
        assigned_by: Uuid,
    },

    /// A chapter event was held + recorded (demo night, workshop, etc.).
    EventRecorded {
        event_kind: String,
        title: String,
        attended_by: Vec<Uuid>,
        recorded_by: Uuid,
        held_at: DateTime<Utc>,
    },

    /// The chapter charter was amended. `new_charter_hash` is the post-amendment
    /// hash. Must be signed by the Sovereign.
    CharterAmended {
        new_charter_hash: String,
        amended_by: Uuid,
        diff_summary: Option<String>,
    },
}

impl ChapterEvent {
    /// Short human-readable kind name — matches the serde tag.
    pub fn kind(&self) -> &'static str {
        match self {
            Self::Genesis { .. } => "genesis",
            Self::MemberAdded { .. } => "member_added",
            Self::MemberRemoved { .. } => "member_removed",
            Self::RoleAssigned { .. } => "role_assigned",
            Self::EventRecorded { .. } => "event_recorded",
            Self::CharterAmended { .. } => "charter_amended",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kind_strings_match_serde_tags() {
        let g = ChapterEvent::Genesis {
            chapter_name: "X".into(),
            charter_hash: "sha256:0".into(),
            founding_sovereign_lct_id: Uuid::nil(),
            created_at: Utc::now(),
        };
        assert_eq!(g.kind(), "genesis");

        let json = serde_json::to_string(&g).unwrap();
        assert!(json.contains("\"kind\":\"genesis\""));
    }

    #[test]
    fn role_assigned_uses_upstream_role_enum() {
        let e = ChapterEvent::RoleAssigned {
            role: SocietyRole::Treasurer,
            role_lct_id: Uuid::new_v4(),
            assigned_to: Uuid::new_v4(),
            assigned_by: Uuid::new_v4(),
        };
        let json = serde_json::to_string(&e).unwrap();
        assert!(json.contains("\"role\":\"treasurer\""));
    }
}
