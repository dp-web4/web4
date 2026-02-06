"""
Federation Client - Client for SAGE Consciousness Task Delegation

Enables platforms to delegate consciousness tasks to remote federation servers.
Handles task creation, signing, sending, and proof verification.

Author: Legion Autonomous Session #54
Date: 2025-12-03
References: MULTI_MACHINE_SAGE_FEDERATION_DESIGN.md
"""

from typing import Dict, List, Optional, Tuple
import time
import json
import base64

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available. Install with: pip install requests")

from game.server.federation_api import FederationTask, ExecutionProof
from game.engine.sage_lct_integration import SAGELCTManager
from game.engine.lct_permissions import check_permission, get_atp_budget


class PlatformRegistration:
    """Remote platform registration"""

    def __init__(
        self,
        name: str,
        endpoint: str,
        capabilities: List[str]
    ):
        self.name = name
        self.endpoint = endpoint
        self.capabilities = capabilities
        self.is_available = True
        self.last_check = 0.0


class FederationClient:
    """
    Client for delegating consciousness tasks to remote platforms

    Enables cross-platform SAGE consciousness delegation with ATP tracking,
    permission enforcement, and quality-based settlement.
    """

    def __init__(
        self,
        platform_name: str,
        lineage: str = "dp"
    ):
        """
        Initialize Federation Client

        Parameters:
        -----------
        platform_name : str
            Local platform name (e.g., "Thor", "Sprout")
        lineage : str
            Lineage for LCT identity creation (default: "dp")
        """
        if not REQUESTS_AVAILABLE:
            print("Warning: Federation client requires 'requests' library")
            print("Install with: pip install requests")

        self.platform_name = platform_name
        self.lineage = lineage
        self.manager = SAGELCTManager(platform_name)
        self.platforms: Dict[str, PlatformRegistration] = {}
        self.pending_tasks: Dict[str, FederationTask] = {}
        self.completed_tasks: Dict[str, ExecutionProof] = {}

    def register_platform(
        self,
        name: str,
        endpoint: str,
        capabilities: List[str]
    ):
        """
        Register remote platform for delegation

        Parameters:
        -----------
        name : str
            Platform name (e.g., "Legion")
        endpoint : str
            HTTP endpoint (e.g., "http://legion.local:8080")
        capabilities : List[str]
            Task types supported (e.g., ["consciousness", "consciousness.sage"])
        """
        self.platforms[name] = PlatformRegistration(
            name=name,
            endpoint=endpoint,
            capabilities=capabilities
        )

        print(f"Registered platform: {name} at {endpoint}")
        print(f"  Capabilities: {', '.join(capabilities)}")

    def find_capable_platform(
        self,
        task_type: str,
        atp_required: float
    ) -> Optional[str]:
        """
        Find platform capable of handling task

        Parameters:
        -----------
        task_type : str
            Required task type (e.g., "consciousness.sage")
        atp_required : float
            ATP budget required

        Returns:
        --------
        Optional[str]
            Platform name or None if no capable platform found
        """
        for name, platform in self.platforms.items():
            # Check if platform is available
            if not platform.is_available:
                continue

            # Check if platform supports task type
            if task_type not in platform.capabilities:
                continue

            # Platform is capable
            return name

        return None

    def should_delegate(
        self,
        task_type: str,
        operation: str,
        atp_cost: float,
        local_lct: str
    ) -> Tuple[bool, str]:
        """
        Determine if task should be delegated

        Parameters:
        -----------
        task_type : str
            Task type (e.g., "consciousness")
        operation : str
            Operation (e.g., "execution")
        atp_cost : float
            Estimated ATP cost
        local_lct : str
            Local LCT identity

        Returns:
        --------
        Tuple[bool, str]
            (should_delegate, reason) tuple
        """
        # Check if we have delegation permission
        can_delegate = check_permission(task_type, "federation:delegate")
        if not can_delegate:
            return (False, f"Task {task_type} cannot delegate")

        # Get local ATP budget
        if local_lct not in self.manager.sage_instances:
            return (False, "Unknown local LCT identity")

        state = self.manager.sage_instances[local_lct]

        # Check if we have sufficient local ATP
        if state.atp_spent + atp_cost <= state.atp_budget:
            # We can handle locally
            return (False, "Sufficient local ATP budget")

        # We need to delegate
        return (True, "Local ATP budget insufficient")

    def delegate_task(
        self,
        source_lct: str,
        task_type: str,
        operation: str,
        atp_budget: float,
        parameters: Optional[Dict] = None,
        timeout_seconds: int = 60,
        target_platform: Optional[str] = None
    ) -> Tuple[Optional[ExecutionProof], str]:
        """
        Delegate consciousness task to remote platform

        Parameters:
        -----------
        source_lct : str
            Source LCT identity (local)
        task_type : str
            Task type (e.g., "consciousness.sage")
        operation : str
            Operation (e.g., "execution")
        atp_budget : float
            ATP budget for task
        parameters : Optional[Dict]
            Task parameters
        timeout_seconds : int
            Task timeout (default: 60)
        target_platform : Optional[str]
            Target platform name (auto-selected if None)

        Returns:
        --------
        Tuple[Optional[ExecutionProof], str]
            (proof, error_message) tuple
        """
        if parameters is None:
            parameters = {}

        # Find capable platform if not specified
        if target_platform is None:
            target_platform = self.find_capable_platform(task_type, atp_budget)
            if target_platform is None:
                return (None, f"No capable platform found for {task_type}")

        # Check if platform is registered
        if target_platform not in self.platforms:
            return (None, f"Platform {target_platform} not registered")

        platform = self.platforms[target_platform]

        # Construct target LCT
        # Parse source LCT to get lineage
        from game.engine.lct_identity import parse_lct_id
        lct_components = parse_lct_id(source_lct)
        if lct_components is None:
            return (None, f"Invalid source LCT: {source_lct}")

        lineage, context, source_task = lct_components

        # Target LCT: same lineage, target platform context, specified task type
        target_lct = f"lct:web4:agent:{lineage}@{platform.name}#{task_type}"

        # Create federation task
        task_id = f"{self.platform_name}_{int(time.time()* 1000)}_{operation}"
        task = FederationTask(
            task_id=task_id,
            source_lct=source_lct,
            target_lct=target_lct,
            task_type=task_type,
            operation=operation,
            atp_budget=atp_budget,
            timeout_seconds=timeout_seconds,
            parameters=parameters,
            created_at=time.time()
        )

        # Sign task (placeholder for Ed25519)
        signature = self._sign_task(task)

        # Send task to platform
        proof, error = self._send_task(platform, task, signature)

        if proof:
            # Track completed task
            self.completed_tasks[task_id] = proof
            return (proof, "")
        else:
            return (None, error)

    def _sign_task(
        self,
        task: FederationTask
    ) -> bytes:
        """
        Sign federation task with Ed25519

        In production, this would:
        1. Load platform Ed25519 keypair
        2. Sign task.to_signable_dict()
        3. Return signature bytes

        For now, we return placeholder.
        """
        # Placeholder signature
        import hashlib
        task_str = json.dumps(task.to_signable_dict(), sort_keys=True)
        signature = hashlib.sha256(task_str.encode()).digest()
        return signature

    def _send_task(
        self,
        platform: PlatformRegistration,
        task: FederationTask,
        signature: bytes
    ) -> Tuple[Optional[ExecutionProof], str]:
        """
        Send task to remote platform via HTTP

        Parameters:
        -----------
        platform : PlatformRegistration
            Target platform
        task : FederationTask
            Task to send
        signature : bytes
            Task signature

        Returns:
        --------
        Tuple[Optional[ExecutionProof], str]
            (proof, error_message) tuple
        """
        if not REQUESTS_AVAILABLE:
            return (None, "requests library not available")

        # Prepare request
        url = f"{platform.endpoint}/api/v1/consciousness/delegate"
        payload = {
            "task": task.to_dict(),
            "signature": base64.b64encode(signature).decode('utf-8')
        }

        try:
            # Send POST request
            response = requests.post(
                url,
                json=payload,
                timeout=task.timeout_seconds + 5  # Add buffer
            )

            # Parse response
            result = response.json()

            if result.get('success'):
                proof_data = result.get('proof')
                if proof_data:
                    proof = ExecutionProof.from_dict(proof_data)
                    return (proof, "")
                else:
                    return (None, "No proof in response")
            else:
                error = result.get('error', 'Unknown error')
                return (None, error)

        except requests.exceptions.Timeout:
            platform.is_available = False
            return (None, f"Request to {platform.name} timed out")

        except requests.exceptions.ConnectionError:
            platform.is_available = False
            return (None, f"Could not connect to {platform.name}")

        except Exception as e:
            return (None, f"Error sending task: {str(e)}")

    def get_task_status(
        self,
        task_id: str
    ) -> Optional[ExecutionProof]:
        """
        Get status of completed task

        Parameters:
        -----------
        task_id : str
            Task ID

        Returns:
        --------
        Optional[ExecutionProof]
            Proof if task completed, None otherwise
        """
        return self.completed_tasks.get(task_id)

    def get_platform_status(
        self,
        platform_name: str,
        lct_id: str
    ) -> Optional[Dict]:
        """
        Get consciousness status on remote platform

        Parameters:
        -----------
        platform_name : str
            Platform name
        lct_id : str
            LCT identity to check

        Returns:
        --------
        Optional[Dict]
            Status dictionary or None
        """
        if platform_name not in self.platforms:
            return None

        platform = self.platforms[platform_name]

        if not REQUESTS_AVAILABLE:
            return None

        try:
            # URL-encode LCT ID
            from urllib.parse import quote
            lct_encoded = quote(lct_id, safe='')

            url = f"{platform.endpoint}/api/v1/consciousness/status/{lct_encoded}"

            response = requests.get(url, timeout=5)
            result = response.json()

            if result.get('success'):
                return result.get('status')
            else:
                return None

        except Exception as e:
            print(f"Error getting status: {e}")
            return None
