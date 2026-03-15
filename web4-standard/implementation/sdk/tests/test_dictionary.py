"""
Test web4.dictionary module — Dictionary Entities.

Tests verify:
- DictionarySpec domain coverage (forward, reverse, unrelated)
- DictionaryEntity creation with LCT, domain bindings, capabilities
- Translation recording with confidence/degradation tracking
- TranslationChain multiplicative degradation (spec §4.3)
- Chain acceptability threshold checking
- Dictionary evolution: versioning, feedback processing
- Feedback updates trust tensors (corrections lower, validations raise)
- Dictionary selection scoring (spec §6.2)
- select_best_dictionary filters and ranks candidates
- Test vector validation (dict-001 through dict-005)
"""

import json
import os
import pytest

from web4.dictionary import (
    DictionaryEntity,
    DictionarySpec,
    DictionaryType,
    DomainCoverage,
    CompressionProfile,
    AmbiguityHandling,
    TranslationRequest,
    TranslationResult,
    TranslationChain,
    ChainStep,
    EvolutionConfig,
    DictionaryVersion,
    FeedbackRecord,
    dictionary_selection_score,
    select_best_dictionary,
    SELECTION_WEIGHT_TRUST,
    SELECTION_WEIGHT_COVERAGE,
    SELECTION_WEIGHT_RECENCY,
    SELECTION_WEIGHT_COST,
)
from web4.lct import EntityType
from web4.trust import T3, V3


# ── DictionarySpec ───────────────────────────────────────────────

class TestDictionarySpec:

    def test_covers_forward(self):
        spec = DictionarySpec(source_domain="medical", target_domain="legal")
        assert spec.covers_domains("medical", "legal")

    def test_covers_reverse_when_bidirectional(self):
        spec = DictionarySpec(source_domain="medical", target_domain="legal", bidirectional=True)
        assert spec.covers_domains("legal", "medical")

    def test_no_reverse_when_unidirectional(self):
        spec = DictionarySpec(source_domain="medical", target_domain="legal", bidirectional=False)
        assert not spec.covers_domains("legal", "medical")

    def test_no_coverage_for_unrelated(self):
        spec = DictionarySpec(source_domain="medical", target_domain="legal")
        assert not spec.covers_domains("engineering", "business")

    def test_spec_type_default(self):
        spec = DictionarySpec(source_domain="a", target_domain="b")
        assert spec.dictionary_type == DictionaryType.DOMAIN

    def test_meta_dictionary_type(self):
        spec = DictionarySpec(
            source_domain="dict_a", target_domain="dict_b",
            dictionary_type=DictionaryType.META,
        )
        assert spec.dictionary_type == DictionaryType.META


# ── DictionaryEntity Creation ────────────────────────────────────

class TestDictionaryEntityCreation:

    def test_create_basic(self):
        d = DictionaryEntity.create(
            source_domain="medical",
            target_domain="legal",
            public_key="mb64testkey",
        )
        assert d.lct.binding.entity_type == EntityType.DICTIONARY
        assert d.spec.source_domain == "medical"
        assert d.spec.target_domain == "legal"
        assert d.lct.is_active

    def test_domain_bindings_in_mrh(self):
        d = DictionaryEntity.create(
            source_domain="medical",
            target_domain="legal",
            public_key="mb64testkey",
        )
        assert "lct:web4:domain:medical" in d.lct.mrh.bound
        assert "lct:web4:domain:legal" in d.lct.mrh.bound

    def test_capabilities(self):
        d = DictionaryEntity.create(
            source_domain="medical",
            target_domain="legal",
            public_key="mb64testkey",
        )
        caps = d.lct.policy.capabilities
        assert "translate" in caps
        assert "evolve" in caps
        assert "witness_translations" in caps

    def test_initial_version(self):
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1", version="2.3.1",
        )
        assert d.current_version == "2.3.1"
        assert len(d.versions) == 1

    def test_custom_t3_v3(self):
        t3 = T3(talent=0.8, training=0.9, temperament=0.85)
        v3 = V3(valuation=0.7, veracity=0.8, validity=0.9)
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1", t3=t3, v3=v3,
        )
        assert d.t3.talent == 0.8
        assert d.v3.validity == 0.9

    def test_lct_id_shortcut(self):
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1",
        )
        assert d.lct_id == d.lct.lct_id

    def test_can_translate(self):
        d = DictionaryEntity.create(
            source_domain="medical", target_domain="legal",
            public_key="key1",
        )
        assert d.can_translate("medical", "legal")
        assert d.can_translate("legal", "medical")  # bidirectional by default
        assert not d.can_translate("engineering", "business")


