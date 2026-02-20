package lct

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"math"
	"regexp"
	"strings"
	"time"
)

// EntityType enumerates the 15 canonical entity types per entity-types.md (Feb 2026).
type EntityType string

const (
	EntityHuman          EntityType = "human"
	EntityAI             EntityType = "ai"
	EntitySociety        EntityType = "society"
	EntityOrganization   EntityType = "organization"
	EntityRole           EntityType = "role"
	EntityTask           EntityType = "task"
	EntityResource       EntityType = "resource"
	EntityDevice         EntityType = "device"
	EntityService        EntityType = "service"
	EntityOracle         EntityType = "oracle"
	EntityAccumulator    EntityType = "accumulator"
	EntityDictionary     EntityType = "dictionary"
	EntityHybrid         EntityType = "hybrid"
	EntityPolicy         EntityType = "policy"
	EntityInfrastructure EntityType = "infrastructure"
)

// ValidEntityTypes lists all canonical entity types for validation.
var ValidEntityTypes = []EntityType{
	EntityHuman, EntityAI, EntitySociety, EntityOrganization, EntityRole,
	EntityTask, EntityResource, EntityDevice, EntityService, EntityOracle,
	EntityAccumulator, EntityDictionary, EntityHybrid, EntityPolicy,
	EntityInfrastructure,
}

// T3Tensor represents the Trust Tensor with 3 canonical root dimensions.
// Each root aggregates an open-ended RDF sub-dimension graph via web4:subDimensionOf.
type T3Tensor struct {
	// Role-specific capability (0.0-1.0)
	Talent float64 `json:"talent"`
	// Role-specific expertise / learning quality (0.0-1.0)
	Training float64 `json:"training"`
	// Behavioral stability / reliability (0.0-1.0)
	Temperament float64 `json:"temperament"`
	// Optional domain-specific refinements
	SubDimensions map[string]map[string]float64 `json:"sub_dimensions,omitempty"`
	// Weighted composite score (0.0-1.0)
	CompositeScore float64 `json:"composite_score,omitempty"`
	// When tensors were last computed
	LastComputed string `json:"last_computed,omitempty"`
	// LCT IDs of entities that computed these scores
	ComputationWitnesses []string `json:"computation_witnesses,omitempty"`
}

// V3Tensor represents the Value Tensor with 3 canonical root dimensions.
type V3Tensor struct {
	// Subjective worth / economic value (0.0+, can exceed 1.0)
	Valuation float64 `json:"valuation"`
	// Truthfulness / accuracy of claims (0.0-1.0)
	Veracity float64 `json:"veracity"`
	// Soundness of reasoning / confirmed value delivery (0.0-1.0)
	Validity float64 `json:"validity"`
	// Optional domain-specific refinements
	SubDimensions map[string]map[string]float64 `json:"sub_dimensions,omitempty"`
	// Weighted composite score
	CompositeScore float64 `json:"composite_score,omitempty"`
	// When tensors were last computed
	LastComputed string `json:"last_computed,omitempty"`
	// LCT IDs of entities that computed these scores
	ComputationWitnesses []string `json:"computation_witnesses,omitempty"`
}

// Binding represents a cryptographic anchor for an LCT.
type Binding struct {
	EntityType    EntityType `json:"entity_type"`
	PublicKey     string     `json:"public_key"`
	HardwareAnchor string   `json:"hardware_anchor,omitempty"`
	CreatedAt     string     `json:"created_at"`
	BindingProof  string     `json:"binding_proof"`
}

// BirthContext describes the context of an entity's birth.
type BirthContext string

const (
	BirthNation       BirthContext = "nation"
	BirthPlatform     BirthContext = "platform"
	BirthNetwork      BirthContext = "network"
	BirthOrganization BirthContext = "organization"
	BirthEcosystem    BirthContext = "ecosystem"
)

// BirthCertificate is the society-issued genesis identity record.
type BirthCertificate struct {
	IssuingSociety string       `json:"issuing_society"`
	CitizenRole    string       `json:"citizen_role"`
	Context        BirthContext `json:"context"`
	BirthTimestamp string       `json:"birth_timestamp"`
	ParentEntity   string       `json:"parent_entity,omitempty"`
	BirthWitnesses []string     `json:"birth_witnesses"`
}

// BoundType describes the type of hierarchical attachment.
type BoundType string

const (
	BoundParent  BoundType = "parent"
	BoundChild   BoundType = "child"
	BoundSibling BoundType = "sibling"
)

// PairingType describes the type of paired relationship.
type PairingType string

const (
	PairingBirthCertificate PairingType = "birth_certificate"
	PairingRole             PairingType = "role"
	PairingOperational      PairingType = "operational"
)

