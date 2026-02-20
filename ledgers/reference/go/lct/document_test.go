package lct

import (
	"encoding/json"
	"math"
	"testing"
)

// ═══════════════════════════════════════════════════════════════
// Test Fixtures
// ═══════════════════════════════════════════════════════════════

func minimalValidDoc() *Document {
	return &Document{
		LCTID:   "lct:web4:ai:test0000deadbeef",
		Subject: "did:web4:key:z6Mk1234567890",
		Binding: Binding{
			EntityType:   EntityAI,
			PublicKey:    "mb64testkey",
			CreatedAt:    "2026-02-19T00:00:00Z",
			BindingProof: "cose:test_proof",
		},
		BirthCert: BirthCertificate{
			IssuingSociety: "lct:web4:society:genesis",
			CitizenRole:    "lct:web4:role:citizen:ai",
			Context:        BirthPlatform,
			BirthTimestamp: "2026-02-19T00:00:00Z",
			BirthWitnesses: []string{"lct:web4:witness:w1", "lct:web4:witness:w2", "lct:web4:witness:w3"},
		},
		MRH: MRH{
			Bound: []MRHBound{},
			Paired: []MRHPaired{{
				LCTID:       "lct:web4:role:citizen:ai",
				PairingType: PairingBirthCertificate,
				Permanent:   true,
				TS:          "2026-02-19T00:00:00Z",
			}},
			Witnessing:   []MRHWitnessing{},
			HorizonDepth: 3,
			LastUpdated:  "2026-02-19T00:00:00Z",
		},
		Policy: Policy{
			Capabilities: []string{"witness:attest"},
		},
		T3: &T3Tensor{
			Talent:         0.5,
			Training:       0.5,
			Temperament:    0.5,
			CompositeScore: 0.5,
		},
		V3: &V3Tensor{
			Valuation:      0.0,
			Veracity:       0.5,
			Validity:       0.5,
			CompositeScore: 0.35,
		},
		Revocation: &Revocation{Status: RevocationActive},
	}
}

// ═══════════════════════════════════════════════════════════════
// Document Validation Tests
// ═══════════════════════════════════════════════════════════════

func TestValidateMinimalDocument(t *testing.T) {
	doc := minimalValidDoc()
	result := ValidateDocument(doc)
	if !result.Valid {
		t.Fatalf("Expected valid, got errors: %v", result.Errors)
	}
	t.Logf("Warnings: %v", result.Warnings)
}

func TestValidateDocumentInvalidLCTID(t *testing.T) {
	doc := minimalValidDoc()
	doc.LCTID = "bad-id"
	result := ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for bad lct_id")
	}
	found := false
	for _, e := range result.Errors {
		if contains(e, "lct_id") {
			found = true
		}
	}
	if !found {
		t.Errorf("Expected lct_id error, got: %v", result.Errors)
	}
}

func TestValidateDocumentInvalidSubject(t *testing.T) {
	doc := minimalValidDoc()
	doc.Subject = "not-a-did"
	result := ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for bad subject")
	}
}

func TestValidateDocumentInvalidEntityType(t *testing.T) {
	doc := minimalValidDoc()
	doc.Binding.EntityType = "alien"
	result := ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for bad entity_type")
	}
}

func TestValidateDocumentMissingBirthWitnesses(t *testing.T) {
	doc := minimalValidDoc()
	doc.BirthCert.BirthWitnesses = nil
	result := ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for missing birth witnesses")
	}
}

func TestValidateDocumentFewBirthWitnessesWarning(t *testing.T) {
	doc := minimalValidDoc()
	doc.BirthCert.BirthWitnesses = []string{"lct:web4:witness:w1"}
	result := ValidateDocument(doc)
	if !result.Valid {
		t.Fatalf("Expected valid (1 witness is minimum), got errors: %v", result.Errors)
	}
	found := false
	for _, w := range result.Warnings {
		if contains(w, "at least 3") {
			found = true
		}
	}
	if !found {
		t.Error("Expected warning about < 3 witnesses")
	}
}

func TestValidateDocumentMRHNoPaired(t *testing.T) {
	doc := minimalValidDoc()
	doc.MRH.Paired = nil
	result := ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for empty mrh.paired")
	}
}

