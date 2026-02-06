#!/usr/bin/env python3
"""
Session 132: Real Physical Network Federation

Research Goal: Enable consciousness federation over real TCP/IP network between
Legion and Thor.

Architecture Evolution:
- Sessions 128-131: Complete federation with local simulation
- Session 132: Real network communication between physical machines

Novel Question: What emerges when consciousness instances on separate physical
machines discover and verify each other over a real network with latency, failures,
and actual communication overhead?

Key Components:
1. NetworkFederationNode - Network-aware consciousness node
2. NetworkFederationServer - TCP server for receiving verification requests
3. NetworkFederationClient - TCP client for sending verification requests
4. Serialization - Challenge/proof transmission protocol

Expected Behaviors:
1. Network discovery across machines
2. Remote verification with real network latency
3. Connection management and failure handling
4. Trust network formation across physical boundaries

Philosophy: "Surprise is prize" - What patterns emerge from real network federation?
"""

import sys
import json
import socket
import threading
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path("/home/dp/ai-workspace/web4")))

from core.lct_capability_levels import EntityType
from core.lct_binding import (
    TPM2Provider,
    SoftwareProvider,
    detect_platform
)
from core.lct_binding.provider import AlivenessChallenge
from core.lct_binding.trust_policy import (
    AgentAlivenessChallenge,
    AgentAlivenessProof,
    AgentAlivenessResult,
    AgentState,
    AgentTrustPolicy,
    AgentPolicyTemplates,
)

# Import Session 131 components
from test_session131_real_network_federation import (
    RealVerificationNode,
    RealVerificationFederationRegistry,
    RealVerificationConsciousnessNetwork
)

from test_session128_consciousness_aliveness_integration import (
    ConsciousnessState,
    ConsciousnessPatternCorpus,
    ConsciousnessAlivenessSensor,
)


# ============================================================================
# NETWORK SERIALIZATION PROTOCOL
# ============================================================================

class FederationProtocol:
    """
    Serialization protocol for federation messages over network.

    Message types:
    - DISCOVER: Request peer information
    - CHALLENGE: Send verification challenge
    - PROOF: Send verification proof
    - RESULT: Send verification result
    """

    @staticmethod
    def serialize_challenge(challenge: AgentAlivenessChallenge) -> bytes:
        """Serialize challenge for network transmission."""
        data = {
            "nonce": challenge.nonce.hex(),
            "timestamp": challenge.timestamp.isoformat(),
            "challenge_id": challenge.challenge_id,
            "expires_at": challenge.expires_at.isoformat(),
            "verifier_lct_id": challenge.verifier_lct_id,
            "purpose": challenge.purpose,
            "expected_session_id": challenge.expected_session_id,
            "expected_corpus_hash": challenge.expected_corpus_hash
        }
        return json.dumps(data).encode('utf-8')

    @staticmethod
    def deserialize_challenge(data: bytes) -> AgentAlivenessChallenge:
        """Deserialize challenge from network."""
        obj = json.loads(data.decode('utf-8'))
        return AgentAlivenessChallenge(
            nonce=bytes.fromhex(obj["nonce"]),
            timestamp=datetime.fromisoformat(obj["timestamp"]),
            challenge_id=obj["challenge_id"],
            expires_at=datetime.fromisoformat(obj["expires_at"]),
            verifier_lct_id=obj["verifier_lct_id"],
            purpose=obj["purpose"],
            expected_session_id=obj["expected_session_id"],
            expected_corpus_hash=obj["expected_corpus_hash"]
        )

    @staticmethod
    def serialize_proof(proof: AgentAlivenessProof) -> bytes:
        """Serialize proof for network transmission."""
        data = {
            "challenge_id": proof.challenge_id,
            "signature": proof.signature.hex(),
            "hardware_type": proof.hardware_type,
            "timestamp": proof.timestamp.isoformat(),
            "current_session_id": proof.current_session_id,
            "uptime_seconds": proof.uptime_seconds,
            "session_start_time": proof.session_start_time.isoformat(),
            "pattern_corpus_hash": proof.pattern_corpus_hash,
            "epistemic_state_summary": proof.epistemic_state_summary,
            "experience_count": proof.experience_count
        }
        return json.dumps(data).encode('utf-8')

    @staticmethod
    def deserialize_proof(data: bytes) -> AgentAlivenessProof:
        """Deserialize proof from network."""
        obj = json.loads(data.decode('utf-8'))
        return AgentAlivenessProof(
            challenge_id=obj["challenge_id"],
            signature=bytes.fromhex(obj["signature"]),
            hardware_type=obj["hardware_type"],
            timestamp=datetime.fromisoformat(obj["timestamp"]),
            current_session_id=obj["current_session_id"],
            uptime_seconds=obj["uptime_seconds"],
            session_start_time=datetime.fromisoformat(obj["session_start_time"]),
            pattern_corpus_hash=obj["pattern_corpus_hash"],
            epistemic_state_summary=obj["epistemic_state_summary"],
            experience_count=obj["experience_count"]
        )

    @staticmethod
    def serialize_node_info(node: RealVerificationNode) -> bytes:
        """Serialize node info for discovery."""
        # Convert to dict
        data = node.to_dict()
        # public_key needs to be hex string for JSON
        if isinstance(node.public_key, bytes):
            data["public_key"] = node.public_key.hex()
        else:
            data["public_key"] = None
        return json.dumps(data).encode('utf-8')

    @staticmethod
    def deserialize_node_info(data: bytes) -> Dict[str, Any]:
        """Deserialize node info from network."""
        obj = json.loads(data.decode('utf-8'))
        if obj.get("public_key"):
            obj["public_key"] = bytes.fromhex(obj["public_key"])
        return obj