// WitnessRole describes the role of a witness.
type WitnessRole string

const (
	WitnessTime      WitnessRole = "time"
	WitnessAudit     WitnessRole = "audit"
	WitnessOracle    WitnessRole = "oracle"
	WitnessPeer      WitnessRole = "peer"
	WitnessExistence WitnessRole = "existence"
	WitnessAction    WitnessRole = "action"
	WitnessState     WitnessRole = "state"
	WitnessQuality   WitnessRole = "quality"
)

// MRHBound represents a permanent hierarchical attachment.
type MRHBound struct {
	LCTID string    `json:"lct_id"`
	Type  BoundType `json:"type"`
	TS    string    `json:"ts"`
}

// MRHPaired represents an authorized operational relationship.
type MRHPaired struct {
	LCTID       string      `json:"lct_id"`
	PairingType PairingType `json:"pairing_type,omitempty"`
	Permanent   bool        `json:"permanent,omitempty"`
	Context     string      `json:"context,omitempty"`
	SessionID   string      `json:"session_id,omitempty"`
	TS          string      `json:"ts"`
}

// MRHWitnessing represents a witness relationship.
type MRHWitnessing struct {
	LCTID           string      `json:"lct_id"`
	Role            WitnessRole `json:"role"`
	LastAttestation string      `json:"last_attestation"`
}

// MRH represents the Markov Relevancy Horizon.
type MRH struct {
	Bound        []MRHBound      `json:"bound"`
	Paired       []MRHPaired     `json:"paired"`
	Witnessing   []MRHWitnessing `json:"witnessing,omitempty"`
	HorizonDepth int             `json:"horizon_depth"`
	LastUpdated  string          `json:"last_updated"`
}

// Policy describes capabilities and constraints.
type Policy struct {
	Capabilities []string               `json:"capabilities"`
	Constraints  map[string]interface{} `json:"constraints,omitempty"`
}

// Attestation represents a witness observation.
type Attestation struct {
	Witness string                 `json:"witness"`
	Type    string                 `json:"type"`
	Sig     string                 `json:"sig"`
	TS      string                 `json:"ts"`
	Claims  map[string]interface{} `json:"claims,omitempty"`
}

// LineageReason describes why a lineage event occurred.
type LineageReason string

const (
	LineageGenesis  LineageReason = "genesis"
	LineageRotation LineageReason = "rotation"
	LineageFork     LineageReason = "fork"
	LineageUpgrade  LineageReason = "upgrade"
)

// LineageEntry represents an evolution history entry.
type LineageEntry struct {
	Parent string        `json:"parent,omitempty"`
	Reason LineageReason `json:"reason"`
	TS     string        `json:"ts"`
}

// RevocationStatus describes whether an LCT is active or revoked.
type RevocationStatus string

const (
	RevocationActive  RevocationStatus = "active"
	RevocationRevoked RevocationStatus = "revoked"
)

// RevocationReason describes why an LCT was revoked.
type RevocationReason string

const (
	RevocationCompromise  RevocationReason = "compromise"
	RevocationSuperseded  RevocationReason = "superseded"
	RevocationExpired     RevocationReason = "expired"
)

// Revocation is the termination record for an LCT.
type Revocation struct {
	Status RevocationStatus `json:"status"`
	TS     string           `json:"ts,omitempty"`
	Reason RevocationReason `json:"reason,omitempty"`
}

// Document is a complete Linked Context Token (LCT) document.
//
// Required: LCTID, Subject, Binding, BirthCert, MRH, Policy
// Optional: T3, V3, Attestations, Lineage, Revocation
type Document struct {
	LCTID        string            `json:"lct_id"`
	Subject      string            `json:"subject"`
	Binding      Binding           `json:"binding"`
	BirthCert    BirthCertificate  `json:"birth_certificate"`
	MRH          MRH               `json:"mrh"`
	Policy       Policy            `json:"policy"`
	T3           *T3Tensor         `json:"t3_tensor,omitempty"`
	V3           *V3Tensor         `json:"v3_tensor,omitempty"`
	Attestations []Attestation     `json:"attestations,omitempty"`
	Lineage      []LineageEntry    `json:"lineage,omitempty"`
	Revocation   *Revocation       `json:"revocation,omitempty"`
}

// ═══════════════════════════════════════════════════════════════
// Tensor Operations
// ═══════════════════════════════════════════════════════════════

// ComputeT3Composite calculates the weighted composite score for a T3 tensor.
// Weights: talent=0.4, training=0.3, temperament=0.3
func ComputeT3Composite(t3 *T3Tensor) float64 {
	return t3.Talent*0.4 + t3.Training*0.3 + t3.Temperament*0.3
}