# ── Translation Recording ────────────────────────────────────────

class TestTranslationRecording:

    def test_record_translation(self):
        d = DictionaryEntity.create(
            source_domain="medical", target_domain="legal",
            public_key="key1",
        )
        req = TranslationRequest(
            source_content="acute MI",
            source_domain="medical",
            target_domain="legal",
        )
        result = d.record_translation(req, "heart attack", 0.95)
        assert result.confidence == 0.95
        assert abs(result.degradation - 0.05) < 0.001
        assert result.dictionary_lct_id == d.lct_id
        assert d.translation_count == 1
        assert d.successful_translations == 1

    def test_low_confidence_requires_witness(self):
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1",
        )
        req = TranslationRequest(source_content="x", source_domain="a", target_domain="b")
        result = d.record_translation(req, "y", 0.80)
        assert result.witness_required  # < 0.95 → witness required

    def test_explicit_witness_requirement(self):
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1",
        )
        req = TranslationRequest(
            source_content="x", source_domain="a", target_domain="b",
            require_witness=True,
        )
        result = d.record_translation(req, "y", 0.99)
        assert result.witness_required  # request.require_witness overrides

    def test_success_rate_tracking(self):
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1",
        )
        req = TranslationRequest(
            source_content="x", source_domain="a", target_domain="b",
            minimum_fidelity=0.9,
        )
        d.record_translation(req, "y1", 0.95)
        d.record_translation(req, "y2", 0.80)  # below minimum_fidelity
        assert d.success_rate == 0.5

    def test_witnesses_added_to_mrh(self):
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1",
        )
        req = TranslationRequest(source_content="x", source_domain="a", target_domain="b")
        d.record_translation(req, "y", 0.95, witness_lct_ids=["lct:web4:witness:w1"])
        assert "lct:web4:witness:w1" in d.lct.mrh.witnessing


# ── Translation Chain ────────────────────────────────────────────

class TestTranslationChain:

    def test_empty_chain(self):
        chain = TranslationChain()
        assert chain.cumulative_confidence == 1.0
        assert chain.cumulative_degradation == 0.0
        assert chain.length == 0

    def test_two_hop_degradation(self):
        """Test vector dict-001: medical→legal→insurance."""
        chain = TranslationChain()
        chain.add_step("medical", "legal", "lct:dict:med-legal", 0.95)
        chain.add_step("legal", "insurance", "lct:dict:legal-ins", 0.92)
        assert abs(chain.cumulative_confidence - 0.874) < 0.001
        assert abs(chain.cumulative_degradation - 0.126) < 0.001
        assert chain.length == 2

    def test_three_hop_below_threshold(self):
        """Test vector dict-003: three hops drops below 0.8."""
        chain = TranslationChain()
        chain.add_step("medical", "legal", "d1", 0.95)
        chain.add_step("legal", "insurance", "d2", 0.92)
        chain.add_step("insurance", "regulatory", "d3", 0.90)
        assert abs(chain.cumulative_confidence - 0.7866) < 0.001
        assert not chain.is_acceptable(0.8)

    def test_single_step_confidence(self):
        chain = TranslationChain()
        chain.add_step("a", "b", "d1", 0.97)
        assert abs(chain.cumulative_confidence - 0.97) < 0.001
        assert chain.is_acceptable(0.9)

    def test_step_numbering(self):
        chain = TranslationChain()
        s1 = chain.add_step("a", "b", "d1", 0.9)
        s2 = chain.add_step("b", "c", "d2", 0.9)
        assert s1.step == 1
        assert s2.step == 2


