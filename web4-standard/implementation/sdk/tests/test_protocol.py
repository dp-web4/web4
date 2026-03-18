"""
Tests for web4.protocol — Core protocol types.

Validates handshake messages, pairing methods, transport profiles,
discovery mechanisms, Web4 URI parsing, and transport negotiation
per core-protocol.md.
"""

import json
import pathlib
import pytest

from web4.protocol import (
    HandshakePhase,
    ClientHello,
    ServerHello,
    ClientFinished,
    ServerFinished,
    HandshakeMessage,
    PairingMethod,
    Transport,
    TransportCompliance,
    TransportProfile,
    TRANSPORT_PROFILES,
    get_transport_profile,
    required_transports,
    negotiate_transport,
    DiscoveryMethod,
    PrivacyLevel,
    DISCOVERY_METADATA,
    required_discovery_methods,
    discovery_privacy,
    DiscoveryRequest,
    DiscoveryResponse,
    Web4URI,
    web4_uri_to_dict,
    web4_uri_from_dict,
    transport_profile_to_dict,
)


# ── Fixtures ──────────────────────────────────────────────────────

VECTORS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "test-vectors" / "protocol"


@pytest.fixture
def vectors():
    """Load cross-language test vectors."""
    with open(VECTORS_DIR / "core-protocol.json") as f:
        data = json.load(f)
    return {v["name"]: v for v in data["vectors"]}


# ── Handshake Phase Tests ────────────────────────────────────────

class TestHandshakePhase:
    def test_phase_ordering(self):
        assert HandshakePhase.CLIENT_HELLO < HandshakePhase.SERVER_HELLO
        assert HandshakePhase.SERVER_HELLO < HandshakePhase.CLIENT_FINISHED
        assert HandshakePhase.CLIENT_FINISHED < HandshakePhase.SERVER_FINISHED

    def test_all_phases_present(self):
        phases = list(HandshakePhase)
        assert len(phases) == 4


class TestClientHello:
    def test_basic_construction(self):
        ch = ClientHello(
            supported_suites=["W4-BASE-1"],
            client_public_key="ed25519:pk_abc",
            client_w4id_ephemeral="w4id:key:eph001",
            nonce="deadbeef",
        )
        assert ch.phase == HandshakePhase.CLIENT_HELLO
        assert len(ch.supported_suites) == 1
        assert ch.nonce == "deadbeef"

    def test_multiple_suites(self):
        ch = ClientHello(
            supported_suites=["W4-BASE-1", "W4-FIPS-1"],
            client_public_key="ed25519:pk_abc",
            client_w4id_ephemeral="w4id:key:eph001",
            nonce="abc123",
        )
        assert len(ch.supported_suites) == 2

    def test_empty_suites_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            ClientHello(
                supported_suites=[],
                client_public_key="pk",
                client_w4id_ephemeral="eph",
                nonce="nonce",
            )

    def test_empty_nonce_raises(self):
        with pytest.raises(ValueError, match="nonce"):
            ClientHello(
                supported_suites=["W4-BASE-1"],
                client_public_key="pk",
                client_w4id_ephemeral="eph",
                nonce="",
            )

    def test_grease_extensions(self):
        ch = ClientHello(
            supported_suites=["W4-BASE-1"],
            client_public_key="pk",
            client_w4id_ephemeral="eph",
            nonce="nonce",
            grease_extensions=["grease_0a0a"],
        )
        assert ch.grease_extensions == ["grease_0a0a"]


class TestServerHello:
    def test_basic_construction(self):
        sh = ServerHello(
            selected_suite="W4-BASE-1",
            server_public_key="ed25519:pk_server",
            server_w4id_ephemeral="w4id:key:eph002",
            nonce="cafebabe",
        )
        assert sh.phase == HandshakePhase.SERVER_HELLO
        assert sh.selected_suite == "W4-BASE-1"

    def test_with_encrypted_credentials(self):
        sh = ServerHello(
            selected_suite="W4-FIPS-1",
            server_public_key="p256:pk_server",
            server_w4id_ephemeral="w4id:key:eph002",
            nonce="cafebabe",
            encrypted_credentials="enc:cred:data",
        )
        assert sh.encrypted_credentials == "enc:cred:data"

    def test_empty_suite_raises(self):
        with pytest.raises(ValueError, match="select a suite"):
            ServerHello(
                selected_suite="",
                server_public_key="pk",
                server_w4id_ephemeral="eph",
                nonce="nonce",
            )

    def test_empty_nonce_raises(self):
        with pytest.raises(ValueError, match="nonce"):
            ServerHello(
                selected_suite="W4-BASE-1",
                server_public_key="pk",
                server_w4id_ephemeral="eph",
                nonce="",
            )


