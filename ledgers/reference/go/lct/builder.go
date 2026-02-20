package lct

import (
	"fmt"
	"time"
)

// Builder provides fluent construction of LCT Documents.
//
// Example:
//
//	doc, err := lct.NewBuilder(lct.EntityAI, "sage-legion").
//	    WithBinding("mb64key", "cose:proof").
//	    WithBirthCertificate("lct:web4:society:fed", "lct:web4:role:citizen:ai", lct.BirthPlatform,
//	        []string{"lct:web4:witness:w1", "lct:web4:witness:w2", "lct:web4:witness:w3"}).
//	    WithT3(0.8, 0.7, 0.9).
//	    AddCapability("witness:attest").
//	    Build()
type Builder struct {
	doc        Document
	entityType EntityType
}

// NewBuilder creates a new LCT document builder.
func NewBuilder(entityType EntityType, name string) *Builder {
	hash := simpleHash(fmt.Sprintf("%s:%s:%d", entityType, name, time.Now().UnixNano()))
	now := time.Now().UTC().Format(time.RFC3339)

	return &Builder{
		entityType: entityType,
		doc: Document{
			LCTID:   fmt.Sprintf("lct:web4:%s:%s", entityType, hash),
			Subject: fmt.Sprintf("did:web4:key:%s", hash),
			Binding: Binding{
				EntityType: entityType,
				CreatedAt:  now,
			},
			MRH: MRH{
				Bound:        []MRHBound{},
				Paired:       []MRHPaired{},
				Witnessing:   []MRHWitnessing{},
				HorizonDepth: 3,
				LastUpdated:  now,
			},
			Policy: Policy{
				Capabilities: []string{},
			},
			Revocation: &Revocation{Status: RevocationActive},
		},
	}
}

// WithBinding sets the public key and binding proof.
func (b *Builder) WithBinding(publicKey, bindingProof string) *Builder {
	b.doc.Binding.PublicKey = publicKey
	b.doc.Binding.BindingProof = bindingProof
	return b
}

// WithHardwareAnchor sets the EAT hardware attestation token.
func (b *Builder) WithHardwareAnchor(anchor string) *Builder {
	b.doc.Binding.HardwareAnchor = anchor
	return b
}

// WithBirthCertificate sets the society-issued birth certificate.
func (b *Builder) WithBirthCertificate(
	issuingSociety, citizenRole string,
	context BirthContext,
	witnesses []string,
) *Builder {
	now := time.Now().UTC().Format(time.RFC3339)
	b.doc.BirthCert = BirthCertificate{
		IssuingSociety: issuingSociety,
		CitizenRole:    citizenRole,
		Context:        context,
		BirthTimestamp: now,
		BirthWitnesses: witnesses,
	}
	// Add permanent citizen pairing to MRH
	b.doc.MRH.Paired = append(b.doc.MRH.Paired, MRHPaired{
		LCTID:       citizenRole,
		PairingType: PairingBirthCertificate,
		Permanent:   true,
		TS:          now,
	})
	return b
}

// WithT3 sets the trust tensor with the 3 canonical root dimensions.
func (b *Builder) WithT3(talent, training, temperament float64) *Builder {
	t3 := &T3Tensor{
		Talent:      talent,
		Training:    training,
		Temperament: temperament,
		LastComputed: time.Now().UTC().Format(time.RFC3339),
	}
	t3.CompositeScore = ComputeT3Composite(t3)
	b.doc.T3 = t3
	return b
}

// WithV3 sets the value tensor with the 3 canonical root dimensions.
func (b *Builder) WithV3(valuation, veracity, validity float64) *Builder {
	v3 := &V3Tensor{
		Valuation: valuation,
		Veracity:  veracity,
		Validity:  validity,
		LastComputed: time.Now().UTC().Format(time.RFC3339),
	}
	v3.CompositeScore = ComputeV3Composite(v3)
	b.doc.V3 = v3
	return b
}

// AddCapability adds a capability string to the policy.
func (b *Builder) AddCapability(capability string) *Builder {
	b.doc.Policy.Capabilities = append(b.doc.Policy.Capabilities, capability)
	return b
}

// WithConstraints sets policy constraints.
func (b *Builder) WithConstraints(constraints map[string]interface{}) *Builder {
	b.doc.Policy.Constraints = constraints
	return b
}

// AddBound adds a permanent hierarchical attachment.
func (b *Builder) AddBound(lctID string, boundType BoundType) *Builder {
	b.doc.MRH.Bound = append(b.doc.MRH.Bound, MRHBound{
		LCTID: lctID,
		Type:  boundType,
		TS:    time.Now().UTC().Format(time.RFC3339),
	})
	return b
}

// AddPairing adds an operational pairing relationship.
func (b *Builder) AddPairing(lctID string, pairingType PairingType, permanent bool) *Builder {
	b.doc.MRH.Paired = append(b.doc.MRH.Paired, MRHPaired{
		LCTID:       lctID,
		PairingType: pairingType,
		Permanent:   permanent,
		TS:          time.Now().UTC().Format(time.RFC3339),
	})
	return b
}

// AddWitness adds a witness relationship.
func (b *Builder) AddWitness(lctID string, role WitnessRole) *Builder {
	b.doc.MRH.Witnessing = append(b.doc.MRH.Witnessing, MRHWitnessing{
		LCTID:           lctID,
		Role:            role,
		LastAttestation: time.Now().UTC().Format(time.RFC3339),
	})
	return b
}

// AddLineage adds an evolution history entry.
func (b *Builder) AddLineage(reason LineageReason, parent string) *Builder {
	b.doc.Lineage = append(b.doc.Lineage, LineageEntry{
		Parent: parent,
		Reason: reason,
		TS:     time.Now().UTC().Format(time.RFC3339),
	})
	return b
}

// Build validates and returns the LCT document.
// Returns error if validation fails.
func (b *Builder) Build() (*Document, error) {
	result := ValidateDocument(&b.doc)
	if !result.Valid {
		return nil, fmt.Errorf("invalid LCT document: %v", result.Errors)
	}
	doc := b.doc // copy
	return &doc, nil
}

// BuildUnsafe returns the LCT document without validation.
// Use for testing or partial documents.
func (b *Builder) BuildUnsafe() *Document {
	doc := b.doc // copy
	return &doc
}

// simpleHash creates a deterministic hash for LCT ID generation.
func simpleHash(input string) string {
	var h uint32
	for _, c := range input {
		h = (h << 5) - h + uint32(c)
	}
	return fmt.Sprintf("%016x", h)
}
