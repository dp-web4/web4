//! Witnessing relationships and chains
//!
//! Witnessing is how trust flows between entities in Web4:
//! - When entity A witnesses entity B succeed, both accumulate trust
//! - B gains reliability (it worked)
//! - A gains alignment (its judgment was validated)

mod event;
mod chain;

pub use event::{WitnessEvent, WitnessNode};
pub use chain::WitnessingChain;
