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
- JSON-LD serialization roundtrips (DictionarySpec, TranslationResult,
  TranslationChain, DictionaryEntity)
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


# ── JSON-LD Serialization Tests ──────────────────────────────────

class TestDictionarySpecJsonLd:
    """DictionarySpec JSON-LD roundtrip tests."""

    def test_minimal_spec_roundtrip(self):
        spec = DictionarySpec(source_domain="medical", target_domain="legal")
        doc = spec.to_jsonld()
        assert doc["@type"] == "DictionarySpec"
        assert doc["@context"] == ["https://web4.io/contexts/dictionary.jsonld"]
        assert doc["source_domain"] == "medical"
        assert doc["target_domain"] == "legal"
        assert doc["bidirectional"] is True
        assert doc["dictionary_type"] == "domain"
        # Coverage and compression omitted when default
        assert "coverage" not in doc
        assert "compression" not in doc
        restored = DictionarySpec.from_jsonld(doc)
        assert restored.source_domain == spec.source_domain
        assert restored.target_domain == spec.target_domain
        assert restored.bidirectional == spec.bidirectional

    def test_full_spec_roundtrip(self):
        spec = DictionarySpec(
            source_domain="python",
            target_domain="rust",
            bidirectional=False,
            version="2.1.0",
            coverage=DomainCoverage(terms=500, concepts=120, relationships=80),
            compression=CompressionProfile(
                average_ratio=0.7,
                lossy_threshold=0.05,
                context_required="full",
                ambiguity_handling=AmbiguityHandling.DETERMINISTIC,
            ),
            dictionary_type=DictionaryType.MODEL,
        )
        doc = spec.to_jsonld()
        assert doc["coverage"]["terms"] == 500
        assert doc["compression"]["ambiguity_handling"] == "deterministic"
        assert doc["dictionary_type"] == "model"
        restored = DictionarySpec.from_jsonld(doc)
        assert restored.version == "2.1.0"
        assert restored.coverage.concepts == 120
        assert restored.compression.context_required == "full"
        assert restored.dictionary_type == DictionaryType.MODEL
        assert not restored.bidirectional

    def test_spec_string_roundtrip(self):
        spec = DictionarySpec(source_domain="a", target_domain="b")
        s = spec.to_jsonld_string()
        restored = DictionarySpec.from_jsonld_string(s)
        assert restored.source_domain == "a"


class TestTranslationResultJsonLd:
    """TranslationResult JSON-LD roundtrip tests."""

    def test_basic_result_roundtrip(self):
        result = TranslationResult(
            content="translated text",
            confidence=0.95,
            degradation=0.05,
            dictionary_lct_id="lct:web4:dict:med-legal-001",
            witness_required=False,
            timestamp="2026-03-23T12:00:00+00:00",
        )
        doc = result.to_jsonld()
        assert doc["@type"] == "TranslationResult"
        assert doc["content"] == "translated text"
        assert doc["confidence"] == 0.95
        assert doc["degradation"] == 0.05
        assert doc["witness_required"] is False
        assert "witness_lct_ids" not in doc  # empty list omitted
        restored = TranslationResult.from_jsonld(doc)
        assert restored.content == result.content
        assert restored.confidence == result.confidence
        assert restored.dictionary_lct_id == result.dictionary_lct_id

    def test_result_with_witnesses(self):
        result = TranslationResult(
            content="reviewed translation",
            confidence=0.88,
            degradation=0.12,
            dictionary_lct_id="lct:web4:dict:001",
            witness_required=True,
            witness_lct_ids=["lct:web4:witness:a", "lct:web4:witness:b"],
            timestamp="2026-03-23T12:00:00+00:00",
        )
        doc = result.to_jsonld()
        assert doc["witness_required"] is True
        assert len(doc["witness_lct_ids"]) == 2
        restored = TranslationResult.from_jsonld(doc)
        assert restored.witness_required is True
        assert restored.witness_lct_ids == ["lct:web4:witness:a", "lct:web4:witness:b"]

    def test_result_string_roundtrip(self):
        result = TranslationResult(
            content="test", confidence=0.9, degradation=0.1,
            dictionary_lct_id="lct:001",
            timestamp="2026-03-23T12:00:00+00:00",
        )
        s = result.to_jsonld_string()
        restored = TranslationResult.from_jsonld_string(s)
        assert restored.confidence == 0.9


