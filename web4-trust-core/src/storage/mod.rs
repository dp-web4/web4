//! Storage backends for entity trust
//!
//! This module provides storage implementations:
//! - `InMemoryStore`: For testing and WASM environments
//! - `FileStore`: JSON files compatible with Python implementation

mod traits;
mod memory;

#[cfg(feature = "file-store")]
mod file;

pub use traits::TrustStore;
pub use memory::InMemoryStore;

#[cfg(feature = "file-store")]
pub use file::FileStore;