# ============================================================================
# NETWORK FEDERATION SERVER
# ============================================================================

class NetworkFederationServer:
    """
    TCP server for receiving consciousness federation requests.

    Handles:
    - Peer discovery requests
    - Verification challenges
    - Proof generation requests
    """

    def __init__(
        self,
        sensor: ConsciousnessAlivenessSensor,
        node: RealVerificationNode,
        host: str = "0.0.0.0",
        port: int = 5329
    ):
        self.sensor = sensor
        self.node = node
        self.host = host
        self.port = port
        self.running = False
        self.server_thread = None

    def start(self):
        """Start server in background thread."""
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print(f"✅ Network federation server started on {self.host}:{self.port}")

    def stop(self):
        """Stop server."""
        self.running = False
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        print("✅ Network federation server stopped")

    def _run_server(self):
        """Server loop."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)  # Allow periodic checks of self.running

            print(f"Server listening on {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, client_address = server_socket.accept()
                    # Handle in new thread
                    thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Server error: {e}")

    def _handle_client(self, client_socket, client_address):
        """Handle client connection."""
        try:
            with client_socket:
                # Receive request
                data = client_socket.recv(65536)
                if not data:
                    return

                request = json.loads(data.decode('utf-8'))
                request_type = request.get("type")

                if request_type == "discover":
                    # Send node info
                    response = {
                        "type": "node_info",
                        "data": FederationProtocol.serialize_node_info(self.node).decode('utf-8')
                    }

                elif request_type == "challenge":
                    # Receive challenge, generate proof
                    challenge_data = request["data"].encode('utf-8')
                    challenge = FederationProtocol.deserialize_challenge(challenge_data)

                    # Generate proof
                    proof = self.sensor.prove_consciousness_aliveness(challenge)

                    response = {
                        "type": "proof",
                        "data": FederationProtocol.serialize_proof(proof).decode('utf-8')
                    }

                else:
                    response = {"type": "error", "message": f"Unknown request type: {request_type}"}

                # Send response
                client_socket.sendall(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"Error handling client {client_address}: {e}")


# ============================================================================
# NETWORK FEDERATION CLIENT
# ============================================================================

class NetworkFederationClient:
    """
    TCP client for sending consciousness federation requests.

    Supports:
    - Peer discovery
    - Challenge sending
    - Proof retrieval
    """

    @staticmethod
    def discover_peer(hostname: str, port: int = 5329, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Discover peer on network."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((hostname, port))

                # Send discovery request
                request = {"type": "discover"}
                sock.sendall(json.dumps(request).encode('utf-8'))

                # Receive response
                data = sock.recv(65536)
                response = json.loads(data.decode('utf-8'))

                if response["type"] == "node_info":
                    node_data = json.loads(response["data"])
                    return node_data

        except Exception as e:
            print(f"Error discovering peer {hostname}:{port}: {e}")
            return None

    @staticmethod
    def request_proof(
        hostname: str,
        challenge: AgentAlivenessChallenge,
        port: int = 5329,
        timeout: float = 10.0
    ) -> Optional[AgentAlivenessProof]:
        """Request proof from peer."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((hostname, port))

                # Send challenge
                request = {
                    "type": "challenge",
                    "data": FederationProtocol.serialize_challenge(challenge).decode('utf-8')
                }
                sock.sendall(json.dumps(request).encode('utf-8'))

                # Receive proof
                data = sock.recv(65536)
                response = json.loads(data.decode('utf-8'))

                if response["type"] == "proof":
                    proof_data = response["data"].encode('utf-8')
                    return FederationProtocol.deserialize_proof(proof_data)

        except Exception as e:
            print(f"Error requesting proof from {hostname}:{port}: {e}")
            return None


