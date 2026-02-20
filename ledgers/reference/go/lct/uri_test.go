package lct

import (
	"strings"
	"testing"
)

// ═══════════════════════════════════════════════════════════════
// ParseURI Tests
// ═══════════════════════════════════════════════════════════════

func TestParseBasicURI(t *testing.T) {
	result := ParseURI("lct://sage:thinker:expert_42@testnet")
	if !result.Success {
		t.Fatalf("Expected success, got errors: %v", result.Errors)
	}

	id := result.Identity
	assertEqual(t, "component", "sage", id.Component)
	assertEqual(t, "instance", "thinker", id.Instance)
	assertEqual(t, "role", "expert_42", id.Role)
	assertEqual(t, "network", "testnet", id.Network)
	assertEqual(t, "version", "1.0.0", id.Version)
}

func TestParseURIWithQueryParams(t *testing.T) {
	uri := "lct://web4-agent:guardian:coordinator@mainnet?pairing_status=active&trust_threshold=0.75"
	result := ParseURI(uri)
	if !result.Success {
		t.Fatalf("Expected success, got errors: %v", result.Errors)
	}

	id := result.Identity
	assertEqual(t, "component", "web4-agent", id.Component)
	assertEqual(t, "instance", "guardian", id.Instance)
	assertEqual(t, "role", "coordinator", id.Role)
	assertEqual(t, "network", "mainnet", id.Network)

	if id.PairingStatus != PairingActive {
		t.Errorf("Expected PairingActive, got %q", id.PairingStatus)
	}
	if id.TrustThreshold != 0.75 {
		t.Errorf("Expected trust_threshold=0.75, got %f", id.TrustThreshold)
	}
}

func TestParseURIWithCapabilitiesAndFragment(t *testing.T) {
	uri := "lct://mcp:filesystem:reader@local?capabilities=read,list#did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
	result := ParseURI(uri)
	if !result.Success {
		t.Fatalf("Expected success, got errors: %v", result.Errors)
	}

	id := result.Identity
	assertEqual(t, "component", "mcp", id.Component)
	assertEqual(t, "instance", "filesystem", id.Instance)
	assertEqual(t, "role", "reader", id.Role)
	assertEqual(t, "network", "local", id.Network)

	if len(id.Capabilities) != 2 || id.Capabilities[0] != "read" || id.Capabilities[1] != "list" {
		t.Errorf("Expected capabilities=[read,list], got %v", id.Capabilities)
	}

	expectedKey := "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
	if id.PublicKeyHash != expectedKey {
		t.Errorf("Expected publicKeyHash=%q, got %q", expectedKey, id.PublicKeyHash)
	}
}

func TestParseURIWithVersion(t *testing.T) {
	result := ParseURI("lct://sage:thinker:expert@testnet?version=2.0.0")
	if !result.Success {
		t.Fatalf("Expected success, got errors: %v", result.Errors)
	}
	assertEqual(t, "version", "2.0.0", result.Identity.Version)
}

func TestParseURIInvalidScheme(t *testing.T) {
	result := ParseURI("http://sage:thinker:expert@testnet")
	if result.Success {
		t.Fatal("Expected failure for invalid scheme")
	}
	if !strings.Contains(result.Errors[0], "Invalid LCT URI scheme") {
		t.Errorf("Expected scheme error, got: %s", result.Errors[0])
	}
}

func TestParseURIInvalidAuthority(t *testing.T) {
	tests := []struct {
		name string
		uri  string
	}{
		{"missing role", "lct://sage:thinker@testnet"},
		{"missing network", "lct://sage:thinker:expert"},
		{"empty", "lct://"},
		{"no colons", "lct://sageonly@testnet"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ParseURI(tt.uri)
			if result.Success {
				t.Errorf("Expected failure for %q", tt.uri)
			}
		})
	}
}

func TestParseURIInvalidPairingStatus(t *testing.T) {
	result := ParseURI("lct://sage:thinker:expert@testnet?pairing_status=invalid")
	if result.Success {
		t.Fatal("Expected failure for invalid pairing_status")
	}
	if !strings.Contains(result.Errors[0], "Invalid pairing_status") {
		t.Errorf("Expected pairing_status error, got: %s", result.Errors[0])
	}
}

func TestParseURIInvalidTrustThreshold(t *testing.T) {
	tests := []string{
		"lct://sage:thinker:expert@testnet?trust_threshold=2.0",
		"lct://sage:thinker:expert@testnet?trust_threshold=-0.5",
		"lct://sage:thinker:expert@testnet?trust_threshold=abc",
	}

	for _, uri := range tests {
		result := ParseURI(uri)
		if result.Success {
			t.Errorf("Expected failure for %q", uri)
		}
	}
}

// ═══════════════════════════════════════════════════════════════
// BuildURI Tests
// ═══════════════════════════════════════════════════════════════

func TestBuildBasicURI(t *testing.T) {
	id := &Identity{
		Component: "sage",
		Instance:  "thinker",
		Role:      "expert_42",
		Network:   "testnet",
		Version:   "1.0.0",
		TrustThreshold: -1,
	}

	uri := BuildURI(id)
	assertEqual(t, "built URI", "lct://sage:thinker:expert_42@testnet", uri)
}

func TestBuildURIWithParams(t *testing.T) {
	id := &Identity{
		Component:      "web4-agent",
		Instance:       "guardian",
		Role:           "coordinator",
		Network:        "mainnet",
		Version:        "1.0.0",
		PairingStatus:  PairingActive,
		TrustThreshold: 0.75,
	}

	uri := BuildURI(id)
	if !strings.Contains(uri, "pairing_status=active") {
		t.Errorf("Expected pairing_status=active in URI: %s", uri)
	}
	if !strings.Contains(uri, "trust_threshold=0.75") {
		t.Errorf("Expected trust_threshold=0.75 in URI: %s", uri)
	}
}