func TestValidateDocumentMRHBadHorizonDepth(t *testing.T) {
	doc := minimalValidDoc()
	doc.MRH.HorizonDepth = 0
	result := ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for horizon_depth=0")
	}

	doc.MRH.HorizonDepth = 11
	result = ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for horizon_depth=11")
	}
}

func TestValidateDocumentNoCitizenPairingWarning(t *testing.T) {
	doc := minimalValidDoc()
	doc.MRH.Paired = []MRHPaired{{
		LCTID:       "lct:web4:role:worker",
		PairingType: PairingOperational,
		TS:          "2026-02-19T00:00:00Z",
	}}
	result := ValidateDocument(doc)
	if !result.Valid {
		t.Fatalf("Expected valid, got: %v", result.Errors)
	}
	found := false
	for _, w := range result.Warnings {
		if contains(w, "birth_certificate pairing") {
			found = true
		}
	}
	if !found {
		t.Error("Expected warning about missing citizen pairing")
	}
}

func TestValidateDocumentInvalidT3(t *testing.T) {
	doc := minimalValidDoc()
	doc.T3.Talent = 1.5
	result := ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for talent=1.5")
	}

	doc.T3.Talent = 0.5
	doc.T3.Training = -0.1
	result = ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for training=-0.1")
	}
}

func TestValidateDocumentInvalidV3(t *testing.T) {
	doc := minimalValidDoc()
	doc.V3.Valuation = -1.0
	result := ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for valuation=-1.0")
	}

	doc.V3.Valuation = 0.0
	doc.V3.Veracity = 2.0
	result = ValidateDocument(doc)
	if result.Valid {
		t.Fatal("Expected invalid for veracity=2.0")
	}
}

func TestValidateDocumentRevokedWarnings(t *testing.T) {
	doc := minimalValidDoc()
	doc.Revocation = &Revocation{Status: RevocationRevoked}
	result := ValidateDocument(doc)
	if !result.Valid {
		t.Fatalf("Expected valid, got: %v", result.Errors)
	}
	if len(result.Warnings) < 2 {
		t.Errorf("Expected at least 2 warnings for revoked without ts/reason, got %d", len(result.Warnings))
	}
}

// ═══════════════════════════════════════════════════════════════
// Tensor Operations Tests
// ═══════════════════════════════════════════════════════════════

func TestComputeT3Composite(t *testing.T) {
	t3 := &T3Tensor{Talent: 0.8, Training: 0.6, Temperament: 0.9}
	composite := ComputeT3Composite(t3)
	expected := 0.8*0.4 + 0.6*0.3 + 0.9*0.3 // 0.77
	if math.Abs(composite-expected) > 0.001 {
		t.Errorf("T3 composite: expected %.3f, got %.3f", expected, composite)
	}
}

func TestComputeV3Composite(t *testing.T) {
	v3 := &V3Tensor{Valuation: 0.5, Veracity: 0.8, Validity: 0.6}
	composite := ComputeV3Composite(v3)
	expected := 0.5*0.3 + 0.8*0.35 + 0.6*0.35 // 0.64
	if math.Abs(composite-expected) > 0.001 {
		t.Errorf("V3 composite: expected %.3f, got %.3f", expected, composite)
	}
}

func TestDefaultT3(t *testing.T) {
	t3 := DefaultT3()
	if t3.Talent != 0.5 || t3.Training != 0.5 || t3.Temperament != 0.5 {
		t.Error("DefaultT3 should have all 0.5 root dimensions")
	}
	if t3.CompositeScore != 0.5 {
		t.Errorf("DefaultT3 composite should be 0.5, got %f", t3.CompositeScore)
	}
}

func TestDefaultV3(t *testing.T) {
	v3 := DefaultV3()
	if v3.Valuation != 0.0 {
		t.Errorf("DefaultV3 valuation should be 0.0, got %f", v3.Valuation)
	}
	if v3.CompositeScore != 0.35 {
		t.Errorf("DefaultV3 composite should be 0.35, got %f", v3.CompositeScore)
	}
}