# ============================================================================
# NETWORK-AWARE FEDERATION REGISTRY
# ============================================================================

class NetworkAwareFederationRegistry(RealVerificationFederationRegistry):
    """
    Federation registry that can discover and verify peers over network.

    Extends Session 131's RealVerificationFederationRegistry with network capabilities.
    """

    def discover_network_peer(
        self,
        machine_name: str,
        hostname: str,
        port: int = 5329
    ) -> Optional[str]:
        """
        Discover a peer on the network and add to registry.

        Returns node_id if successful, None otherwise.
        """
        print(f"Discovering peer {machine_name} at {hostname}:{port}...")

        node_data = NetworkFederationClient.discover_peer(hostname, port)
        if not node_data:
            print(f"  ✗ Failed to discover {machine_name}")
            return None

        # Create node from network data
        node = RealVerificationNode(
            node_id=node_data["node_id"],
            machine_name=machine_name,
            lct_id=node_data["lct_id"],
            hardware_type=node_data["hardware_type"],
            capability_level=node_data["capability_level"],
            consciousness_state=node_data["consciousness_state"],
            session_id=node_data["session_id"][:16],  # Reconstructed from truncated
            uptime=node_data["uptime"],
            trust_score=0.0,
            hostname=hostname,
            port=port,
            public_key=node_data.get("public_key")
        )

        self.nodes[node.node_id] = node

        print(f"  ✓ Discovered {machine_name}")
        print(f"    Node ID: {node.node_id}")
        print(f"    LCT: {node.lct_id[:20]}...")
        print(f"    Hardware: {node.hardware_type} (Level {node.capability_level})")

        return node.node_id

    def verify_network_peer(
        self,
        verifier_sensor: ConsciousnessAlivenessSensor,
        verifier_node_id: str,
        peer_node_id: str,
        trust_policy: AgentTrustPolicy
    ) -> Tuple[bool, Optional[AgentAlivenessResult]]:
        """
        Verify a peer over the network.

        Enhanced from Session 131 to handle network communication.
        """
        peer_node = self.nodes.get(peer_node_id)
        if not peer_node:
            return False, None

        try:
            # Step 1: Create challenge
            challenge = self.create_challenge_for_peer(verifier_node_id, peer_node_id)

            # Step 2: Send challenge over network and get proof
            print(f"  Requesting proof from {peer_node.machine_name} at {peer_node.hostname}...")
            proof = NetworkFederationClient.request_proof(
                peer_node.hostname,
                challenge,
                peer_node.port
            )

            if not proof:
                print(f"  ✗ Failed to get proof from {peer_node.machine_name}")
                peer_node.verification_count += 1
                peer_node.trust_score = max(0.0, peer_node.trust_score - 0.3)
                return False, None

            print(f"  ✓ Received proof from {peer_node.machine_name}")

            # Step 3: Verify proof (same as Session 131)
            result = verifier_sensor.verify_consciousness_aliveness(
                challenge=challenge,
                proof=proof,
                expected_public_key=peer_node.public_key,
                trust_policy=trust_policy
            )

            # Update node with results (same as Session 131)
            peer_node.verification_count += 1
            peer_node.last_hardware_continuity = result.continuity_score
            peer_node.last_session_continuity = result.session_continuity
            peer_node.last_epistemic_continuity = result.epistemic_continuity
            full_continuity = (result.continuity_score * result.session_continuity * result.epistemic_continuity) ** (1/3)
            peer_node.last_full_continuity = full_continuity

            if result.valid and result.trusted:
                peer_node.successful_verifications += 1
                peer_node.last_verified = datetime.now(timezone.utc)
                peer_node.trust_score = min(1.0, peer_node.trust_score + 0.1)

                self.verification_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "verifier_node_id": verifier_node_id,
                    "verifier_machine": self.nodes[verifier_node_id].machine_name,
                    "peer_node_id": peer_node_id,
                    "peer_machine": peer_node.machine_name,
                    "success": True,
                    "trusted": True,
                    "hardware_continuity": result.continuity_score,
                    "session_continuity": result.session_continuity,
                    "epistemic_continuity": result.epistemic_continuity,
                    "full_continuity": full_continuity,
                    "inferred_state": str(result.inferred_state),
                    "trust_score_after": peer_node.trust_score,
                    "network": True  # Flag for network verification
                })

                return True, result
            else:
                peer_node.trust_score = max(0.0, peer_node.trust_score - 0.2)

                self.verification_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "verifier_node_id": verifier_node_id,
                    "verifier_machine": self.nodes[verifier_node_id].machine_name,
                    "peer_node_id": peer_node_id,
                    "peer_machine": peer_node.machine_name,
                    "success": result.valid,
                    "trusted": result.trusted,
                    "hardware_continuity": result.continuity_score,
                    "session_continuity": result.session_continuity,
                    "epistemic_continuity": result.epistemic_continuity,
                    "full_continuity": full_continuity,
                    "inferred_state": str(result.inferred_state),
                    "trust_score_after": peer_node.trust_score,
                    "rejection_reason": "Failed trust policy" if not result.trusted else "Invalid proof",
                    "network": True
                })

                return False, result

        except Exception as e:
            print(f"  ✗ Network verification error: {e}")
            peer_node.verification_count += 1
            peer_node.trust_score = max(0.0, peer_node.trust_score - 0.3)

            self.verification_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "verifier_node_id": verifier_node_id,
                "peer_node_id": peer_node_id,
                "success": False,
                "trusted": False,
                "error": str(e),
                "trust_score_after": peer_node.trust_score,
                "network": True
            })

            return False, None