class TestClientFinished:
    def test_basic_construction(self):
        cf = ClientFinished(
            encrypted_credentials="enc:client:creds",
            transcript_mac="mac:abc123",
        )
        assert cf.phase == HandshakePhase.CLIENT_FINISHED
        assert cf.transcript_mac == "mac:abc123"

    def test_empty_mac_raises(self):
        with pytest.raises(ValueError, match="transcript MAC"):
            ClientFinished(encrypted_credentials="creds", transcript_mac="")


class TestServerFinished:
    def test_basic_construction(self):
        sf = ServerFinished(
            transcript_mac="mac:final",
            session_id="sess:001",
        )
        assert sf.phase == HandshakePhase.SERVER_FINISHED
        assert sf.session_id == "sess:001"

    def test_empty_mac_raises(self):
        with pytest.raises(ValueError, match="transcript MAC"):
            ServerFinished(transcript_mac="", session_id="sess:001")

    def test_empty_session_id_raises(self):
        with pytest.raises(ValueError, match="session_id"):
            ServerFinished(transcript_mac="mac", session_id="")


class TestHandshakeMessage:
    def test_envelope_wraps_client_hello(self):
        ch = ClientHello(
            supported_suites=["W4-BASE-1"],
            client_public_key="pk",
            client_w4id_ephemeral="eph",
            nonce="nonce",
        )
        msg = HandshakeMessage(phase=HandshakePhase.CLIENT_HELLO, payload=ch)
        assert msg.transport == Transport.TLS_1_3

    def test_to_dict_client_hello(self):
        ch = ClientHello(
            supported_suites=["W4-BASE-1", "W4-FIPS-1"],
            client_public_key="ed25519:pk_abc",
            client_w4id_ephemeral="w4id:key:eph001",
            nonce="a1b2c3",
        )
        msg = HandshakeMessage(phase=HandshakePhase.CLIENT_HELLO, payload=ch)
        d = msg.to_dict()
        assert d["phase"] == "CLIENT_HELLO"
        assert d["payload"]["supported_suites"] == ["W4-BASE-1", "W4-FIPS-1"]
        assert d["payload"]["nonce"] == "a1b2c3"

    def test_to_dict_server_finished(self):
        sf = ServerFinished(transcript_mac="mac:done", session_id="sess:42")
        msg = HandshakeMessage(
            phase=HandshakePhase.SERVER_FINISHED,
            payload=sf,
            transport=Transport.QUIC,
        )
        d = msg.to_dict()
        assert d["phase"] == "SERVER_FINISHED"
        assert d["transport"] == "quic"
        assert d["payload"]["session_id"] == "sess:42"


# ── Pairing Method Tests ─────────────────────────────────────────

class TestPairingMethod:
    def test_all_methods(self):
        methods = list(PairingMethod)
        assert len(methods) == 3
        assert PairingMethod.DIRECT in methods
        assert PairingMethod.MEDIATED in methods
        assert PairingMethod.QR_CODE in methods

    def test_string_values(self):
        assert PairingMethod.DIRECT.value == "direct"
        assert PairingMethod.MEDIATED.value == "mediated"
        assert PairingMethod.QR_CODE.value == "qr_code"


# ── Transport Tests ──────────────────────────────────────────────

class TestTransport:
    def test_all_transports(self):
        transports = list(Transport)
        assert len(transports) == 8

    def test_required_transports(self, vectors):
        required = required_transports()
        v = vectors["transport_required"]
        required_ids = [t.value for t in required]
        assert set(required_ids) == set(v["expected"]["required_transports"])

    def test_constrained_transports(self, vectors):
        v = vectors["transport_required"]
        constrained = [t for t, p in TRANSPORT_PROFILES.items() if p.compressed_handshake]
        constrained_ids = [t.value for t in constrained]
        assert set(constrained_ids) == set(v["expected"]["constrained_transports"])