func TestMigrateT3FromLegacy6D(t *testing.T) {
	t3 := MigrateT3FromLegacy6D(0.8, 0.7, 0.6, 0.9, 0.5, 0.8)
	if t3.Talent != 0.8 {
		t.Errorf("talent should be 0.8 (= competence), got %f", t3.Talent)
	}
	expectedTraining := (0.7 + 0.6 + 0.5) / 3.0 // 0.6
	if math.Abs(t3.Training-expectedTraining) > 0.001 {
		t.Errorf("training should be %.3f, got %.3f", expectedTraining, t3.Training)
	}
	expectedTemperament := (0.9 + 0.8) / 2.0 // 0.85
	if math.Abs(t3.Temperament-expectedTemperament) > 0.001 {
		t.Errorf("temperament should be %.3f, got %.3f", expectedTemperament, t3.Temperament)
	}
}

func TestMigrateV3FromLegacy6D(t *testing.T) {
	v3 := MigrateV3FromLegacy6D(0.6, 0.4, 0.7, 0.5, 0.8, 0.3)
	expectedValuation := (0.6 + 0.4) / 2.0 // 0.5
	if math.Abs(v3.Valuation-expectedValuation) > 0.001 {
		t.Errorf("valuation should be %.3f, got %.3f", expectedValuation, v3.Valuation)
	}
	if v3.Veracity != 0.8 {
		t.Errorf("veracity should be 0.8 (= reputation), got %f", v3.Veracity)
	}
	expectedValidity := (0.7 + 0.5 + 0.3) / 3.0 // 0.5
	if math.Abs(v3.Validity-expectedValidity) > 0.001 {
		t.Errorf("validity should be %.3f, got %.3f", expectedValidity, v3.Validity)
	}
}

// ═══════════════════════════════════════════════════════════════
// JSON Serialization Tests
// ═══════════════════════════════════════════════════════════════

func TestDocumentJSONRoundtrip(t *testing.T) {
	doc := minimalValidDoc()

	data, err := json.Marshal(doc)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	var restored Document
	if err := json.Unmarshal(data, &restored); err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	// Verify key fields survive roundtrip
	assertEqual(t, "lct_id", doc.LCTID, restored.LCTID)
	assertEqual(t, "subject", doc.Subject, restored.Subject)
	assertEqual(t, "entity_type", string(doc.Binding.EntityType), string(restored.Binding.EntityType))
	assertEqual(t, "issuing_society", doc.BirthCert.IssuingSociety, restored.BirthCert.IssuingSociety)

	if restored.T3.Talent != 0.5 {
		t.Errorf("T3 talent should be 0.5, got %f", restored.T3.Talent)
	}
	if restored.V3.Veracity != 0.5 {
		t.Errorf("V3 veracity should be 0.5, got %f", restored.V3.Veracity)
	}

	// Validate restored document
	result := ValidateDocument(&restored)
	if !result.Valid {
		t.Errorf("Restored document invalid: %v", result.Errors)
	}
}

func TestDocumentHash(t *testing.T) {
	doc := minimalValidDoc()
	hash1 := doc.Hash()
	hash2 := doc.Hash()

	if hash1 != hash2 {
		t.Error("Same document should produce same hash")
	}
	if len(hash1) != 64 {
		t.Errorf("Expected 64-char SHA-256 hex, got %d chars", len(hash1))
	}

	// Different document → different hash
	doc2 := minimalValidDoc()
	doc2.LCTID = "lct:web4:ai:different"
	hash3 := doc2.Hash()
	if hash1 == hash3 {
		t.Error("Different documents should produce different hashes")
	}
}

func TestDocumentToURI(t *testing.T) {
	doc := minimalValidDoc()
	uri := doc.ToURI("testnet", "agent")
	if uri == "" {
		t.Fatal("ToURI returned empty string")
	}
	// Should be parseable
	result := ParseURI(uri)
	if !result.Success {
		t.Errorf("ToURI produced invalid URI: %v", result.Errors)
	}
}

// ═══════════════════════════════════════════════════════════════
// Entity Type Tests
// ═══════════════════════════════════════════════════════════════

func TestAllEntityTypesValid(t *testing.T) {
	for _, et := range ValidEntityTypes {
		if !isValidEntityType(et) {
			t.Errorf("Entity type %q should be valid", et)
		}
	}
}

func TestEntityTypeCount(t *testing.T) {
	if len(ValidEntityTypes) != 15 {
		t.Errorf("Expected 15 entity types (spec), got %d", len(ValidEntityTypes))
	}
}

func TestInvalidEntityType(t *testing.T) {
	if isValidEntityType("alien") {
		t.Error("'alien' should not be a valid entity type")
	}
}

// ═══════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsSubstring(s, substr))
}

func containsSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