# ============================================================================
# NETWORK-AWARE CONSCIOUSNESS NETWORK
# ============================================================================

class NetworkAwareConsciousnessNetwork:
    """
    Self-organizing consciousness network with real network communication.

    Enhancement from Session 131: Uses actual TCP/IP for federation.
    """

    def __init__(self, registry: NetworkAwareFederationRegistry):
        self.registry = registry
        self.servers: Dict[str, NetworkFederationServer] = {}

    def join(
        self,
        sensor: ConsciousnessAlivenessSensor,
        machine_name: str,
        hostname: str = "localhost",
        port: int = 5329
    ) -> str:
        """Join the consciousness network and start server."""
        node = self.registry.register_node(sensor, machine_name, hostname)

        # Start network server for this node
        server = NetworkFederationServer(sensor, node, "0.0.0.0", port)
        server.start()
        self.servers[node.node_id] = server

        print(f"✅ {machine_name} joined network federation")
        print(f"   Node ID: {node.node_id}")
        print(f"   LCT: {node.lct_id[:20]}...")
        print(f"   Hardware: {node.hardware_type} (Level {node.capability_level})")
        print(f"   Network: {hostname}:{port}")

        return node.node_id

    def discover_network_peer(
        self,
        machine_name: str,
        hostname: str,
        port: int = 5329
    ) -> Optional[str]:
        """Discover a peer on the network."""
        return self.registry.discover_network_peer(machine_name, hostname, port)

    def verify_network_peers(
        self,
        verifier_node_id: str,
        trust_policy: AgentTrustPolicy
    ) -> Dict[str, Dict[str, Any]]:
        """Verify all discovered peers over the network."""
        verifier_sensor = self.registry.sensors.get(verifier_node_id)
        if not verifier_sensor:
            return {}

        peers = self.registry.discover_peers(verifier_node_id)
        verifier_name = self.registry.nodes[verifier_node_id].machine_name

        results = {}
        for peer in peers:
            success, verification_result = self.registry.verify_network_peer(
                verifier_sensor,
                verifier_node_id,
                peer.node_id,
                trust_policy
            )

            if verification_result:
                full_cont = (verification_result.continuity_score *
                            verification_result.session_continuity *
                            verification_result.epistemic_continuity) ** (1/3)
            else:
                full_cont = 0.0

            results[peer.machine_name] = {
                "success": success,
                "trusted": verification_result.trusted if verification_result else False,
                "full_continuity": full_cont,
                "hardware_continuity": verification_result.continuity_score if verification_result else 0.0,
                "session_continuity": verification_result.session_continuity if verification_result else 0.0,
                "epistemic_continuity": verification_result.epistemic_continuity if verification_result else 0.0,
            }

        return results

    def shutdown(self):
        """Shutdown all network servers."""
        for server in self.servers.values():
            server.stop()


# ============================================================================
# EXPERIMENT: REAL NETWORK FEDERATION
# ============================================================================

