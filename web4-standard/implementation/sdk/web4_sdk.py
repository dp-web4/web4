"""
Web4 Client SDK
===============

Research prototype Python SDK for integrating with Web4 infrastructure.

This SDK provides high-level abstractions for:
- Identity management (LCT)
- Authorization requests
- Resource allocation
- Reputation tracking
- Knowledge graph queries

Usage Example:
-------------
```python
from web4_sdk import Web4Client, Action

# Initialize client
client = Web4Client(
    identity_url="http://identity.web4.local:8001",
    auth_url="http://auth.web4.local:8003",
    lct_id="lct:web4:ai:society:001",
    private_key=agent_secret
)

# Request authorization for an action
result = await client.authorize(
    action=Action.COMPUTE,
    resource="model:training",
    atp_cost=500,
    context={"delegation_id": "deleg:001"}
)

if result.decision == "granted":
    # Execute action
    ...
    # Report outcome
    await client.report_outcome(
        action=Action.COMPUTE,
        outcome="success",
        quality_score=0.85
    )
```

Author: Web4 Infrastructure Team
License: MIT
"""

import asyncio
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

try:
    import aiohttp
except ImportError:
    aiohttp = None
    import warnings
    warnings.warn("aiohttp not installed. Async methods will not work. Install with: pip install aiohttp")

try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.encoding import HexEncoder
except ImportError:
    SigningKey = None
    VerifyKey = None
    import warnings
    warnings.warn("PyNaCl not installed. Cryptographic signing will not work. Install with: pip install pynacl")


# =============================================================================
# Enums and Data Classes
# =============================================================================

class Action(Enum):
    """Standard Web4 actions"""
    READ = "read"
    WRITE = "write"
    COMPUTE = "compute"
    QUERY = "query"
    DELEGATE = "delegate"
    ALLOCATE = "allocate"