class TestTransportProfile:
    def test_tls_profile(self):
        profile = get_transport_profile(Transport.TLS_1_3)
        assert profile.compliance == TransportCompliance.MUST
        assert "web" in profile.use_cases
        assert profile.full_metering is True

    def test_ble_profile(self):
        profile = get_transport_profile(Transport.BLE_GATT)
        assert profile.compliance == TransportCompliance.MAY
        assert profile.compressed_handshake is True
        assert profile.limited_metering is True
        assert profile.full_metering is False

    def test_all_profiles_exist(self):
        for t in Transport:
            assert t in TRANSPORT_PROFILES

    def test_to_dict(self):
        profile = get_transport_profile(Transport.QUIC)
        d = transport_profile_to_dict(profile)
        assert d["transport_id"] == "quic"
        assert d["compliance"] == "MUST"
        assert d["compressed_handshake"] is False


class TestTransportNegotiation:
    def test_negotiate_mutual(self, vectors):
        v = vectors["transport_negotiate_mutual"]
        client = [Transport(t) for t in v["input"]["client_transports"]]
        server = [Transport(t) for t in v["input"]["server_transports"]]
        result = negotiate_transport(client, server)
        assert result is not None
        assert result.value == v["expected"]["selected"]

    def test_negotiate_fallback(self, vectors):
        v = vectors["transport_negotiate_fallback"]
        client = [Transport(t) for t in v["input"]["client_transports"]]
        server = [Transport(t) for t in v["input"]["server_transports"]]
        result = negotiate_transport(client, server)
        assert result is not None
        assert result.value == v["expected"]["selected"]

    def test_negotiate_no_match(self, vectors):
        v = vectors["transport_negotiate_no_match"]
        client = [Transport(t) for t in v["input"]["client_transports"]]
        server = [Transport(t) for t in v["input"]["server_transports"]]
        result = negotiate_transport(client, server)
        assert result is None

    def test_negotiate_client_priority(self):
        """Client's priority order determines selection."""
        result = negotiate_transport(
            [Transport.QUIC, Transport.TLS_1_3],
            [Transport.TLS_1_3, Transport.QUIC],
        )
        assert result == Transport.QUIC


# ── Discovery Tests ──────────────────────────────────────────────

class TestDiscoveryMethod:
    def test_all_methods(self):
        methods = list(DiscoveryMethod)
        assert len(methods) == 6

    def test_required_methods(self, vectors):
        required = required_discovery_methods()
        v = vectors["discovery_required"]
        required_ids = [m.value for m in required]
        assert set(required_ids) == set(v["expected"]["required_methods"])

    def test_privacy_levels(self, vectors):
        v = vectors["discovery_required"]
        high_privacy = [m for m in DiscoveryMethod
                        if discovery_privacy(m) == PrivacyLevel.HIGH]
        high_ids = [m.value for m in high_privacy]
        assert set(high_ids) == set(v["expected"]["high_privacy_methods"])

    def test_witness_relay_is_must(self):
        meta = DISCOVERY_METADATA[DiscoveryMethod.WITNESS_RELAY]
        assert meta["compliance"] == TransportCompliance.MUST

    def test_qr_code_high_privacy(self):
        assert discovery_privacy(DiscoveryMethod.QR_CODE_OOB) == PrivacyLevel.HIGH


class TestDiscoveryRequest:
    def test_basic_construction(self):
        req = DiscoveryRequest(
            desired_capabilities=["database_query", "compute"],
            acceptable_witnesses=["lct:witness1"],
            nonce="replay_guard",
        )
        assert len(req.desired_capabilities) == 2
        assert req.nonce == "replay_guard"

    def test_empty_request(self):
        req = DiscoveryRequest(desired_capabilities=[])
        assert len(req.acceptable_witnesses) == 0


class TestDiscoveryResponse:
    def test_empty_response(self):
        resp = DiscoveryResponse()
        assert len(resp.entities) == 0

    def test_with_entities(self):
        resp = DiscoveryResponse(
            entities=[{"lct_id": "lct:web4:server:001", "endpoint": "web4://server"}],
            witness_attestations=[{"witness": "w1", "signature": "sig1"}],
        )
        assert len(resp.entities) == 1
        assert len(resp.witness_attestations) == 1


