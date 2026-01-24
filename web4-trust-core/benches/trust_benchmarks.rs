//! Trust operation benchmarks

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use web4_trust_core::{EntityTrust, T3Tensor};
use web4_trust_core::storage::{InMemoryStore, TrustStore};

fn tensor_average(c: &mut Criterion) {
    let t3 = T3Tensor::neutral();

    c.bench_function("t3_average", |b| {
        b.iter(|| black_box(t3.average()))
    });
}

fn tensor_update(c: &mut Criterion) {
    c.bench_function("t3_update_from_outcome", |b| {
        let mut t3 = T3Tensor::neutral();
        b.iter(|| {
            t3.update_from_outcome(black_box(true), black_box(0.1));
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