// ComputeV3Composite calculates the weighted composite score for a V3 tensor.
// Weights: valuation=0.3, veracity=0.35, validity=0.35
func ComputeV3Composite(v3 *V3Tensor) float64 {
	return v3.Valuation*0.3 + v3.Veracity*0.35 + v3.Validity*0.35
}

// DefaultT3 creates a neutral starting T3 tensor (all 0.5).
func DefaultT3() T3Tensor {
	return T3Tensor{
		Talent:         0.5,
		Training:       0.5,
		Temperament:    0.5,
		CompositeScore: 0.5,
		LastComputed:   time.Now().UTC().Format(time.RFC3339),
	}
}

// DefaultV3 creates a default V3 tensor (valuation=0, veracity/validity=0.5).
func DefaultV3() V3Tensor {
	return V3Tensor{
		Valuation:      0.0,
		Veracity:       0.5,
		Validity:       0.5,
		CompositeScore: 0.35,
		LastComputed:   time.Now().UTC().Format(time.RFC3339),
	}
}

// MigrateT3FromLegacy6D converts legacy 6-dim T3 to canonical 3-dim.
// Migration path from web4-trust-core/src/tensor/t3.rs::from_legacy_6d()
func MigrateT3FromLegacy6D(competence, reliability, consistency, witnesses, lineage, alignment float64) T3Tensor {
	talent := competence
	training := (reliability + consistency + lineage) / 3.0
	temperament := (witnesses + alignment) / 2.0

	t3 := T3Tensor{
		Talent:      clamp01(talent),
		Training:    clamp01(training),
		Temperament: clamp01(temperament),
	}
	t3.CompositeScore = ComputeT3Composite(&t3)
	t3.LastComputed = time.Now().UTC().Format(time.RFC3339)
	return t3
}

// MigrateV3FromLegacy6D converts legacy 6-dim V3 to canonical 3-dim.
func MigrateV3FromLegacy6D(energy, contribution, stewardship, network, reputation, temporal float64) V3Tensor {
	valuation := (energy + contribution) / 2.0
	veracity := reputation
	validity := (stewardship + network + temporal) / 3.0

	v3 := V3Tensor{
		Valuation: clamp01(valuation),
		Veracity:  clamp01(veracity),
		Validity:  clamp01(validity),
	}
	v3.CompositeScore = ComputeV3Composite(&v3)
	v3.LastComputed = time.Now().UTC().Format(time.RFC3339)
	return v3
}

func clamp01(v float64) float64 {
	return math.Max(0, math.Min(1, v))
}

// ═══════════════════════════════════════════════════════════════
// Validation
// ═══════════════════════════════════════════════════════════════

// DocValidationResult holds document validation results.
type DocValidationResult struct {
	Valid    bool
	Errors   []string
	Warnings []string
}

var (
	lctIDPattern  = regexp.MustCompile(`^lct:web4:[A-Za-z0-9_:-]+$`)
	subjectPattern = regexp.MustCompile(`^did:web4:(key|method):[A-Za-z0-9_-]+$`)
)

func isValidEntityType(et EntityType) bool {
	for _, t := range ValidEntityTypes {
		if t == et {
			return true
		}
	}
	return false
}

