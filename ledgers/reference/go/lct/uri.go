// Package lct provides parsing, validation, and construction of Web4
// Linked Context Token (LCT) URIs and documents.
//
// URI format: lct://{component}:{instance}:{role}@{network}?{query}#{fragment}
//
// Example URIs:
//
//	lct://sage:thinker:expert_42@testnet
//	lct://web4-agent:guardian:coordinator@mainnet?pairing_status=active&trust_threshold=0.75
//	lct://mcp:filesystem:reader@local#did:key:z6Mk...
package lct

import (
	"fmt"
	"net/url"
	"regexp"
	"strconv"
	"strings"
)

// PairingStatus represents the pairing state of an LCT relationship.
type PairingStatus string

const (
	PairingPending   PairingStatus = "pending"
	PairingActive    PairingStatus = "active"
	PairingSuspended PairingStatus = "suspended"
	PairingRevoked   PairingStatus = "revoked"
)

// Identity is a parsed LCT URI structure.
type Identity struct {
	// System or domain (e.g., "sage", "web4-agent", "mcp")
	Component string
	// Instance within component (e.g., "thinker", "guardian", "filesystem")
	Instance string
	// Role or capability (e.g., "expert_42", "coordinator", "reader")
	Role string
	// Network identifier (e.g., "testnet", "mainnet", "local")
	Network string
	// Version (defaults to "1.0.0")
	Version string
	// Current pairing status (optional)
	PairingStatus PairingStatus
	// Trust threshold for operations, 0.0-1.0 (optional, -1 means unset)
	TrustThreshold float64
	// List of capabilities (optional)
	Capabilities []string
	// Public key hash or DID from URI fragment (optional)
	PublicKeyHash string
	// Raw URI string for reference
	RawURI string
}

// ParseResult is the result of parsing an LCT URI.
type ParseResult struct {
	Success  bool
	Identity *Identity
	Errors   []string
}

// ValidationResult holds validation results for an LCT URI.
type ValidationResult struct {
	Valid    bool
	Errors   []string
	Warnings []string
}

var (
	// Authority pattern: component:instance:role@network
	authorityPattern = regexp.MustCompile(`^([a-z0-9][a-z0-9-]*):([a-zA-Z0-9][a-zA-Z0-9_-]*):([a-zA-Z0-9][a-zA-Z0-9_-]*)@([a-z0-9][a-z0-9-]*)$`)

	// Component name validation (lowercase alphanumeric with hyphens)
	componentPattern = regexp.MustCompile(`^[a-z0-9][a-z0-9-]*$`)

	// Instance/role name validation (alphanumeric with underscores and hyphens)
	namePattern = regexp.MustCompile(`^(?i)[a-z0-9][a-z0-9_-]*$`)

	// Network name validation
	networkPattern = regexp.MustCompile(`^[a-z0-9][a-z0-9-]*$`)
)

// validPairingStatuses lists accepted pairing status values.
var validPairingStatuses = map[string]PairingStatus{
	"pending":   PairingPending,
	"active":    PairingActive,
	"suspended": PairingSuspended,
	"revoked":   PairingRevoked,
}

// ParseURI parses an LCT URI into a structured Identity.
//
// Example:
//
//	result := lct.ParseURI("lct://sage:thinker:expert_42@testnet")
//	if result.Success {
//	    fmt.Println(result.Identity.Component) // "sage"
//	}
func ParseURI(uri string) ParseResult {
	// Validate scheme
	if !strings.HasPrefix(uri, "lct://") {
		return ParseResult{
			Success: false,
			Errors:  []string{fmt.Sprintf("Invalid LCT URI scheme: must start with \"lct://\", got %q", truncate(uri, 20))},
		}
	}

	// Remove scheme
	withoutScheme := uri[6:]

	// Split off fragment (public key hash)
	var fragment string
	if idx := strings.Index(withoutScheme, "#"); idx >= 0 {
		fragment = withoutScheme[idx+1:]
		withoutScheme = withoutScheme[:idx]
	}

	// Split off query string
	var queryString string
	if idx := strings.Index(withoutScheme, "?"); idx >= 0 {
		queryString = withoutScheme[idx+1:]
		withoutScheme = withoutScheme[:idx]
	}

	authority := withoutScheme

	// Parse authority (component:instance:role@network)
	matches := authorityPattern.FindStringSubmatch(authority)
	if matches == nil {
		return ParseResult{
			Success: false,
			Errors:  []string{fmt.Sprintf("Invalid LCT authority format: expected \"component:instance:role@network\", got %q", authority)},
		}
	}

	component := matches[1]
	instance := matches[2]
	role := matches[3]
	network := matches[4]

	// Validate individual parts
	var errors []string
	if !componentPattern.MatchString(component) {
		errors = append(errors, fmt.Sprintf("Invalid component name: %q - must be lowercase alphanumeric with hyphens", component))
	}
	if !namePattern.MatchString(instance) {
		errors = append(errors, fmt.Sprintf("Invalid instance name: %q - must be alphanumeric with underscores/hyphens", instance))
	}
	if !namePattern.MatchString(role) {
		errors = append(errors, fmt.Sprintf("Invalid role name: %q - must be alphanumeric with underscores/hyphens", role))
	}
	if !networkPattern.MatchString(network) {
		errors = append(errors, fmt.Sprintf("Invalid network name: %q - must be lowercase alphanumeric with hyphens", network))
	}

	if len(errors) > 0 {
		return ParseResult{Success: false, Errors: errors}
	}

	// Parse query parameters
	version := "1.0.0"
	var pairingStatus PairingStatus
	trustThreshold := -1.0
	var capabilities []string

	if queryString != "" {
		params, err := url.ParseQuery(queryString)
		if err != nil {
			return ParseResult{
				Success: false,
				Errors:  []string{fmt.Sprintf("Invalid query string: %v", err)},
			}
		}

		if v := params.Get("version"); v != "" {
			version = v
		}

		if s := params.Get("pairing_status"); s != "" {
			if ps, ok := validPairingStatuses[s]; ok {
				pairingStatus = ps
			} else {
				errors = append(errors, fmt.Sprintf("Invalid pairing_status: %q - must be pending|active|suspended|revoked", s))
			}
		}

		if t := params.Get("trust_threshold"); t != "" {
			threshold, err := strconv.ParseFloat(t, 64)
			if err != nil || threshold < 0 || threshold > 1 {
				errors = append(errors, fmt.Sprintf("Invalid trust_threshold: %q - must be a number between 0 and 1", t))
			} else {
				trustThreshold = threshold
			}
		}

		if c := params.Get("capabilities"); c != "" {
			for _, cap := range strings.Split(c, ",") {
				cap = strings.TrimSpace(cap)
				if cap != "" {
					capabilities = append(capabilities, cap)
				}
			}
		}
	}

	if len(errors) > 0 {
		return ParseResult{Success: false, Errors: errors}
	}

	return ParseResult{
		Success: true,
		Identity: &Identity{
			Component:      component,
			Instance:       instance,
			Role:           role,
			Network:        network,
			Version:        version,
			PairingStatus:  pairingStatus,
			TrustThreshold: trustThreshold,
			Capabilities:   capabilities,
			PublicKeyHash:  fragment,
			RawURI:         uri,
		},
		Errors: nil,
	}
}

