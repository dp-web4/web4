//! Language bindings
//!
//! This module contains bindings for other languages:
//! - Python (via PyO3) - when `python` feature is enabled
//! - WASM (via wasm-bindgen) - when `wasm` feature is enabled

#[cfg(feature = "python")]
pub mod python;

#[cfg(feature = "python")]
pub use python::*;

#[cfg(feature = "wasm")]
mod wasm;