# ── Web4 URI Tests ───────────────────────────────────────────────

class TestWeb4URI:
    def test_parse_basic(self, vectors):
        v = vectors["web4_uri_basic"]
        uri = Web4URI.parse(v["input"]["uri"])
        assert uri.w4id == v["expected"]["w4id"]
        assert uri.path == v["expected"]["path"]
        assert uri.query is None
        assert uri.fragment is None
        assert str(uri) == v["expected"]["reconstructed"]

    def test_parse_with_query_and_fragment(self, vectors):
        v = vectors["web4_uri_with_query_and_fragment"]
        uri = Web4URI.parse(v["input"]["uri"])
        assert uri.w4id == v["expected"]["w4id"]
        assert uri.path == v["expected"]["path"]
        assert uri.query == v["expected"]["query"]
        assert uri.fragment == v["expected"]["fragment"]
        assert str(uri) == v["expected"]["reconstructed"]

    def test_parse_root_path(self, vectors):
        v = vectors["web4_uri_root_path"]
        uri = Web4URI.parse(v["input"]["uri"])
        assert uri.w4id == v["expected"]["w4id"]
        assert uri.path == v["expected"]["path"]
        assert uri.query is None
        assert uri.fragment is None
        assert str(uri) == v["expected"]["reconstructed"]

    def test_parse_fragment_only(self, vectors):
        v = vectors["web4_uri_with_fragment_only"]
        uri = Web4URI.parse(v["input"]["uri"])
        assert uri.w4id == v["expected"]["w4id"]
        assert uri.path == v["expected"]["path"]
        assert uri.query is None
        assert uri.fragment == v["expected"]["fragment"]
        assert str(uri) == v["expected"]["reconstructed"]

    def test_invalid_scheme(self, vectors):
        v = vectors["web4_uri_invalid_scheme"]
        assert Web4URI.is_valid(v["input"]["uri"]) is False
        with pytest.raises(ValueError):
            Web4URI.parse(v["input"]["uri"])

    def test_empty_w4id(self, vectors):
        v = vectors["web4_uri_empty_w4id"]
        assert Web4URI.is_valid(v["input"]["uri"]) is False

    def test_is_valid_positive(self):
        assert Web4URI.is_valid("web4://w4id:key:test/path") is True

    def test_is_valid_negative(self):
        assert Web4URI.is_valid("http://example.com") is False
        assert Web4URI.is_valid("") is False
        assert Web4URI.is_valid("web4://") is False

    def test_constructor_empty_w4id_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Web4URI(w4id="")

    def test_frozen(self):
        uri = Web4URI(w4id="test:id", path="/path")
        with pytest.raises(AttributeError):
            uri.w4id = "other"  # type: ignore

    def test_round_trip_dict(self):
        uri = Web4URI(w4id="w4id:key:abc", path="/data", query="x=1", fragment="top")
        d = web4_uri_to_dict(uri)
        restored = web4_uri_from_dict(d)
        assert restored == uri
        assert d["uri_string"] == str(uri)

    def test_round_trip_dict_no_optional(self):
        uri = Web4URI(w4id="w4id:key:abc", path="/")
        d = web4_uri_to_dict(uri)
        assert "query" not in d
        assert "fragment" not in d
        restored = web4_uri_from_dict(d)
        assert restored == uri


# ── Cross-Language Vector Tests ──────────────────────────────────

class TestVectors:
    def test_handshake_client_hello(self, vectors):
        v = vectors["handshake_client_hello"]
        inp = v["input"]
        ch = ClientHello(
            supported_suites=inp["supported_suites"],
            client_public_key=inp["client_public_key"],
            client_w4id_ephemeral=inp["client_w4id_ephemeral"],
            nonce=inp["nonce"],
        )
        assert ch.phase.name == v["expected"]["phase"]
        assert len(ch.supported_suites) == v["expected"]["suite_count"]
        assert bool(ch.nonce) == v["expected"]["has_nonce"]

    def test_all_vectors_loaded(self, vectors):
        """Sanity: ensure test vector file has expected count."""
        assert len(vectors) == 12