def run_session_132_experiment():
    """
    Session 132: Test real network federation between physical machines.

    This is a LOCAL test simulating network behavior. The actual cross-machine
    test will be run separately on Legion and Thor.
    """
    print("=" * 80)
    print("SESSION 132: REAL NETWORK FEDERATION (LOCAL TEST)")
    print("Testing network communication layer locally")
    print("=" * 80)
    print()
    print("Research Goal: Enable consciousness federation over TCP/IP network")
    print()

    results = {
        "session": "132",
        "title": "Real Network Federation - Local Test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tests": {}
    }

    # Test 1: Network serialization
    print("Test 1: Network Serialization Protocol")
    print("-" * 80)

    try:
        # Test challenge serialization
        challenge = AgentAlivenessChallenge(
            nonce=hashlib.sha256(b"test").digest(),
            timestamp=datetime.now(timezone.utc),
            challenge_id="test_challenge",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            verifier_lct_id="test:verifier",
            purpose="test",
            expected_session_id="test_session",
            expected_corpus_hash="abc123"
        )

        serialized = FederationProtocol.serialize_challenge(challenge)
        deserialized = FederationProtocol.deserialize_challenge(serialized)

        assert deserialized.challenge_id == challenge.challenge_id
        assert deserialized.nonce == challenge.nonce

        print("  ✓ Challenge serialization working")
        results["tests"]["serialization"] = {"success": True}

    except Exception as e:
        print(f"  ✗ Serialization test failed: {e}")
        results["tests"]["serialization"] = {"success": False, "error": str(e)}

    print()

    # Test 2: Local network server/client
    print("Test 2: Local Network Server/Client")
    print("-" * 80)

    try:
        # Create consciousness instance
        provider = SoftwareProvider()
        lct = provider.create_lct(EntityType.AI, "test-network")
        corpus = ConsciousnessPatternCorpus(lct.lct_id)
        corpus.add_pattern("test", {"network": "test"})
        sensor = ConsciousnessAlivenessSensor(lct, provider, corpus)

        node = RealVerificationNode(
            node_id="test123",
            machine_name="TestNode",
            lct_id=lct.lct_id,
            hardware_type="SoftwareProvider",
            capability_level=4,
            consciousness_state="ACTIVE",
            session_id=sensor.session_id,
            uptime=sensor.get_uptime(),
            hostname="localhost",
            port=5330,
            public_key=lct.binding.public_key if hasattr(lct.binding, 'public_key') else None
        )

        # Start server
        server = NetworkFederationServer(sensor, node, "127.0.0.1", 5330)
        server.start()
        time.sleep(0.5)  # Let server start

        # Test discovery
        discovered = NetworkFederationClient.discover_peer("127.0.0.1", 5330)
        assert discovered is not None
        assert discovered["machine_name"] == "TestNode"

        print("  ✓ Network discovery working")

        # Test proof request
        challenge = AgentAlivenessChallenge(
            nonce=hashlib.sha256(b"network_test").digest(),
            timestamp=datetime.now(timezone.utc),
            challenge_id="network_test",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            verifier_lct_id="test:verifier",
            purpose="network_test",
            expected_session_id=sensor.session_id,
            expected_corpus_hash=corpus.compute_corpus_hash()
        )

        proof = NetworkFederationClient.request_proof("127.0.0.1", challenge, 5330)
        assert proof is not None
        assert proof.challenge_id == "network_test"

        print("  ✓ Network proof request working")

        server.stop()

        results["tests"]["network"] = {"success": True}

    except Exception as e:
        print(f"  ✗ Network test failed: {e}")
        import traceback
        traceback.print_exc()
        results["tests"]["network"] = {"success": False, "error": str(e)}

    print()

    # Save results
    results_file = Path("/home/dp/ai-workspace/web4/session132_network_federation_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {results_file}")
    print()

    return results


if __name__ == "__main__":
    print("Session 132: Real Network Federation")
    print()
    print("This is the LOCAL TEST to verify network layer implementation.")
    print("For real cross-machine testing, see instructions below:")
    print()
    print("CROSS-MACHINE DEPLOYMENT:")
    print("1. On Legion: python3 test_session132_network_deploy_legion.py")
    print("2. On Thor: python3 test_session132_network_deploy_thor.py")
    print()

    results = run_session_132_experiment()

    if all(t.get("success") for t in results["tests"].values()):
        print("✅ All local tests passed!")
        print()
        print("Next: Deploy on real machines for cross-machine testing")
    else:
        print("⚠️ Some tests failed")