class TestTranslationChainJsonLd:
    """TranslationChain JSON-LD roundtrip tests."""

    def test_empty_chain_roundtrip(self):
        chain = TranslationChain()
        doc = chain.to_jsonld()
        assert doc["@type"] == "TranslationChain"
        assert doc["steps"] == []
        assert doc["cumulative_confidence"] == 1.0
        assert doc["cumulative_degradation"] == 0.0
        assert doc["length"] == 0
        restored = TranslationChain.from_jsonld(doc)
        assert restored.length == 0
        assert restored.cumulative_confidence == 1.0

    def test_multi_step_chain_roundtrip(self):
        chain = TranslationChain()
        chain.add_step("medical", "scientific", "lct:dict:001", 0.95)
        chain.add_step("scientific", "legal", "lct:dict:002", 0.92)
        doc = chain.to_jsonld()
        assert len(doc["steps"]) == 2
        assert doc["steps"][0]["source_domain"] == "medical"
        assert doc["steps"][1]["dictionary_lct_id"] == "lct:dict:002"
        assert abs(doc["cumulative_confidence"] - 0.95 * 0.92) < 1e-10
        assert doc["length"] == 2
        restored = TranslationChain.from_jsonld(doc)
        assert restored.length == 2
        assert abs(restored.cumulative_confidence - 0.95 * 0.92) < 1e-10
        assert restored.steps[0].source_domain == "medical"
        assert restored.steps[1].confidence == 0.92

    def test_chain_with_witnesses(self):
        chain = TranslationChain(witness_lct_ids=["lct:w1", "lct:w2"])
        chain.add_step("a", "b", "lct:d1", 0.9)
        doc = chain.to_jsonld()
        assert doc["witness_lct_ids"] == ["lct:w1", "lct:w2"]
        restored = TranslationChain.from_jsonld(doc)
        assert restored.witness_lct_ids == ["lct:w1", "lct:w2"]

    def test_chain_string_roundtrip(self):
        chain = TranslationChain()
        chain.add_step("x", "y", "lct:d1", 0.85)
        s = chain.to_jsonld_string()
        restored = TranslationChain.from_jsonld_string(s)
        assert restored.steps[0].confidence == 0.85


class TestDictionaryEntityJsonLd:
    """DictionaryEntity JSON-LD roundtrip tests."""

    def test_basic_entity_roundtrip(self):
        entity = DictionaryEntity.create(
            source_domain="medical",
            target_domain="legal",
            public_key="mb64key",
        )
        doc = entity.to_jsonld()
        assert doc["@type"] == "DictionaryEntity"
        assert doc["@context"] == ["https://web4.io/contexts/dictionary.jsonld"]
        assert "lct_id" in doc
        assert doc["spec"]["source_domain"] == "medical"
        assert doc["spec"]["target_domain"] == "legal"
        assert doc["translation_count"] == 0
        assert doc["success_rate"] == 0.0
        restored = DictionaryEntity.from_jsonld(doc, public_key="mb64key")
        assert restored.spec.source_domain == "medical"
        assert restored.spec.target_domain == "legal"
        assert restored.translation_count == 0

    def test_entity_with_translations_roundtrip(self):
        entity = DictionaryEntity.create(
            source_domain="python",
            target_domain="rust",
            public_key="key1",
            version="2.0.0",
            coverage=DomainCoverage(terms=100, concepts=50, relationships=30),
            dictionary_type=DictionaryType.MODEL,
        )
        # Record some translations
        req = TranslationRequest(
            source_content="def foo():",
            source_domain="python",
            target_domain="rust",
        )
        entity.record_translation(req, "fn foo()", 0.95)
        entity.record_translation(req, "fn bar()", 0.85)
        doc = entity.to_jsonld()
        assert doc["translation_count"] == 2
        assert doc["successful_translations"] == 1  # only 0.95 >= 0.9
        assert doc["success_rate"] == 0.5
        assert doc["current_version"] == "2.0.0"
        assert doc["spec"]["coverage"]["terms"] == 100

    def test_entity_spec_inline_no_context_type(self):
        """Spec inside DictionaryEntity should NOT have @context/@type."""
        entity = DictionaryEntity.create(
            source_domain="a", target_domain="b", public_key="k",
        )
        doc = entity.to_jsonld()
        assert "@context" not in doc["spec"]
        assert "@type" not in doc["spec"]

    def test_entity_string_roundtrip(self):
        entity = DictionaryEntity.create(
            source_domain="en", target_domain="fr", public_key="k",
        )
        s = entity.to_jsonld_string()
        restored = DictionaryEntity.from_jsonld_string(s)
        assert restored.spec.source_domain == "en"
