package lct

import (
	"testing"
)

func TestBuilderMinimal(t *testing.T) {
	doc, err := NewBuilder(EntityAI, "test-agent").
		WithBinding("mb64testkey", "cose:proof").
		WithBirthCertificate(
			"lct:web4:society:test",
			"lct:web4:role:citizen:ai",
			BirthPlatform,
			[]string{"lct:web4:witness:w1", "lct:web4:witness:w2", "lct:web4:witness:w3"},
		).
		AddCapability("witness:attest").
		Build()

	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}

	if doc.Binding.EntityType != EntityAI {
		t.Errorf("Expected EntityAI, got %q", doc.Binding.EntityType)
	}

	// Should have citizen pairing from birth certificate
	hasCitizenPairing := false
	for _, p := range doc.MRH.Paired {
		if p.PairingType == PairingBirthCertificate && p.Permanent {
			hasCitizenPairing = true
		}
	}
	if !hasCitizenPairing {
		t.Error("Expected permanent citizen pairing from birth certificate")
	}
}

func TestBuilderWithTensors(t *testing.T) {
	doc, err := NewBuilder(EntityHuman, "researcher").
		WithBinding("mb64key", "cose:proof").
		WithBirthCertificate(
			"lct:web4:society:lab",
			"lct:web4:role:citizen:human",
			BirthOrganization,
			[]string{"lct:web4:witness:w1", "lct:web4:witness:w2", "lct:web4:witness:w3"},
		).
		WithT3(0.8, 0.7, 0.9).
		WithV3(0.5, 0.8, 0.6).
		AddCapability("write:lct").
		Build()

	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}

	if doc.T3 == nil {
		t.Fatal("T3 tensor should be set")
	}
	if doc.T3.Talent != 0.8 {
		t.Errorf("T3 talent: expected 0.8, got %f", doc.T3.Talent)
	}

	// Check composite was computed
	expected := 0.8*0.4 + 0.7*0.3 + 0.9*0.3
	if abs(doc.T3.CompositeScore-expected) > 0.001 {
		t.Errorf("T3 composite: expected %.3f, got %.3f", expected, doc.T3.CompositeScore)
	}

	if doc.V3 == nil {
		t.Fatal("V3 tensor should be set")
	}
	if doc.V3.Valuation != 0.5 {
		t.Errorf("V3 valuation: expected 0.5, got %f", doc.V3.Valuation)
	}
}

func TestBuilderWithMRH(t *testing.T) {
	doc, err := NewBuilder(EntityDevice, "sensor-42").
		WithBinding("mb64key", "cose:proof").
		WithHardwareAnchor("eat:tpm2:attestation_token").
		WithBirthCertificate(
			"lct:web4:society:iot-net",
			"lct:web4:role:citizen:device",
			BirthNetwork,
			[]string{"lct:web4:witness:gateway", "lct:web4:witness:hub", "lct:web4:witness:controller"},
		).
		AddBound("lct:web4:device:gateway", BoundParent).
		AddPairing("lct:web4:service:telemetry", PairingOperational, false).
		AddWitness("lct:web4:oracle:time-server", WitnessTime).
		AddCapability("read:sensor").
		Build()

	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}

	if len(doc.MRH.Bound) != 1 {
		t.Errorf("Expected 1 bound, got %d", len(doc.MRH.Bound))
	}
	if doc.MRH.Bound[0].Type != BoundParent {
		t.Errorf("Expected parent bound type")
	}

	// 2 pairings: citizen (from birth cert) + operational
	if len(doc.MRH.Paired) != 2 {
		t.Errorf("Expected 2 pairings, got %d", len(doc.MRH.Paired))
	}

	if len(doc.MRH.Witnessing) != 1 {
		t.Errorf("Expected 1 witness, got %d", len(doc.MRH.Witnessing))
	}

	if doc.Binding.HardwareAnchor != "eat:tpm2:attestation_token" {
		t.Error("Hardware anchor not set")
	}
}

func TestBuilderWithLineage(t *testing.T) {
	doc := NewBuilder(EntityAI, "agent-v2").
		AddLineage(LineageGenesis, "").
		AddLineage(LineageUpgrade, "lct:web4:ai:agent-v1").
		BuildUnsafe()

	if len(doc.Lineage) != 2 {
		t.Errorf("Expected 2 lineage entries, got %d", len(doc.Lineage))
	}
	if doc.Lineage[0].Reason != LineageGenesis {
		t.Error("First lineage should be genesis")
	}
	if doc.Lineage[1].Parent != "lct:web4:ai:agent-v1" {
		t.Error("Second lineage should reference parent")
	}
}

func TestBuilderValidationFailure(t *testing.T) {
	// Missing binding proof and birth certificate should fail
	_, err := NewBuilder(EntityAI, "invalid").Build()
	if err == nil {
		t.Fatal("Expected validation error for incomplete document")
	}
}

func TestBuilderUnsafeBypassesValidation(t *testing.T) {
	doc := NewBuilder(EntityAI, "partial").BuildUnsafe()
	if doc == nil {
		t.Fatal("BuildUnsafe should always return a document")
	}
	if doc.LCTID == "" {
		t.Error("LCTID should be set even in unsafe build")
	}
}

func TestBuilderAllEntityTypes(t *testing.T) {
	for _, et := range ValidEntityTypes {
		doc := NewBuilder(et, "test").BuildUnsafe()
		if doc.Binding.EntityType != et {
			t.Errorf("Entity type %q: expected %q in binding", et, et)
		}
	}
}

func TestBuilderProducesValidDocument(t *testing.T) {
	doc, err := NewBuilder(EntityAI, "full-featured").
		WithBinding("mb64fullkey", "cose:full_proof").
		WithBirthCertificate(
			"lct:web4:society:main",
			"lct:web4:role:citizen:ai",
			BirthPlatform,
			[]string{"lct:web4:witness:w1", "lct:web4:witness:w2", "lct:web4:witness:w3"},
		).
		WithT3(0.7, 0.8, 0.6).
		WithV3(0.3, 0.9, 0.7).
		AddCapability("write:lct").
		AddCapability("witness:attest").
		AddBound("lct:web4:society:main", BoundParent).
		AddWitness("lct:web4:oracle:time", WitnessTime).
		AddLineage(LineageGenesis, "").
		Build()

	if err != nil {
		t.Fatalf("Build failed: %v", err)
	}

	// Re-validate
	result := ValidateDocument(doc)
	if !result.Valid {
		t.Errorf("Document failed re-validation: %v", result.Errors)
	}

	// Check document can produce URI
	uri := doc.ToURI("testnet", "agent")
	parseResult := ParseURI(uri)
	if !parseResult.Success {
		t.Errorf("ToURI produced invalid URI: %v", parseResult.Errors)
	}
}

func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}
