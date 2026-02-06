"""
Federation API - HTTP Endpoints for SAGE Consciousness Delegation

Provides REST API for cross-platform SAGE consciousness task delegation.
Implements LUPS v1.0 permission enforcement and ATP tracking.

Author: Legion Autonomous Session #54
Date: 2025-12-03
References: MULTI_MACHINE_SAGE_FEDERATION_DESIGN.md
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple
import time
import json

from game.engine.sage_lct_integration import SAGELCTManager
from game.engine.lct_permissions import check_permission
from game.engine.lct_identity import parse_lct_id


@dataclass
class FederationTask:
    """Consciousness task for cross-platform delegation"""
    task_id: str
    source_lct: str          # lct:web4:agent:dp@Legion#consciousness
    target_lct: str          # lct:web4:agent:dp@Thor#consciousness.sage
    task_type: str           # "consciousness" or "consciousness.sage"
    operation: str           # "perception", "planning", "execution"
    atp_budget: float        # ATP allocated for task
    timeout_seconds: int     # Task timeout
    parameters: Dict         # Task-specific params
    created_at: float

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_signable_dict(self) -> Dict:
        """Get dictionary for signature (canonical order)"""
        return {
            "task_id": self.task_id,
            "source_lct": self.source_lct,
            "target_lct": self.target_lct,
            "task_type": self.task_type,
            "operation": self.operation,
            "atp_budget": self.atp_budget,
            "timeout_seconds": self.timeout_seconds,
            "parameters": json.dumps(self.parameters, sort_keys=True),
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'FederationTask':
        """Create from dictionary"""
        # Handle parameters as JSON string if needed
        params = data.get('parameters', {})
        if isinstance(params, str):
            params = json.loads(params)

        return cls(
            task_id=data['task_id'],
            source_lct=data['source_lct'],
            target_lct=data['target_lct'],
            task_type=data['task_type'],
            operation=data['operation'],
            atp_budget=data['atp_budget'],
            timeout_seconds=data['timeout_seconds'],
            parameters=params,
            created_at=data['created_at']
        )


@dataclass
class ExecutionProof:
    """Proof of consciousness task execution"""
    task_id: str
    executor_lct: str        # Who executed
    atp_consumed: float      # Actual ATP used
    execution_time: float    # Time in seconds
    quality_score: float     # 0.0-1.0
    result: Dict             # Task results
    created_at: float

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_signable_dict(self) -> Dict:
        """Get dictionary for signature (canonical order)"""
        return {
            "task_id": self.task_id,
            "executor_lct": self.executor_lct,
            "atp_consumed": self.atp_consumed,
            "execution_time": self.execution_time,
            "quality_score": self.quality_score,
            "result": json.dumps(self.result, sort_keys=True),
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ExecutionProof':
        """Create from dictionary"""
        # Handle result as JSON string if needed
        result = data.get('result', {})
        if isinstance(result, str):
            result = json.loads(result)

        return cls(
            task_id=data['task_id'],
            executor_lct=data['executor_lct'],
            atp_consumed=data['atp_consumed'],
            execution_time=data['execution_time'],
            quality_score=data['quality_score'],
            result=result,
            created_at=data['created_at']
        )


class FederationAPI:
    """
    Federation API for SAGE consciousness delegation

    Provides HTTP endpoints for cross-platform task delegation with
    ATP tracking, permission enforcement, and quality validation.
    """

    def __init__(self, platform_name: str):
        """
        Initialize Federation API

        Parameters:
        -----------
        platform_name : str
            Platform identifier (e.g., "Legion", "Thor", "Sprout")
        """
        self.platform_name = platform_name
        self.manager = SAGELCTManager(platform_name)
        self.active_tasks: Dict[str, FederationTask] = {}
        self.completed_tasks: Dict[str, ExecutionProof] = {}

    def validate_task(
        self,
        task: FederationTask
    ) -> Tuple[bool, str]:
        """
        Validate federation task

        Parameters:
        -----------
        task : FederationTask
            Task to validate

        Returns:
        --------
        Tuple[bool, str]
            (valid, reason) tuple
        """
        # Validate task type
        if task.task_type not in ["consciousness", "consciousness.sage"]:
            return (False, f"Invalid task type: {task.task_type}")

        # Validate operation
        valid_operations = ["perception", "planning", "execution", "delegation"]
        if task.operation not in valid_operations:
            return (False, f"Invalid operation: {task.operation}")

        # Validate ATP budget
        if task.atp_budget <= 0:
            return (False, f"Invalid ATP budget: {task.atp_budget}")

        # Validate timeout
        if task.timeout_seconds <= 0:
            return (False, f"Invalid timeout: {task.timeout_seconds}")

        # Parse target LCT
        lct_components = parse_lct_id(task.target_lct)
        if lct_components is None:
            return (False, f"Invalid target LCT: {task.target_lct}")

        lineage, context, lct_task = lct_components

        # Verify target context matches our platform
        if context != self.platform_name:
            return (
                False,
                f"Target context {context} does not match platform {self.platform_name}"
            )

        # Verify task type matches target LCT task
        if lct_task != task.task_type:
            return (
                False,
                f"Task type {task.task_type} does not match target LCT task {lct_task}"
            )

        # Check if we have permission to execute this operation
        operation_permission_map = {
            "perception": "atp:read",
            "planning": "atp:read",
            "execution": "exec:code",
            "delegation": "federation:delegate"
        }

        required_permission = operation_permission_map.get(task.operation)
        if required_permission:
            can_execute = check_permission(task.task_type, required_permission)
            if not can_execute:
                return (
                    False,
                    f"Task {task.task_type} lacks permission {required_permission}"
                )

        return (True, "")

    def delegate_consciousness_task(
        self,
        task: FederationTask,
        signature: bytes
    ) -> Tuple[Optional[ExecutionProof], str]:
        """
        Handle consciousness task delegation

        Parameters:
        -----------
        task : FederationTask
            Task to execute
        signature : bytes
            Ed25519 signature of task (for verification)

        Returns:
        --------
        Tuple[Optional[ExecutionProof], str]
            (proof, error_message) tuple
        """
        # Validate task
        valid, reason = self.validate_task(task)
        if not valid:
            return (None, reason)

        # Check if task already exists
        if task.task_id in self.active_tasks:
            return (None, f"Task {task.task_id} already active")

        if task.task_id in self.completed_tasks:
            return (None, f"Task {task.task_id} already completed")

        # Create or get SAGE identity for this lineage
        lct_components = parse_lct_id(task.target_lct)
        if lct_components is None:
            return (None, f"Invalid target LCT: {task.target_lct}")

        lineage, context, lct_task = lct_components

        # Create SAGE identity if not exists
        # Check if we already have this identity
        if task.target_lct not in self.manager.sage_instances:
            use_enhanced = (task.task_type == "consciousness.sage")
            identity, state = self.manager.create_sage_identity(
                lineage=lineage,
                use_enhanced_sage=use_enhanced
            )
        else:
            state = self.manager.sage_instances[task.target_lct]

        # Check ATP budget
        if state.atp_spent + task.atp_budget > state.atp_budget:
            return (
                None,
                f"Insufficient ATP budget. "
                f"Required: {task.atp_budget}, "
                f"Available: {state.atp_budget - state.atp_spent}"
            )

        # Mark task as active
        self.active_tasks[task.task_id] = task

        # Execute task (simulated for now)
        start_time = time.time()
        execution_result = self._execute_task(task)
        execution_time = time.time() - start_time

        # Calculate quality score (simulated based on parameters)
        quality_score = self._calculate_quality(task, execution_result)

        # Calculate ATP consumed (based on operation type)
        atp_consumed = self._calculate_atp_consumed(task, execution_time)

        # Record ATP consumption
        success = self.manager.record_consciousness_operation(
            task.target_lct,
            task.operation,
            atp_consumed
        )

        if not success:
            # Failed to record - remove from active tasks
            del self.active_tasks[task.task_id]
            return (None, "Failed to record ATP consumption (budget exceeded)")

        # Create execution proof
        proof = ExecutionProof(
            task_id=task.task_id,
            executor_lct=task.target_lct,
            atp_consumed=atp_consumed,
            execution_time=execution_time,
            quality_score=quality_score,
            result=execution_result,
            created_at=time.time()
        )

        # Move from active to completed
        del self.active_tasks[task.task_id]
        self.completed_tasks[task.task_id] = proof

        return (proof, "")

    def _execute_task(
        self,
        task: FederationTask
    ) -> Dict:
        """
        Execute consciousness task (simulated)

        In production, this would:
        1. Load consciousness state
        2. Execute IRP plugins
        3. Run SNARC selection
        4. Generate outputs
        5. Update state

        For now, we simulate with parameters.
        """
        # Simulated execution based on operation type
        if task.operation == "perception":
            return {
                "observations": task.parameters.get("input", []),
                "salience_scores": [0.5, 0.7, 0.3],
                "selected_observations": ["high salience observation"]
            }

        elif task.operation == "planning":
            return {
                "action_costs": {"option_a": 10.0, "option_b": 15.0},
                "selected_action": "option_a",
                "expected_atp": 10.0
            }

        elif task.operation == "execution":
            return {
                "action_taken": task.parameters.get("action", "default"),
                "success": True,
                "effects": ["state_updated", "output_generated"]
            }

        elif task.operation == "delegation":
            return {
                "delegated_to": task.parameters.get("target", "unknown"),
                "delegation_success": True,
                "atp_locked": task.atp_budget
            }

        else:
            return {"error": "Unknown operation"}

    def _calculate_quality(
        self,
        task: FederationTask,
        result: Dict
    ) -> float:
        """
        Calculate execution quality score

        In production, this would use:
        - Output coherence metrics
        - Correctness validation
        - Resource efficiency
        - Timeliness

        For now, we simulate based on task complexity.
        """
        # Base quality
        quality = 0.7

        # Adjust based on operation type
        if task.operation == "perception":
            quality += 0.1  # Perception usually high quality
        elif task.operation == "execution":
            quality += 0.05  # Execution moderate quality

        # Adjust based on result success
        if result.get("success", True):
            quality += 0.1

        # Add small random variation (simulated)
        import hashlib
        hash_val = int(hashlib.md5(task.task_id.encode()).hexdigest(), 16)
        variation = (hash_val % 100) / 1000.0  # 0.000-0.099
        quality += variation

        # Clamp to [0, 1]
        return max(0.0, min(1.0, quality))

    def _calculate_atp_consumed(
        self,
        task: FederationTask,
        execution_time: float
    ) -> float:
        """
        Calculate ATP consumed during execution

        Based on:
        - Operation type
        - Execution time
        - Task complexity
        """
        # Base costs per operation (from real-world test)
        base_costs = {
            "perception": 5.0,
            "planning": 15.0,
            "execution": 25.0,
            "delegation": 35.0
        }

        base_atp = base_costs.get(task.operation, 10.0)

        # Add time penalty (simulated compute cost)
        time_cost = execution_time * 2.0  # 2 ATP per second

        # Total consumed (but capped at budget)
        consumed = base_atp + time_cost
        return min(consumed, task.atp_budget)

    def get_status(
        self,
        lct_id: str
    ) -> Optional[Dict]:
        """
        Get consciousness status

        Parameters:
        -----------
        lct_id : str
            LCT identity to check

        Returns:
        --------
        Optional[Dict]
            Status dictionary or None if not found
        """
        return self.manager.get_consciousness_summary(lct_id)

    def cancel_task(
        self,
        task_id: str
    ) -> Tuple[bool, float, str]:
        """
        Cancel active task

        Parameters:
        -----------
        task_id : str
            Task to cancel

        Returns:
        --------
        Tuple[bool, float, str]
            (cancelled, atp_refunded, reason) tuple
        """
        # Check if task is active
        if task_id not in self.active_tasks:
            return (False, 0.0, f"Task {task_id} not active")

        task = self.active_tasks[task_id]

        # Remove from active
        del self.active_tasks[task_id]

        # In production, would refund locked ATP
        # For now, return the budget
        return (True, task.atp_budget, "Task cancelled, ATP refunded")
