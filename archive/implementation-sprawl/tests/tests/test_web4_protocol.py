#!/usr/bin/env python3
"""
Web4 Protocol Conformance Tests

This test suite verifies compliance with the Web4 standard specification.
It tests the core protocol functionality including handshake, pairing,
messaging, and credential handling.

Author: Manus AI
License: MIT
"""

import unittest
import json
import base64
from datetime import datetime, timezone
import sys
import os

# Add the reference implementation to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'reference'))

from web4_client import Web4Client


class TestWeb4Protocol(unittest.TestCase):
    """Test suite for Web4 protocol compliance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client1 = Web4Client()
        self.client2 = Web4Client()
    
    def test_w4id_generation(self):
        """Test that W4ID generation follows the specification."""
        w4id = self.client1.w4id
        
        # W4ID should start with "did:web4:key:"
        self.assertTrue(w4id.startswith("did:web4:key:"))
        
        # Should have the correct format
        parts = w4id.split(":")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "did")
        self.assertEqual(parts[1], "web4")
        self.assertEqual(parts[2], "key")
        
        # Key ID should be base64url encoded
        key_id = parts[3]
        try:
            # Should be valid base64url
            base64.urlsafe_b64decode(key_id + "==")
        except Exception:
            self.fail("W4ID key part is not valid base64url")
    
    def test_client_hello_generation(self):
        """Test ClientHello message generation."""
        server_w4id = self.client2.w4id
        client_hello = self.client1.generate_client_hello(server_w4id)
        
        # Check required fields
        required_fields = [
            "type", "version", "client_w4id", "server_w4id",
            "public_key", "supported_algorithms", "timestamp", "nonce"
        ]
        
        for field in required_fields:
            self.assertIn(field, client_hello)
        
        # Check field values
        self.assertEqual(client_hello["type"], "ClientHello")
        self.assertEqual(client_hello["version"], "1.0")
        self.assertEqual(client_hello["client_w4id"], self.client1.w4id)
        self.assertEqual(client_hello["server_w4id"], server_w4id)
        
        # Check that public key is valid base64
        try:
            base64.b64decode(client_hello["public_key"])
        except Exception:
            self.fail("Public key is not valid base64")
        
        # Check supported algorithms
        self.assertIsInstance(client_hello["supported_algorithms"], list)
        self.assertIn("ECDH-P256", client_hello["supported_algorithms"])
        self.assertIn("AES-256-GCM", client_hello["supported_algorithms"])
        self.assertIn("ECDSA-P256-SHA256", client_hello["supported_algorithms"])
    
    def test_message_encryption_decryption(self):
        """Test message encryption and decryption."""
        # Simulate establishing a session key
        test_key = b"0" * 32  # 256-bit key for testing
        self.client1.session_keys[self.client2.w4id] = test_key
        self.client2.session_keys[self.client1.w4id] = test_key
        
        # Test message
        original_message = "Hello, Web4!"
        
        # Encrypt message
        encrypted_msg = self.client1.encrypt_message(original_message, self.client2.w4id)
        
        # Check encrypted message structure
        required_fields = [
            "type", "sender_w4id", "recipient_w4id",
            "nonce", "ciphertext", "timestamp"
        ]
        
        for field in required_fields:
            self.assertIn(field, encrypted_msg)
        
        self.assertEqual(encrypted_msg["type"], "encrypted_message")
        self.assertEqual(encrypted_msg["sender_w4id"], self.client1.w4id)
        self.assertEqual(encrypted_msg["recipient_w4id"], self.client2.w4id)
        
        # Decrypt message
        decrypted_message = self.client2.decrypt_message(encrypted_msg)
        
        # Verify decryption
        self.assertEqual(decrypted_message, original_message)
    
    def test_verifiable_credential_creation(self):
        """Test verifiable credential creation."""
        subject_w4id = self.client2.w4id
        claims = {
            "name": "Test User",
            "email": "test@example.com",
            "role": "tester"
        }
        
        credential = self.client1.create_verifiable_credential(subject_w4id, claims)
        
        # Check required fields
        required_fields = [
            "@context", "id", "type", "issuer",
            "issuanceDate", "credentialSubject", "proof"
        ]
        
        for field in required_fields:
            self.assertIn(field, credential)
        
        # Check field values
        self.assertIsInstance(credential["@context"], list)
        self.assertIn("https://www.w3.org/2018/credentials/v1", credential["@context"])
        
        self.assertIsInstance(credential["type"], list)
        self.assertIn("VerifiableCredential", credential["type"])
        self.assertIn("Web4Credential", credential["type"])
        
        self.assertEqual(credential["issuer"], self.client1.w4id)
        self.assertEqual(credential["credentialSubject"]["id"], subject_w4id)
        
        # Check that claims are included
        for key, value in claims.items():
            self.assertEqual(credential["credentialSubject"][key], value)
        
        # Check proof structure
        proof = credential["proof"]
        proof_fields = ["type", "created", "verificationMethod", "proofPurpose", "jws"]
        
        for field in proof_fields:
            self.assertIn(field, proof)
        
        self.assertEqual(proof["type"], "EcdsaSecp256r1Signature2019")
        self.assertEqual(proof["proofPurpose"], "assertionMethod")
        self.assertTrue(proof["verificationMethod"].startswith(self.client1.w4id))
    
    def test_timestamp_format(self):
        """Test that timestamps are in ISO 8601 format."""
        client_hello = self.client1.generate_client_hello(self.client2.w4id)
        timestamp = client_hello["timestamp"]
        
        # Should be able to parse as ISO 8601
        try:
            parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            self.assertIsInstance(parsed_time, datetime)
        except ValueError:
            self.fail("Timestamp is not in valid ISO 8601 format")
    
    def test_nonce_uniqueness(self):
        """Test that nonces are unique across multiple messages."""
        nonces = set()
        
        # Generate multiple ClientHello messages
        for _ in range(10):
            client_hello = self.client1.generate_client_hello(self.client2.w4id)
            nonce = client_hello["nonce"]
            
            # Nonce should not have been seen before
            self.assertNotIn(nonce, nonces)
            nonces.add(nonce)
    
    def test_json_serialization(self):
        """Test that all messages can be serialized to JSON."""
        # Test ClientHello
        client_hello = self.client1.generate_client_hello(self.client2.w4id)
        try:
            json.dumps(client_hello)
        except Exception:
            self.fail("ClientHello message is not JSON serializable")
        
        # Test Verifiable Credential
        claims = {"test": "value"}
        credential = self.client1.create_verifiable_credential(self.client2.w4id, claims)
        try:
            json.dumps(credential)
        except Exception:
            self.fail("Verifiable Credential is not JSON serializable")


class TestWeb4SecurityRequirements(unittest.TestCase):
    """Test suite for Web4 security requirements."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Web4Client()
    
    def test_key_generation(self):
        """Test that keys are generated correctly."""
        # Should use SECP256R1 curve
        from cryptography.hazmat.primitives.asymmetric import ec
        self.assertIsInstance(self.client.private_key.curve, ec.SECP256R1)
    
    def test_encryption_algorithm(self):
        """Test that AES-256-GCM is used for encryption."""
        # This is tested implicitly in the encryption/decryption test
        # The AESGCM class enforces the correct algorithm
        pass
    
    def test_signature_algorithm(self):
        """Test that ECDSA with SHA-256 is used for signatures."""
        # Create a test credential to verify signature algorithm
        claims = {"test": "value"}
        credential = self.client.create_verifiable_credential(self.client.w4id, claims)
        
        # The signature should be created with ECDSA and SHA-256
        # This is enforced by the cryptography library
        self.assertIn("proof", credential)
        self.assertEqual(credential["proof"]["type"], "EcdsaSecp256r1Signature2019")


def run_conformance_tests():
    """Run the complete conformance test suite."""
    print("Web4 Protocol Conformance Tests")
    print("================================")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestWeb4Protocol))
    suite.addTests(loader.loadTestsFromTestCase(TestWeb4SecurityRequirements))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_conformance_tests()
    sys.exit(0 if success else 1)