class OutcomeType(Enum):
    """Outcome quality levels"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    EXCEPTIONAL_QUALITY = "exceptional_quality"
    POOR_QUALITY = "poor_quality"


class ResourceType(Enum):
    """Resource types for allocation"""
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"


@dataclass
class AuthorizationResult:
    """Result of an authorization request"""
    decision: str  # "granted" or "denied"
    atp_remaining: Optional[int] = None
    reason: Optional[str] = None
    law_version: Optional[str] = None
    law_hash: Optional[str] = None
    ledger_ref: Optional[str] = None
    resource_allocation: Optional[Dict[str, float]] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ReputationScore:
    """Reputation scores for an entity"""
    entity_id: str
    role: str
    t3_score: float  # Trustworthiness
    v3_score: float  # Value creation
    action_count: int
    last_updated: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ResourceAllocation:
    """Resource allocation details"""
    allocation_id: str
    resource_type: str
    amount_allocated: float
    atp_cost: int
    entity_id: str
    timestamp: str
    duration_seconds: Optional[int] = None
    actual_usage: Optional[float] = None


@dataclass
class LCTInfo:
    """LCT identity information"""
    lct_id: str
    entity_type: str
    entity_identifier: str
    society: str
    public_key: str
    birth_certificate_hash: str
    witnesses: List[str]
    created_at: str
    status: str = "active"


# =============================================================================
# Exceptions
# =============================================================================

class Web4Error(Exception):
    """Base exception for Web4 SDK errors"""
    pass


class AuthorizationDenied(Web4Error):
    """Authorization request was denied"""
    pass


class InsufficientATP(Web4Error):
    """Insufficient ATP budget for requested action"""
    pass


class InvalidSignature(Web4Error):
    """Cryptographic signature verification failed"""
    pass


class ServiceUnavailable(Web4Error):
    """Web4 service is unavailable"""
    pass


# =============================================================================
# Web4 Client SDK
# =============================================================================

class Web4Client:
    """
    Main Web4 SDK client for interacting with Web4 infrastructure.

    This client handles:
    - Authentication and signing
    - Authorization requests
    - Reputation tracking
    - Resource allocation
    - Knowledge graph queries

    All network operations are async for performance.
    """

    def __init__(
        self,
        identity_url: str,
        auth_url: str,
        lct_id: str,
        private_key: Optional[bytes] = None,
        reputation_url: Optional[str] = None,
        resources_url: Optional[str] = None,
        knowledge_url: Optional[str] = None,
        governance_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Web4 client.

        Args:
            identity_url: URL of identity service (e.g., http://identity:8001)
            auth_url: URL of authorization service (e.g., http://auth:8003)
            lct_id: LCT identifier for this entity
            private_key: Ed25519 private key bytes (32 bytes) for signing
            reputation_url: Optional URL of reputation service
            resources_url: Optional URL of resource service
            knowledge_url: Optional URL of knowledge service
            governance_url: Optional URL of governance service
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        if not aiohttp:
            raise ImportError("aiohttp is required. Install with: pip install aiohttp")

        if not SigningKey:
            raise ImportError("PyNaCl is required. Install with: pip install pynacl")

        self.identity_url = identity_url.rstrip('/')
        self.auth_url = auth_url.rstrip('/')
        self.lct_id = lct_id
        self.timeout = timeout
        self.max_retries = max_retries

        # Optional service URLs
        self.reputation_url = reputation_url.rstrip('/') if reputation_url else None
        self.resources_url = resources_url.rstrip('/') if resources_url else None
        self.knowledge_url = knowledge_url.rstrip('/') if knowledge_url else None
        self.governance_url = governance_url.rstrip('/') if governance_url else None

        # Cryptographic signing key
        if private_key:
            if len(private_key) != 32:
                raise ValueError("Private key must be exactly 32 bytes")
            self.signing_key = SigningKey(private_key)
        else:
            self.signing_key = None

        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._nonce_counter = int(time.time() * 1000)

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Create HTTP session"""
        if not self._session:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

    async def disconnect(self):
        """Close HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None

    def _get_nonce(self) -> int:
        """Generate monotonically increasing nonce"""
        self._nonce_counter += 1
        return self._nonce_counter

    def _sign_request(self, method: str, path: str, body: Optional[Dict] = None) -> tuple[str, int]:
        """
        Sign a request with Ed25519 signature.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Optional request body

        Returns:
            Tuple of (signature_hex, nonce)
        """
        if not self.signing_key:
            raise ValueError("No private key configured for signing")

        nonce = self._get_nonce()

        # Create signature payload
        payload = f"{method}|{path}|{nonce}"
        if body:
            body_json = json.dumps(body, sort_keys=True)
            payload += f"|{body_json}"

        # Sign with Ed25519
        signature = self.signing_key.sign(payload.encode('utf-8'))
        signature_hex = signature.signature.hex()

        return signature_hex, nonce

    async def _request(
        self,
        method: str,
        url: str,
        body: Optional[Dict] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request to Web4 service.

        Args:
            method: HTTP method
            url: Full URL
            body: Optional request body
            require_auth: Whether to include authentication headers

        Returns:
            Response JSON

        Raises:
            ServiceUnavailable: If service is unavailable
            Web4Error: On other errors
        """
        if not self._session:
            await self.connect()

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Web4-SDK/1.0"
        }

        # Add authentication if required
        if require_auth and self.signing_key:
            path = url.split('/', 3)[-1] if '://' in url else url
            signature, nonce = self._sign_request(method, path, body)
            headers["Authorization"] = f"Bearer {self.lct_id}"
            headers["X-Signature"] = signature
            headers["X-Nonce"] = str(nonce)

        # Make request with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with self._session.request(
                    method,
                    url,
                    json=body if body else None,
                    headers=headers
                ) as response:
                    # Parse response
                    try:
                        data = await response.json()
                    except Exception:
                        data = {"error": await response.text()}

                    # Check for errors
                    if response.status >= 500:
                        last_error = ServiceUnavailable(
                            f"Service unavailable: {response.status} - {data.get('error', 'Unknown error')}"
                        )
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue

                    if response.status >= 400:
                        error_msg = data.get('error', f"HTTP {response.status}")
                        raise Web4Error(f"Request failed: {error_msg}")

                    return data

            except aiohttp.ClientError as e:
                last_error = ServiceUnavailable(f"Network error: {str(e)}")
                await asyncio.sleep(2 ** attempt)

        # All retries failed
        raise last_error if last_error else ServiceUnavailable("Request failed after retries")

    # =========================================================================
    # Identity Service Methods
    # =========================================================================

    async def get_lct_info(self, lct_id: Optional[str] = None) -> LCTInfo:
        """
        Retrieve LCT information from identity service.

        Args:
            lct_id: LCT ID to query (defaults to self)

        Returns:
            LCT information
        """
        target_lct = lct_id or self.lct_id
        url = f"{self.identity_url}/v1/lct/{target_lct}"

        response = await self._request("GET", url, require_auth=False)

        if not response.get('success'):
            raise Web4Error(f"Failed to retrieve LCT: {response.get('error')}")

        data = response['data']
        return LCTInfo(
            lct_id=data['lct_id'],
            entity_type=data['entity_type'],
            entity_identifier=data['entity_identifier'],
            society=data['society'],
            public_key=data['public_key'],
            birth_certificate_hash=data['birth_certificate']['certificate_hash'],
            witnesses=data['birth_certificate']['witnesses'],
            created_at=data['created_at'],
            status=data.get('status', 'active')
        )

    async def verify_lct_signature(
        self,
        lct_id: str,
        message: bytes,
        signature: bytes
    ) -> bool:
        """
        Verify signature from another LCT.

        Args:
            lct_id: LCT ID of signer
            message: Original message
            signature: Signature bytes

        Returns:
            True if signature is valid
        """
        url = f"{self.identity_url}/v1/lct/{lct_id}/verify"

        response = await self._request(
            "POST",
            url,
            body={
                "message": message.hex(),
                "signature": signature.hex()
            },
            require_auth=False
        )

        return response.get('success', False) and response.get('data', {}).get('valid', False)

    # =========================================================================
    # Authorization Service Methods
    # =========================================================================

    async def authorize(
        self,
        action: Action,
        resource: str,
        atp_cost: int,
        context: Optional[Dict[str, Any]] = None
    ) -> AuthorizationResult:
        """
        Request authorization for an action.

        Args:
            action: Action type
            resource: Resource identifier
            atp_cost: ATP cost for this action
            context: Optional context (delegation_id, witnesses, etc.)

        Returns:
            Authorization result

        Raises:
            AuthorizationDenied: If authorization is denied
            InsufficientATP: If ATP budget is insufficient
        """
        url = f"{self.auth_url}/v1/auth/authorize"

        body = {
            "action": action.value,
            "resource": resource,
            "atp_cost": atp_cost,
            "context": context or {}
        }

        response = await self._request("POST", url, body=body)

        if not response.get('success'):
            error = response.get('error', 'Unknown error')
            if 'insufficient' in error.lower():
                raise InsufficientATP(error)
            raise AuthorizationDenied(error)

        data = response['data']
        metadata = response.get('metadata', {})

        result = AuthorizationResult(
            decision=data['decision'],
            atp_remaining=data.get('atp_remaining'),
            reason=data.get('reason'),
            law_version=metadata.get('law_version'),
            law_hash=metadata.get('law_hash'),
            ledger_ref=metadata.get('ledger_ref'),
            resource_allocation=data.get('resource_allocation'),
            timestamp=metadata.get('timestamp'),
            metadata=metadata
        )

        if result.decision != "granted":
            raise AuthorizationDenied(f"Authorization denied: {result.reason}")

        return result

    async def check_delegation(
        self,
        delegation_id: str
    ) -> Dict[str, Any]:
        """
        Check delegation status and details.

        Args:
            delegation_id: Delegation identifier

        Returns:
            Delegation details
        """
        url = f"{self.auth_url}/v1/delegation/{delegation_id}"

        response = await self._request("GET", url)

        if not response.get('success'):
            raise Web4Error(f"Failed to retrieve delegation: {response.get('error')}")

        return response['data']

    # =========================================================================
    # Reputation Service Methods
    # =========================================================================

    async def get_reputation(
        self,
        entity_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> ReputationScore:
        """
        Get reputation scores for an entity.

        Args:
            entity_id: Entity to query (defaults to self)
            role: Optional role filter

        Returns:
            Reputation scores
        """
        if not self.reputation_url:
            raise Web4Error("Reputation service URL not configured")

        target_entity = entity_id or self.lct_id
        url = f"{self.reputation_url}/v1/reputation/{target_entity}"

        if role:
            url += f"?role={role}"

        response = await self._request("GET", url)

        if not response.get('success'):
            raise Web4Error(f"Failed to retrieve reputation: {response.get('error')}")

        data = response['data']
        return ReputationScore(
            entity_id=data['entity_id'],
            role=data['role'],
            t3_score=data['t3_score'],
            v3_score=data['v3_score'],
            action_count=data['action_count'],
            last_updated=data['last_updated'],
            metadata=data.get('metadata')
        )

    async def report_outcome(
        self,
        action: Action,
        outcome: OutcomeType,
        quality_score: Optional[float] = None,
        witnesses: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReputationScore:
        """
        Report action outcome to update reputation.

        Args:
            action: Action performed
            outcome: Outcome type
            quality_score: Optional quality score (0.0-1.0)
            witnesses: Optional witness LCT IDs
            context: Optional context

        Returns:
            Updated reputation scores
        """
        if not self.reputation_url:
            raise Web4Error("Reputation service URL not configured")

        url = f"{self.reputation_url}/v1/reputation/record"

        body = {
            "entity": self.lct_id,
            "action": action.value,
            "outcome": outcome.value,
            "quality_score": quality_score,
            "witnesses": witnesses or [],
            "context": context or {}
        }

        response = await self._request("POST", url, body=body)

        if not response.get('success'):
            raise Web4Error(f"Failed to record outcome: {response.get('error')}")

        data = response['data']
        return ReputationScore(
            entity_id=data['entity_id'],
            role=data['role'],
            t3_score=data['t3_score'],
            v3_score=data['v3_score'],
            action_count=data['action_count'],
            last_updated=data['last_updated'],
            metadata=data.get('metadata')
        )

    # =========================================================================
    # Resource Service Methods
    # =========================================================================

    async def allocate_resources(
        self,
        resource_type: ResourceType,
        amount: float,
        duration_seconds: Optional[int] = None
    ) -> ResourceAllocation:
        """
        Allocate resources using ATP.

        Args:
            resource_type: Type of resource
            amount: Amount to allocate
            duration_seconds: Optional duration

        Returns:
            Resource allocation details
        """
        if not self.resources_url:
            raise Web4Error("Resource service URL not configured")

        url = f"{self.resources_url}/v1/resources/allocate"

        body = {
            "entity_id": self.lct_id,
            "resource_type": resource_type.value,
            "amount": amount,
            "duration_seconds": duration_seconds
        }

        response = await self._request("POST", url, body=body)

        if not response.get('success'):
            raise Web4Error(f"Failed to allocate resources: {response.get('error')}")

        data = response['data']
        return ResourceAllocation(
            allocation_id=data['allocation_id'],
            resource_type=data['resource_type'],
            amount_allocated=data['amount_allocated'],
            atp_cost=data['atp_cost'],
            entity_id=data['entity_id'],
            timestamp=data['timestamp'],
            duration_seconds=data.get('duration_seconds'),
            actual_usage=data.get('actual_usage')
        )

    async def report_resource_usage(
        self,
        allocation_id: str,
        actual_usage: float
    ) -> Dict[str, Any]:
        """
        Report actual resource usage.

        Args:
            allocation_id: Allocation ID
            actual_usage: Actual usage amount

        Returns:
            Usage report response
        """
        if not self.resources_url:
            raise Web4Error("Resource service URL not configured")

        url = f"{self.resources_url}/v1/resources/usage"

        body = {
            "allocation_id": allocation_id,
            "actual_usage": actual_usage
        }

        response = await self._request("POST", url, body=body)

        if not response.get('success'):
            raise Web4Error(f"Failed to report usage: {response.get('error')}")

        return response['data']

    # =========================================================================
    # Knowledge Service Methods
    # =========================================================================

    async def query_knowledge_graph(
        self,
        sparql_query: str
    ) -> List[Dict[str, Any]]:
        """
        Execute SPARQL query on knowledge graph.

        Args:
            sparql_query: SPARQL query string

        Returns:
            Query results
        """
        if not self.knowledge_url:
            raise Web4Error("Knowledge service URL not configured")

        url = f"{self.knowledge_url}/v1/graph/query"

        body = {"query": sparql_query}

        response = await self._request("POST", url, body=body)

        if not response.get('success'):
            raise Web4Error(f"Query failed: {response.get('error')}")

        return response['data']['results']

    async def get_trust_propagation(
        self,
        start_entity: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Get trust propagation from entity.

        Args:
            start_entity: Starting entity LCT
            max_depth: Maximum graph depth

        Returns:
            Trust propagation results
        """
        if not self.knowledge_url:
            raise Web4Error("Knowledge service URL not configured")

        url = f"{self.knowledge_url}/v1/graph/trust/{start_entity}"

        response = await self._request(
            "GET",
            f"{url}?max_depth={max_depth}"
        )

        if not response.get('success'):
            raise Web4Error(f"Trust query failed: {response.get('error')}")

        return response['data']

    # =========================================================================
    # Governance Service Methods
    # =========================================================================

    async def get_law_version(self) -> Dict[str, Any]:
        """
        Get current law dataset version.

        Returns:
            Law version info
        """
        if not self.governance_url:
            raise Web4Error("Governance service URL not configured")

        url = f"{self.governance_url}/v1/law/version"

        response = await self._request("GET", url, require_auth=False)

        if not response.get('success'):
            raise Web4Error(f"Failed to get law version: {response.get('error')}")

        return response['data']

    async def check_action_legal(
        self,
        action: Action,
        entity_type: str,
        role: str
    ) -> bool:
        """
        Check if action is legal for entity/role.

        Args:
            action: Action to check
            entity_type: Entity type
            role: Role

        Returns:
            True if legal
        """
        if not self.governance_url:
            raise Web4Error("Governance service URL not configured")

        url = f"{self.governance_url}/v1/law/check"

        body = {
            "action": action.value,
            "entity_type": entity_type,
            "role": role
        }

        response = await self._request("POST", url, body=body, require_auth=False)

        if not response.get('success'):
            raise Web4Error(f"Law check failed: {response.get('error')}")

        return response['data'].get('legal', False)


# =============================================================================
# High-Level Workflow Helpers
# =============================================================================

class Web4Workflow:
    """
    High-level workflow helpers for common Web4 operations.

    These methods combine multiple SDK calls into common workflows.
    """

    def __init__(self, client: Web4Client):
        """
        Initialize workflow helper.

        Args:
            client: Web4Client instance
        """
        self.client = client

    async def execute_action_with_reporting(
        self,
        action: Action,
        resource: str,
        atp_cost: int,
        executor_fn,
        context: Optional[Dict] = None
    ) -> tuple[Any, ReputationScore]:
        """
        Complete workflow: authorize -> execute -> report outcome.

        Args:
            action: Action type
            resource: Resource identifier
            atp_cost: ATP cost
            executor_fn: Async function to execute (receives auth_result)
            context: Optional context

        Returns:
            Tuple of (executor_result, updated_reputation)
        """
        # Step 1: Request authorization
        auth_result = await self.client.authorize(
            action=action,
            resource=resource,
            atp_cost=atp_cost,
            context=context
        )

        # Step 2: Execute action
        try:
            result = await executor_fn(auth_result)
            outcome = OutcomeType.SUCCESS
            quality_score = 0.75
        except Exception as e:
            result = None
            outcome = OutcomeType.FAILURE
            quality_score = 0.0

        # Step 3: Report outcome
        reputation = await self.client.report_outcome(
            action=action,
            outcome=outcome,
            quality_score=quality_score,
            context={"auth_result": str(auth_result)}
        )

        return result, reputation

    async def delegate_with_budget(
        self,
        target_lct: str,
        role: str,
        permissions: List[str],
        atp_budget: int,
        duration_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create delegation with ATP budget.

        Args:
            target_lct: Target entity LCT
            role: Role to delegate
            permissions: List of permissions
            atp_budget: ATP budget
            duration_seconds: Optional duration

        Returns:
            Delegation details
        """
        # This would call a delegation endpoint
        # For now, this is a placeholder showing the workflow
        raise NotImplementedError("Delegation workflow not yet implemented in services")

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all configured services.

        Returns:
            Dict mapping service name to health status
        """
        health = {}

        # Check identity service
        try:
            await self.client.get_lct_info()
            health['identity'] = True
        except Exception:
            health['identity'] = False

        # Check authorization service
        try:
            await self.client._request(
                "GET",
                f"{self.client.auth_url}/health",
                require_auth=False
            )
            health['authorization'] = True
        except Exception:
            health['authorization'] = False

        # Check optional services
        if self.client.reputation_url:
            try:
                await self.client._request(
                    "GET",
                    f"{self.client.reputation_url}/health",
                    require_auth=False
                )
                health['reputation'] = True
            except Exception:
                health['reputation'] = False

        if self.client.resources_url:
            try:
                await self.client._request(
                    "GET",
                    f"{self.client.resources_url}/health",
                    require_auth=False
                )
                health['resources'] = True
            except Exception:
                health['resources'] = False

        if self.client.knowledge_url:
            try:
                await self.client._request(
                    "GET",
                    f"{self.client.knowledge_url}/health",
                    require_auth=False
                )
                health['knowledge'] = True
            except Exception:
                health['knowledge'] = False

        if self.client.governance_url:
            try:
                await self.client._request(
                    "GET",
                    f"{self.client.governance_url}/health",
                    require_auth=False
                )
                health['governance'] = True
            except Exception:
                health['governance'] = False

        return health


# =============================================================================
# Convenience Functions
# =============================================================================

def create_client_from_env() -> Web4Client:
    """
    Create Web4Client from environment variables.

    Expected environment variables:
    - WEB4_IDENTITY_URL
    - WEB4_AUTH_URL
    - WEB4_LCT_ID
    - WEB4_PRIVATE_KEY (hex encoded)
    - WEB4_REPUTATION_URL (optional)
    - WEB4_RESOURCES_URL (optional)
    - WEB4_KNOWLEDGE_URL (optional)
    - WEB4_GOVERNANCE_URL (optional)

    Returns:
        Configured Web4Client
    """
    import os

    required_vars = ['WEB4_IDENTITY_URL', 'WEB4_AUTH_URL', 'WEB4_LCT_ID']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    private_key_hex = os.getenv('WEB4_PRIVATE_KEY')
    private_key = bytes.fromhex(private_key_hex) if private_key_hex else None

    return Web4Client(
        identity_url=os.getenv('WEB4_IDENTITY_URL'),
        auth_url=os.getenv('WEB4_AUTH_URL'),
        lct_id=os.getenv('WEB4_LCT_ID'),
        private_key=private_key,
        reputation_url=os.getenv('WEB4_REPUTATION_URL'),
        resources_url=os.getenv('WEB4_RESOURCES_URL'),
        knowledge_url=os.getenv('WEB4_KNOWLEDGE_URL'),
        governance_url=os.getenv('WEB4_GOVERNANCE_URL')
    )


__all__ = [
    'Web4Client',
    'Web4Workflow',
    'Action',
    'OutcomeType',
    'ResourceType',
    'AuthorizationResult',
    'ReputationScore',
    'ResourceAllocation',
    'LCTInfo',
    'Web4Error',
    'AuthorizationDenied',
    'InsufficientATP',
    'InvalidSignature',
    'ServiceUnavailable',
    'create_client_from_env'
]