# ── Dictionary Evolution ─────────────────────────────────────────

class TestDictionaryEvolution:

    def test_feedback_correction_lowers_trust(self):
        """Test vector dict-005: corrections decrease composite."""
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1",
        )
        initial_composite = d.t3.composite
        feedback = FeedbackRecord(
            feedback_type="correction",
            mapping_id="m1",
            success=False,
            corrector_lct_id="lct:expert",
        )
        d.apply_feedback(feedback)
        assert d.t3.composite < initial_composite

    def test_feedback_validation_raises_trust(self):
        """Test vector dict-005: validations increase composite."""
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1",
        )
        initial_composite = d.t3.composite
        feedback = FeedbackRecord(
            feedback_type="validation",
            mapping_id="m1",
            success=True,
        )
        d.apply_feedback(feedback)
        assert d.t3.composite > initial_composite

    def test_version_creation(self):
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1", version="1.0.0",
        )
        v = d.create_new_version("1.1.0", changelog="Added 50 terms")
        assert d.current_version == "1.1.0"
        assert v.parent_version == "1.0.0"
        assert len(d.versions) == 2

    def test_feedback_history(self):
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1",
        )
        d.apply_feedback(FeedbackRecord(feedback_type="correction", mapping_id="m1"))
        d.apply_feedback(FeedbackRecord(feedback_type="validation", mapping_id="m2", success=True))
        assert len(d.feedback_history) == 2


# ── Dictionary Selection ─────────────────────────────────────────

class TestDictionarySelection:

    def test_selection_score(self):
        """Test vector dict-002."""
        score = dictionary_selection_score(
            trust_composite=0.85,
            coverage_ratio=0.90,
            recency_score=0.75,
            cost_score=1.0,
        )
        expected = 0.4 * 0.85 + 0.3 * 0.90 + 0.2 * 0.75 + 0.1 * 1.0
        assert abs(score - expected) < 0.001

    def test_selection_score_weights_sum_to_one(self):
        total = (SELECTION_WEIGHT_TRUST + SELECTION_WEIGHT_COVERAGE
                 + SELECTION_WEIGHT_RECENCY + SELECTION_WEIGHT_COST)
        assert abs(total - 1.0) < 0.001

    def test_select_best_dictionary(self):
        d1 = DictionaryEntity.create(
            source_domain="medical", target_domain="legal",
            public_key="key1", t3=T3(talent=0.9, training=0.9, temperament=0.9),
        )
        d2 = DictionaryEntity.create(
            source_domain="medical", target_domain="legal",
            public_key="key2", t3=T3(talent=0.5, training=0.5, temperament=0.5),
        )
        best = select_best_dictionary(
            candidates=[d1, d2],
            source_domain="medical",
            target_domain="legal",
        )
        assert best is d1  # Higher trust → selected

    def test_select_filters_by_domain(self):
        d1 = DictionaryEntity.create(
            source_domain="medical", target_domain="legal",
            public_key="key1",
        )
        d2 = DictionaryEntity.create(
            source_domain="engineering", target_domain="business",
            public_key="key2",
        )
        best = select_best_dictionary(
            candidates=[d1, d2],
            source_domain="medical",
            target_domain="legal",
        )
        assert best is d1

    def test_select_no_eligible(self):
        d1 = DictionaryEntity.create(
            source_domain="engineering", target_domain="business",
            public_key="key1",
        )
        best = select_best_dictionary(
            candidates=[d1],
            source_domain="medical",
            target_domain="legal",
        )
        assert best is None

    def test_meets_trust_requirement(self):
        d = DictionaryEntity.create(
            source_domain="a", target_domain="b",
            public_key="key1", t3=T3(talent=0.8, training=0.9, temperament=0.85),
        )
        assert d.meets_trust_requirement(0.8)
        assert not d.meets_trust_requirement(0.95)
