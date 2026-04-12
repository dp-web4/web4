#!/usr/bin/env python3
"""
Web4 Deployment Conformance Profiles — Reference Implementation
Specs: web4-standard/profiles/{edge-device,cloud-service,peer-to-peer,blockchain-bridge}-profile.md

Four deployment profiles with specific protocol stacks, data formats,
and cryptographic suites for different deployment contexts.

Covers:
  Profile 1: Edge Device — CoAP/UDP/BLE, CBOR, W4-IOT-1
  Profile 2: Cloud Service — HTTPS/TCP/OAuth, JSON, W4-FIPS-1
  Profile 3: Peer-to-Peer — WebRTC/SCTP, CBOR, W4-BASE-1
  Profile 4: Blockchain Bridge — anchoring/timestamping/verification, JSON, W4-BASE-1

Run: python deployment_profiles.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================
# Protocol Components
# ============================================================

class NetworkProtocol(Enum):
    COAP = "CoAP"         # Constrained Application Protocol
    HTTPS = "HTTPS"       # HTTP Secure
    WEBRTC = "WebRTC"     # Web Real-Time Communication


class TransportProtocol(Enum):
    UDP = "UDP"
    TCP = "TCP"
    SCTP = "SCTP"


class PhysicalLayer(Enum):
    BLE = "BLE"           # Bluetooth Low Energy
    ETHERNET = "Ethernet"
    WIFI = "WiFi"
    NONE = "None"         # Software-only


class AuthMethod(Enum):
    NONE = "None"
    OAUTH2 = "OAuth 2.0"
    MUTUAL_TLS = "Mutual TLS"


# ============================================================
# Data Formats
# ============================================================

class DataFormat(Enum):
    CBOR = "CBOR"         # Concise Binary Object Representation
    JSON = "JSON"


class Canonicalization(Enum):
    CBOR_DET = "CBOR Deterministic Encoding"
    JCS = "JSON Canonicalization Scheme"


# ============================================================
# Cryptographic Suites
# ============================================================

class CryptoSuiteID(Enum):
    W4_IOT_1 = "W4-IOT-1"     # IoT/Edge
    W4_FIPS_1 = "W4-FIPS-1"   # FIPS-compliant (Cloud)
    W4_BASE_1 = "W4-BASE-1"   # Baseline (P2P, Blockchain)


class KEM(Enum):
    X25519 = "X25519"
    P256ECDH = "P-256ECDH"


class SignatureAlgorithm(Enum):
    ED25519 = "Ed25519"
    ECDSA_P256 = "ECDSA-P256"


class AEAD(Enum):
    AES_CCM = "AES-CCM"
    AES_128_GCM = "AES-128-GCM"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"


class HashAlgorithm(Enum):
    SHA256 = "SHA-256"


class KDF(Enum):
    HKDF = "HKDF"


@dataclass
class CryptoSuite:
    suite_id: CryptoSuiteID
    kem: KEM
    signature: SignatureAlgorithm
    aead: AEAD
    hash: HashAlgorithm = HashAlgorithm.SHA256
    kdf: KDF = KDF.HKDF


# ============================================================
# Blockchain Integration (Profile 4)
# ============================================================

class BlockchainCapability(Enum):
    ANCHORING = "anchoring"         # Store LCT hash in smart contract
    TIMESTAMPING = "timestamping"   # Verifiable creation/update time
    VERIFICATION = "verification"   # Smart contract authenticity checks


# ============================================================
# Deployment Profile
# ============================================================

class ProfileID(Enum):
    EDGE_DEVICE = "edge-device"
    CLOUD_SERVICE = "cloud-service"
    PEER_TO_PEER = "peer-to-peer"
    BLOCKCHAIN_BRIDGE = "blockchain-bridge"


@dataclass
class ProtocolStack:
    network: Optional[NetworkProtocol] = None
    transport: Optional[TransportProtocol] = None
    physical: PhysicalLayer = PhysicalLayer.NONE
    auth: AuthMethod = AuthMethod.NONE


@dataclass
class DataConfig:
    primary_format: DataFormat = DataFormat.JSON
    canonicalization: Canonicalization = Canonicalization.JCS


@dataclass
class DeploymentProfile:
    profile_id: ProfileID
    description: str
    protocol_stack: ProtocolStack
    data_config: DataConfig
    crypto_suite: CryptoSuite
    blockchain_capabilities: list[BlockchainCapability] = field(default_factory=list)
    resource_constrained: bool = False

    def supports_blockchain(self) -> bool:
        return len(self.blockchain_capabilities) > 0

    def is_fips_compliant(self) -> bool:
        return self.crypto_suite.suite_id == CryptoSuiteID.W4_FIPS_1

    def uses_binary_encoding(self) -> bool:
        return self.data_config.primary_format == DataFormat.CBOR

    def summary(self) -> dict:
        return {
            "profile": self.profile_id.value,
            "suite": self.crypto_suite.suite_id.value,
            "format": self.data_config.primary_format.value,
            "fips": self.is_fips_compliant(),
            "binary": self.uses_binary_encoding(),
            "blockchain": self.supports_blockchain(),
            "constrained": self.resource_constrained,
        }


# ============================================================
# Canonical Profile Definitions
# ============================================================

PROFILES = {
    ProfileID.EDGE_DEVICE: DeploymentProfile(
        profile_id=ProfileID.EDGE_DEVICE,
        description="Edge devices: IoT sensors, actuators, gateways. Resource-constrained.",
        protocol_stack=ProtocolStack(
            network=NetworkProtocol.COAP,
            transport=TransportProtocol.UDP,
            physical=PhysicalLayer.BLE,
        ),
        data_config=DataConfig(
            primary_format=DataFormat.CBOR,
            canonicalization=Canonicalization.CBOR_DET,
        ),
        crypto_suite=CryptoSuite(
            suite_id=CryptoSuiteID.W4_IOT_1,
            kem=KEM.X25519,
            signature=SignatureAlgorithm.ED25519,
            aead=AEAD.AES_CCM,
        ),
        resource_constrained=True,
    ),
    ProfileID.CLOUD_SERVICE: DeploymentProfile(
        profile_id=ProfileID.CLOUD_SERVICE,
        description="Cloud services: web servers, APIs, backend systems. Not resource-constrained.",
        protocol_stack=ProtocolStack(
            network=NetworkProtocol.HTTPS,
            transport=TransportProtocol.TCP,
            auth=AuthMethod.OAUTH2,
        ),
        data_config=DataConfig(
            primary_format=DataFormat.JSON,
            canonicalization=Canonicalization.JCS,
        ),
        crypto_suite=CryptoSuite(
            suite_id=CryptoSuiteID.W4_FIPS_1,
            kem=KEM.P256ECDH,
            signature=SignatureAlgorithm.ECDSA_P256,
            aead=AEAD.AES_128_GCM,
        ),
        resource_constrained=False,
    ),
    ProfileID.PEER_TO_PEER: DeploymentProfile(
        profile_id=ProfileID.PEER_TO_PEER,
        description="Peer-to-peer: secure messaging, file sharing, collaborative editing.",
        protocol_stack=ProtocolStack(
            network=NetworkProtocol.WEBRTC,
            transport=TransportProtocol.SCTP,
        ),
        data_config=DataConfig(
            primary_format=DataFormat.CBOR,
            canonicalization=Canonicalization.CBOR_DET,
        ),
        crypto_suite=CryptoSuite(
            suite_id=CryptoSuiteID.W4_BASE_1,
            kem=KEM.X25519,
            signature=SignatureAlgorithm.ED25519,
            aead=AEAD.CHACHA20_POLY1305,
        ),
        resource_constrained=False,
    ),
    ProfileID.BLOCKCHAIN_BRIDGE: DeploymentProfile(
        profile_id=ProfileID.BLOCKCHAIN_BRIDGE,
        description="Blockchain bridge: anchoring, timestamping, verification via smart contracts.",
        protocol_stack=ProtocolStack(),  # Network-agnostic
        data_config=DataConfig(
            primary_format=DataFormat.JSON,
            canonicalization=Canonicalization.JCS,
        ),
        crypto_suite=CryptoSuite(
            suite_id=CryptoSuiteID.W4_BASE_1,
            kem=KEM.X25519,
            signature=SignatureAlgorithm.ED25519,
            aead=AEAD.CHACHA20_POLY1305,
        ),
        blockchain_capabilities=[
            BlockchainCapability.ANCHORING,
            BlockchainCapability.TIMESTAMPING,
            BlockchainCapability.VERIFICATION,
        ],
        resource_constrained=False,
    ),
}


# ============================================================
# Profile Compatibility Checker
# ============================================================

class ProfileCompatibility:
    """Check compatibility between two deployment profiles."""

    @staticmethod
    def can_communicate(a: DeploymentProfile, b: DeploymentProfile) -> bool:
        """Check if two profiles can directly communicate."""
        # Need compatible data format OR a bridge
        if a.data_config.primary_format == b.data_config.primary_format:
            return True
        # JSON profiles can bridge to CBOR via transcoding
        return False

    @staticmethod
    def shared_crypto(a: DeploymentProfile, b: DeploymentProfile) -> bool:
        """Check if two profiles share a crypto suite or compatible algorithms."""
        if a.crypto_suite.suite_id == b.crypto_suite.suite_id:
            return True
        # X25519 and Ed25519 are compatible across suites
        if (a.crypto_suite.kem == b.crypto_suite.kem and
                a.crypto_suite.signature == b.crypto_suite.signature):
            return True
        return False

    @staticmethod
    def needs_bridge(a: DeploymentProfile, b: DeploymentProfile) -> bool:
        """Check if communication requires a protocol bridge."""
        return (a.data_config.primary_format != b.data_config.primary_format or
                a.crypto_suite.suite_id != b.crypto_suite.suite_id)


# ════════════════════════════════════════════════════════════════
#  TESTS
# ════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    # ── T1: Profile Enumeration ──────────────────────────────────
    print("T1: Profile Enumeration")
    check("T1.1 Four profiles defined",
          len(ProfileID) == 4)
    check("T1.2 Four profiles in registry",
          len(PROFILES) == 4)
    check("T1.3 Edge device profile",
          ProfileID.EDGE_DEVICE.value == "edge-device")
    check("T1.4 Cloud service profile",
          ProfileID.CLOUD_SERVICE.value == "cloud-service")
    check("T1.5 Peer-to-peer profile",
          ProfileID.PEER_TO_PEER.value == "peer-to-peer")
    check("T1.6 Blockchain bridge profile",
          ProfileID.BLOCKCHAIN_BRIDGE.value == "blockchain-bridge")

    # ── T2: Edge Device Profile ──────────────────────────────────
    print("T2: Edge Device Profile")
    edge = PROFILES[ProfileID.EDGE_DEVICE]
    check("T2.1 CoAP network",
          edge.protocol_stack.network == NetworkProtocol.COAP)
    check("T2.2 UDP transport",
          edge.protocol_stack.transport == TransportProtocol.UDP)
    check("T2.3 BLE physical",
          edge.protocol_stack.physical == PhysicalLayer.BLE)
    check("T2.4 CBOR data format",
          edge.data_config.primary_format == DataFormat.CBOR)
    check("T2.5 CBOR deterministic canonicalization",
          edge.data_config.canonicalization == Canonicalization.CBOR_DET)
    check("T2.6 W4-IOT-1 crypto suite",
          edge.crypto_suite.suite_id == CryptoSuiteID.W4_IOT_1)
    check("T2.7 X25519 KEM",
          edge.crypto_suite.kem == KEM.X25519)
    check("T2.8 Ed25519 signature",
          edge.crypto_suite.signature == SignatureAlgorithm.ED25519)
    check("T2.9 AES-CCM AEAD",
          edge.crypto_suite.aead == AEAD.AES_CCM)
    check("T2.10 SHA-256 hash",
          edge.crypto_suite.hash == HashAlgorithm.SHA256)
    check("T2.11 HKDF",
          edge.crypto_suite.kdf == KDF.HKDF)
    check("T2.12 Resource constrained",
          edge.resource_constrained is True)
    check("T2.13 Uses binary encoding",
          edge.uses_binary_encoding() is True)
    check("T2.14 Not FIPS compliant",
          edge.is_fips_compliant() is False)
    check("T2.15 No blockchain",
          edge.supports_blockchain() is False)

    # ── T3: Cloud Service Profile ────────────────────────────────
    print("T3: Cloud Service Profile")
    cloud = PROFILES[ProfileID.CLOUD_SERVICE]
    check("T3.1 HTTPS network",
          cloud.protocol_stack.network == NetworkProtocol.HTTPS)
    check("T3.2 TCP transport",
          cloud.protocol_stack.transport == TransportProtocol.TCP)
    check("T3.3 OAuth 2.0 auth",
          cloud.protocol_stack.auth == AuthMethod.OAUTH2)
    check("T3.4 JSON data format",
          cloud.data_config.primary_format == DataFormat.JSON)
    check("T3.5 JCS canonicalization",
          cloud.data_config.canonicalization == Canonicalization.JCS)
    check("T3.6 W4-FIPS-1 crypto suite",
          cloud.crypto_suite.suite_id == CryptoSuiteID.W4_FIPS_1)
    check("T3.7 P-256ECDH KEM",
          cloud.crypto_suite.kem == KEM.P256ECDH)
    check("T3.8 ECDSA-P256 signature",
          cloud.crypto_suite.signature == SignatureAlgorithm.ECDSA_P256)
    check("T3.9 AES-128-GCM AEAD",
          cloud.crypto_suite.aead == AEAD.AES_128_GCM)
    check("T3.10 Not resource constrained",
          cloud.resource_constrained is False)
    check("T3.11 FIPS compliant",
          cloud.is_fips_compliant() is True)
    check("T3.12 Uses text encoding (JSON)",
          cloud.uses_binary_encoding() is False)

    # ── T4: Peer-to-Peer Profile ─────────────────────────────────
    print("T4: Peer-to-Peer Profile")
    p2p = PROFILES[ProfileID.PEER_TO_PEER]
    check("T4.1 WebRTC network",
          p2p.protocol_stack.network == NetworkProtocol.WEBRTC)
    check("T4.2 SCTP transport",
          p2p.protocol_stack.transport == TransportProtocol.SCTP)
    check("T4.3 CBOR format",
          p2p.data_config.primary_format == DataFormat.CBOR)
    check("T4.4 W4-BASE-1 suite",
          p2p.crypto_suite.suite_id == CryptoSuiteID.W4_BASE_1)
    check("T4.5 X25519 KEM",
          p2p.crypto_suite.kem == KEM.X25519)
    check("T4.6 Ed25519 signature",
          p2p.crypto_suite.signature == SignatureAlgorithm.ED25519)
    check("T4.7 ChaCha20-Poly1305 AEAD",
          p2p.crypto_suite.aead == AEAD.CHACHA20_POLY1305)
    check("T4.8 Not resource constrained",
          p2p.resource_constrained is False)
    check("T4.9 Binary encoding",
          p2p.uses_binary_encoding() is True)

    # ── T5: Blockchain Bridge Profile ────────────────────────────
    print("T5: Blockchain Bridge Profile")
    chain = PROFILES[ProfileID.BLOCKCHAIN_BRIDGE]
    check("T5.1 JSON format",
          chain.data_config.primary_format == DataFormat.JSON)
    check("T5.2 W4-BASE-1 suite",
          chain.crypto_suite.suite_id == CryptoSuiteID.W4_BASE_1)
    check("T5.3 Supports blockchain",
          chain.supports_blockchain() is True)
    check("T5.4 Has anchoring",
          BlockchainCapability.ANCHORING in chain.blockchain_capabilities)
    check("T5.5 Has timestamping",
          BlockchainCapability.TIMESTAMPING in chain.blockchain_capabilities)
    check("T5.6 Has verification",
          BlockchainCapability.VERIFICATION in chain.blockchain_capabilities)
    check("T5.7 Three blockchain capabilities",
          len(chain.blockchain_capabilities) == 3)

    # ── T6: Crypto Suite Details ─────────────────────────────────
    print("T6: Crypto Suite Details")
    check("T6.1 Three crypto suites",
          len(CryptoSuiteID) == 3)
    check("T6.2 All suites use SHA-256",
          all(p.crypto_suite.hash == HashAlgorithm.SHA256 for p in PROFILES.values()))
    check("T6.3 All suites use HKDF",
          all(p.crypto_suite.kdf == KDF.HKDF for p in PROFILES.values()))

    # IOT vs FIPS vs BASE
    check("T6.4 IOT uses X25519 (compact)",
          PROFILES[ProfileID.EDGE_DEVICE].crypto_suite.kem == KEM.X25519)
    check("T6.5 FIPS uses P-256 (NIST-approved)",
          PROFILES[ProfileID.CLOUD_SERVICE].crypto_suite.kem == KEM.P256ECDH)
    check("T6.6 BASE uses X25519 (general)",
          PROFILES[ProfileID.PEER_TO_PEER].crypto_suite.kem == KEM.X25519)

    # ── T7: Profile Summary ──────────────────────────────────────
    print("T7: Profile Summary")
    for pid, profile in PROFILES.items():
        s = profile.summary()
        check(f"T7.{list(PROFILES.keys()).index(pid)+1} {pid.value} summary has profile",
              s["profile"] == pid.value)
        check(f"T7.{list(PROFILES.keys()).index(pid)+5} {pid.value} summary has suite",
              s["suite"] in [cs.value for cs in CryptoSuiteID])

    # ── T8: Compatibility ────────────────────────────────────────
    print("T8: Profile Compatibility")
    compat = ProfileCompatibility()

    # Same format = can communicate
    check("T8.1 Edge ↔ P2P (both CBOR)",
          compat.can_communicate(edge, p2p))
    check("T8.2 Cloud ↔ Blockchain (both JSON)",
          compat.can_communicate(cloud, chain))

    # Different format = need bridge
    check("T8.3 Edge ↔ Cloud need bridge (CBOR vs JSON)",
          not compat.can_communicate(edge, cloud))
    check("T8.4 P2P ↔ Blockchain need bridge",
          not compat.can_communicate(p2p, chain))

    # Shared crypto
    check("T8.5 P2P ↔ Blockchain share crypto (W4-BASE-1)",
          compat.shared_crypto(p2p, chain))
    check("T8.6 Edge ↔ P2P share kem+sig (X25519+Ed25519)",
          compat.shared_crypto(edge, p2p))
    check("T8.7 Cloud ↔ Edge NO shared crypto",
          not compat.shared_crypto(cloud, edge))

    # Needs bridge
    check("T8.8 Cloud → Edge needs bridge",
          compat.needs_bridge(cloud, edge))
    check("T8.9 P2P → P2P no bridge needed",
          not compat.needs_bridge(p2p, p2p))

    # ── T9: Component Enums ──────────────────────────────────────
    print("T9: Component Enums")
    check("T9.1 Three network protocols",
          len(NetworkProtocol) == 3)
    check("T9.2 Three transport protocols",
          len(TransportProtocol) == 3)
    check("T9.3 Four physical layers",
          len(PhysicalLayer) == 4)
    check("T9.4 Three auth methods",
          len(AuthMethod) == 3)
    check("T9.5 Two data formats",
          len(DataFormat) == 2)
    check("T9.6 Two canonicalizations",
          len(Canonicalization) == 2)
    check("T9.7 Two KEM algorithms",
          len(KEM) == 2)
    check("T9.8 Two signature algorithms",
          len(SignatureAlgorithm) == 2)
    check("T9.9 Three AEAD algorithms",
          len(AEAD) == 3)
    check("T9.10 Three blockchain capabilities",
          len(BlockchainCapability) == 3)

    # ── T10: Edge Cases ──────────────────────────────────────────
    print("T10: Edge Cases")
    # Blockchain bridge has no network protocol (network-agnostic)
    check("T10.1 Blockchain bridge network is None",
          chain.protocol_stack.network is None)
    check("T10.2 Blockchain bridge transport is None",
          chain.protocol_stack.transport is None)
    check("T10.3 Edge has no auth method",
          edge.protocol_stack.auth == AuthMethod.NONE)

    # Only cloud is FIPS
    fips_profiles = [p for p in PROFILES.values() if p.is_fips_compliant()]
    check("T10.4 Only one FIPS profile",
          len(fips_profiles) == 1)
    check("T10.5 Cloud is the FIPS profile",
          fips_profiles[0].profile_id == ProfileID.CLOUD_SERVICE)

    # Only blockchain bridge has blockchain capabilities
    bc_profiles = [p for p in PROFILES.values() if p.supports_blockchain()]
    check("T10.6 Only one blockchain profile",
          len(bc_profiles) == 1)

    # Two profiles use CBOR
    cbor_profiles = [p for p in PROFILES.values() if p.uses_binary_encoding()]
    check("T10.7 Two CBOR profiles (edge, p2p)",
          len(cbor_profiles) == 2)

    # Two profiles use JSON
    json_profiles = [p for p in PROFILES.values() if not p.uses_binary_encoding()]
    check("T10.8 Two JSON profiles (cloud, blockchain)",
          len(json_profiles) == 2)

    # ═══════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"Deployment Profiles: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  ({failed} FAILED)")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