// ValidateURI validates an LCT URI format without fully parsing it.
// Returns validation result with errors and warnings.
func ValidateURI(uri string) ValidationResult {
	result := ParseURI(uri)
	if !result.Success {
		return ValidationResult{Valid: false, Errors: result.Errors}
	}

	id := result.Identity
	var warnings []string

	if id.Network == "local" && id.PublicKeyHash == "" {
		warnings = append(warnings, "Local network LCTs should include public key hash for verification")
	}

	if id.TrustThreshold >= 0 && id.TrustThreshold < 0.5 {
		warnings = append(warnings, fmt.Sprintf("Low trust threshold (%.2f) may allow untrusted operations", id.TrustThreshold))
	}

	if id.Version != "1.0.0" {
		warnings = append(warnings, fmt.Sprintf("Non-standard version: %s", id.Version))
	}

	return ValidationResult{Valid: true, Warnings: warnings}
}

// BuildURI constructs an LCT URI from an Identity.
func BuildURI(id *Identity) string {
	var b strings.Builder
	b.WriteString("lct://")
	b.WriteString(id.Component)
	b.WriteByte(':')
	b.WriteString(id.Instance)
	b.WriteByte(':')
	b.WriteString(id.Role)
	b.WriteByte('@')
	b.WriteString(id.Network)

	// Build query string
	var params []string
	if id.Version != "" && id.Version != "1.0.0" {
		params = append(params, "version="+url.QueryEscape(id.Version))
	}
	if id.PairingStatus != "" {
		params = append(params, "pairing_status="+url.QueryEscape(string(id.PairingStatus)))
	}
	if id.TrustThreshold >= 0 {
		params = append(params, fmt.Sprintf("trust_threshold=%g", id.TrustThreshold))
	}
	if len(id.Capabilities) > 0 {
		params = append(params, "capabilities="+url.QueryEscape(strings.Join(id.Capabilities, ",")))
	}

	if len(params) > 0 {
		b.WriteByte('?')
		b.WriteString(strings.Join(params, "&"))
	}

	if id.PublicKeyHash != "" {
		b.WriteByte('#')
		b.WriteString(id.PublicKeyHash)
	}

	return b.String()
}

// Canonical returns the canonical string representation for an Identity.
// Format: "component:instance:role@network"
func (id *Identity) Canonical() string {
	return fmt.Sprintf("%s:%s:%s@%s", id.Component, id.Instance, id.Role, id.Network)
}

// EntityID returns the simple entity ID format used by web4-trust-core.
// Format: "component:instance"
func (id *Identity) EntityID() string {
	return fmt.Sprintf("%s:%s", id.Component, id.Instance)
}

// Equals checks if two Identities refer to the same entity.
// Compares component, instance, role, and network (ignoring metadata).
func (id *Identity) Equals(other *Identity) bool {
	if id == nil || other == nil {
		return id == other
	}
	return id.Component == other.Component &&
		id.Instance == other.Instance &&
		id.Role == other.Role &&
		id.Network == other.Network
}

// FromEntityID creates a minimal Identity from a simple "type:name" entity ID.
func FromEntityID(entityID string, network string, role string) *Identity {
	if network == "" {
		network = "local"
	}
	if role == "" {
		role = "default"
	}
	parts := strings.SplitN(entityID, ":", 2)
	component := "unknown"
	instance := "unknown"
	if len(parts) >= 1 {
		component = parts[0]
	}
	if len(parts) >= 2 {
		instance = parts[1]
	}
	return &Identity{
		Component: component,
		Instance:  instance,
		Role:      role,
		Network:   network,
		Version:   "1.0.0",
		TrustThreshold: -1,
	}
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}
