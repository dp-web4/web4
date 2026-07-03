//! Trust operation benchmarks

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use web4_trust_core::tensor;
use web4_trust_core::{EntityTrust, T3};
use web4_trust_core::storage::{InMemoryStore, TrustStore};

fn tensor_average(c: &mut Criterion) {
    // P3b: benchmark the canonical `web4_core::t3::T3` via the shared ops.
    let t3 = T3::new();

    c.bench_function("t3_average", |b| {
        b.iter(|| black_box(tensor::t3_average(&t3)))
    });
}

fn tensor_update(c: &mut Criterion) {
    c.bench_function("t3_update_from_outcome", |b| {
        let mut t3 = T3::new();
        b.iter(|| {
            tensor::t3_update_from_outcome(&mut t3, black_box(true), black_box(0.1));
        })
    });
}

fn entity_trust_operations(c: &mut Criterion) {
    c.bench_function("entity_update_from_outcome", |b| {
        let mut trust = EntityTrust::new("mcp:test");
        b.iter(|| {
            trust.update_from_outcome(black_box(true), black_box(0.1));
        })
    });
}

fn store_operations(c: &mut Criterion) {
    let store = InMemoryStore::new();

    c.bench_function("store_get_or_create", |b| {
        b.iter(|| {
            store.get(black_box("mcp:test")).unwrap()
        })
    });

    c.bench_function("store_witness", |b| {
        b.iter(|| {
            store.witness(
                black_box("session:a"),
                black_box("mcp:test"),
                black_box(true),
                black_box(0.1)
            ).unwrap()
        })
    });
}

criterion_group!(benches, tensor_average, tensor_update, entity_trust_operations, store_operations);
criterion_main!(benches);