// ValidateDocument validates an LCT Document against the schema rules.
func ValidateDocument(doc *Document) DocValidationResult {
	var errors, warnings []string

	// Required fields
	if doc.LCTID == "" {
		errors = append(errors, "Missing required field: lct_id")
	}
	if doc.Subject == "" {
		errors = append(errors, "Missing required field: subject")
	}
	if doc.Binding == (Binding{}) {
		errors = append(errors, "Missing required field: binding")
	}
	if doc.Policy.Capabilities == nil {
		errors = append(errors, "Missing policy.capabilities")
	}

	if len(errors) > 0 {
		return DocValidationResult{Valid: false, Errors: errors, Warnings: warnings}
	}

	// LCT ID format
	if !lctIDPattern.MatchString(doc.LCTID) {
		errors = append(errors, fmt.Sprintf("Invalid lct_id format: %q", doc.LCTID))
	}

	// Subject format
	if !subjectPattern.MatchString(doc.Subject) {
		errors = append(errors, fmt.Sprintf("Invalid subject format: %q", doc.Subject))
	}

	// Binding validation
	if !isValidEntityType(doc.Binding.EntityType) {
		errors = append(errors, fmt.Sprintf("Invalid entity_type: %q", doc.Binding.EntityType))
	}
	if doc.Binding.PublicKey == "" {
		errors = append(errors, "Missing binding.public_key")
	}
	if doc.Binding.CreatedAt == "" {
		errors = append(errors, "Missing binding.created_at")
	}
	if doc.Binding.BindingProof == "" {
		errors = append(errors, "Missing binding.binding_proof")
	}

	// Birth certificate validation
	bc := doc.BirthCert
	if bc.IssuingSociety == "" {
		errors = append(errors, "Missing birth_certificate.issuing_society")
	}
	if bc.CitizenRole == "" {
		errors = append(errors, "Missing birth_certificate.citizen_role")
	}
	if bc.Context == "" {
		errors = append(errors, "Missing birth_certificate.context")
	}
	if bc.BirthTimestamp == "" {
		errors = append(errors, "Missing birth_certificate.birth_timestamp")
	}
	if len(bc.BirthWitnesses) == 0 {
		errors = append(errors, "birth_certificate.birth_witnesses must have at least 1 entry")
	}
	if len(bc.BirthWitnesses) > 0 && len(bc.BirthWitnesses) < 3 {
		warnings = append(warnings, "birth_certificate.birth_witnesses should have at least 3 entries per spec")
	}

	// MRH validation
	if len(doc.MRH.Paired) == 0 {
		errors = append(errors, "mrh.paired must have at least 1 entry")
	}
	if doc.MRH.HorizonDepth < 1 || doc.MRH.HorizonDepth > 10 {
		errors = append(errors, fmt.Sprintf("mrh.horizon_depth must be 1-10, got %d", doc.MRH.HorizonDepth))
	}

	// Check for permanent citizen pairing
	hasCitizenPairing := false
	for _, p := range doc.MRH.Paired {
		if p.PairingType == PairingBirthCertificate && p.Permanent {
			hasCitizenPairing = true
			break
		}
	}
	if !hasCitizenPairing {
		warnings = append(warnings, "No permanent birth_certificate pairing found in mrh.paired")
	}

	// T3 tensor validation
	if doc.T3 != nil {
		if doc.T3.Talent < 0 || doc.T3.Talent > 1 {
			errors = append(errors, "t3_tensor.talent must be 0.0-1.0")
		}
		if doc.T3.Training < 0 || doc.T3.Training > 1 {
			errors = append(errors, "t3_tensor.training must be 0.0-1.0")
		}
		if doc.T3.Temperament < 0 || doc.T3.Temperament > 1 {
			errors = append(errors, "t3_tensor.temperament must be 0.0-1.0")
		}
	}

	// V3 tensor validation
	if doc.V3 != nil {
		if doc.V3.Valuation < 0 {
			errors = append(errors, "v3_tensor.valuation must be >= 0")
		}
		if doc.V3.Veracity < 0 || doc.V3.Veracity > 1 {
			errors = append(errors, "v3_tensor.veracity must be 0.0-1.0")
		}
		if doc.V3.Validity < 0 || doc.V3.Validity > 1 {
			errors = append(errors, "v3_tensor.validity must be 0.0-1.0")
		}
	}

	// Revocation validation
	if doc.Revocation != nil && doc.Revocation.Status == RevocationRevoked {
		if doc.Revocation.TS == "" {
			warnings = append(warnings, "Revoked LCT should have revocation timestamp")
		}
		if doc.Revocation.Reason == "" {
			warnings = append(warnings, "Revoked LCT should have revocation reason")
		}
	}

	return DocValidationResult{
		Valid:    len(errors) == 0,
		Errors:   errors,
		Warnings: warnings,
	}
}

// ═══════════════════════════════════════════════════════════════
// Document → URI Bridge
// ═══════════════════════════════════════════════════════════════

// ToURI converts an LCT Document to an LCT URI for network addressing.
func (doc *Document) ToURI(network, role string) string {
	if network == "" {
		network = "local"
	}
	if role == "" {
		role = "default"
	}
	hash := doc.LCTID
	parts := splitLast(hash, ":")
	if parts[1] != "" {
		hash = parts[1]
	}
	return fmt.Sprintf("lct://%s:%s:%s@%s", doc.Binding.EntityType, hash, role, network)
}

// Hash returns the SHA-256 hash of the document's canonical JSON form.
func (doc *Document) Hash() string {
	data, _ := json.Marshal(doc)
	h := sha256.Sum256(data)
	return fmt.Sprintf("%x", h)
}

func splitLast(s, sep string) [2]string {
	idx := strings.LastIndex(s, sep)
	if idx < 0 {
		return [2]string{s, ""}
	}
	return [2]string{s[:idx], s[idx+len(sep):]}
}