func TestBuildURIWithFragment(t *testing.T) {
	id := &Identity{
		Component:     "mcp",
		Instance:      "filesystem",
		Role:          "reader",
		Network:       "local",
		Version:       "1.0.0",
		PublicKeyHash: "did:key:z6Mk1234",
		TrustThreshold: -1,
	}

	uri := BuildURI(id)
	if !strings.HasSuffix(uri, "#did:key:z6Mk1234") {
		t.Errorf("Expected fragment in URI: %s", uri)
	}
}

// ═══════════════════════════════════════════════════════════════
// Roundtrip Tests
// ═══════════════════════════════════════════════════════════════

func TestParseAndBuildRoundtrip(t *testing.T) {
	uris := []string{
		"lct://sage:thinker:expert_42@testnet",
		"lct://mcp:filesystem:reader@local#did:key:z6Mk1234",
	}

	for _, original := range uris {
		result := ParseURI(original)
		if !result.Success {
			t.Fatalf("Failed to parse %q: %v", original, result.Errors)
		}
		rebuilt := BuildURI(result.Identity)
		if rebuilt != original {
			t.Errorf("Roundtrip mismatch: %q → %q", original, rebuilt)
		}
	}
}

// ═══════════════════════════════════════════════════════════════
// ValidateURI Tests
// ═══════════════════════════════════════════════════════════════

func TestValidateURIValid(t *testing.T) {
	result := ValidateURI("lct://sage:thinker:expert@testnet")
	if !result.Valid {
		t.Fatalf("Expected valid, got errors: %v", result.Errors)
	}
}

func TestValidateURILocalWithoutKeyWarning(t *testing.T) {
	result := ValidateURI("lct://sage:thinker:expert@local")
	if !result.Valid {
		t.Fatal("Expected valid")
	}
	if len(result.Warnings) == 0 {
		t.Error("Expected warning for local network without public key hash")
	}
}

func TestValidateURILowTrustWarning(t *testing.T) {
	result := ValidateURI("lct://sage:thinker:expert@testnet?trust_threshold=0.1")
	if !result.Valid {
		t.Fatal("Expected valid")
	}
	found := false
	for _, w := range result.Warnings {
		if strings.Contains(w, "Low trust threshold") {
			found = true
		}
	}
	if !found {
		t.Error("Expected low trust threshold warning")
	}
}

func TestValidateURINonStandardVersionWarning(t *testing.T) {
	result := ValidateURI("lct://sage:thinker:expert@testnet?version=2.0.0")
	if !result.Valid {
		t.Fatal("Expected valid")
	}
	found := false
	for _, w := range result.Warnings {
		if strings.Contains(w, "Non-standard version") {
			found = true
		}
	}
	if !found {
		t.Error("Expected non-standard version warning")
	}
}

// ═══════════════════════════════════════════════════════════════
// Identity Methods
// ═══════════════════════════════════════════════════════════════

func TestIdentityCanonical(t *testing.T) {
	id := &Identity{Component: "sage", Instance: "thinker", Role: "expert", Network: "testnet"}
	assertEqual(t, "canonical", "sage:thinker:expert@testnet", id.Canonical())
}

func TestIdentityEntityID(t *testing.T) {
	id := &Identity{Component: "mcp", Instance: "filesystem"}
	assertEqual(t, "entityID", "mcp:filesystem", id.EntityID())
}

func TestIdentityEquals(t *testing.T) {
	a := &Identity{Component: "sage", Instance: "thinker", Role: "expert", Network: "testnet"}
	b := &Identity{Component: "sage", Instance: "thinker", Role: "expert", Network: "testnet", Version: "2.0.0"}
	c := &Identity{Component: "sage", Instance: "thinker", Role: "other", Network: "testnet"}

	if !a.Equals(b) {
		t.Error("Expected a.Equals(b) to be true")
	}
	if a.Equals(c) {
		t.Error("Expected a.Equals(c) to be false")
	}
}

func TestFromEntityID(t *testing.T) {
	id := FromEntityID("mcp:filesystem", "", "")
	assertEqual(t, "component", "mcp", id.Component)
	assertEqual(t, "instance", "filesystem", id.Instance)
	assertEqual(t, "role", "default", id.Role)
	assertEqual(t, "network", "local", id.Network)
}

// ═══════════════════════════════════════════════════════════════
// Spec Test Vectors
// ═══════════════════════════════════════════════════════════════

func TestSpecTestVectors(t *testing.T) {
	vectors := []struct {
		uri       string
		component string
		instance  string
		role      string
		network   string
	}{
		{"lct://sage:thinker:expert_42@testnet", "sage", "thinker", "expert_42", "testnet"},
		{"lct://web4-agent:guardian:coordinator@mainnet", "web4-agent", "guardian", "coordinator", "mainnet"},
		{"lct://mcp:filesystem:reader@local", "mcp", "filesystem", "reader", "local"},
	}

	for _, v := range vectors {
		t.Run(v.uri, func(t *testing.T) {
			result := ParseURI(v.uri)
			if !result.Success {
				t.Fatalf("Failed to parse: %v", result.Errors)
			}
			assertEqual(t, "component", v.component, result.Identity.Component)
			assertEqual(t, "instance", v.instance, result.Identity.Instance)
			assertEqual(t, "role", v.role, result.Identity.Role)
			assertEqual(t, "network", v.network, result.Identity.Network)
		})
	}
}

// ═══════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════

func assertEqual(t *testing.T, field, expected, actual string) {
	t.Helper()
	if expected != actual {
		t.Errorf("%s: expected %q, got %q", field, expected, actual)
	}
}
