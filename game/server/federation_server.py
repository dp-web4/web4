"""
Federation Server - HTTP Server for SAGE Consciousness Delegation

Provides HTTP server for cross-platform SAGE consciousness task delegation.
Built on FederationAPI with Flask for HTTP handling.

Author: Legion Autonomous Session #54
Date: 2025-12-03
References: MULTI_MACHINE_SAGE_FEDERATION_DESIGN.md
"""

from typing import Dict, Tuple
import json
import traceback

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Warning: Flask not available. Install with: pip install flask")

from game.server.federation_api import (
    FederationAPI,
    FederationTask,
    ExecutionProof
)


class FederationServer:
    """
    HTTP server for SAGE consciousness federation

    Provides REST API endpoints for task delegation, status checking,
    and task cancellation.
    """

    def __init__(
        self,
        platform_name: str,
        host: str = "0.0.0.0",
        port: int = 8080
    ):
        """
        Initialize Federation Server

        Parameters:
        -----------
        platform_name : str
            Platform identifier (e.g., "Legion")
        host : str
            Server host (default: 0.0.0.0)
        port : int
            Server port (default: 8080)
        """
        if not FLASK_AVAILABLE:
            raise RuntimeError("Flask is required for FederationServer")

        self.platform_name = platform_name
        self.host = host
        self.port = port
        self.api = FederationAPI(platform_name)
        self.app = Flask(f"federation-{platform_name}")

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register HTTP routes"""

        @self.app.route('/api/v1/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "platform": self.platform_name,
                "active_tasks": len(self.api.active_tasks),
                "completed_tasks": len(self.api.completed_tasks)
            })

        @self.app.route('/api/v1/consciousness/delegate', methods=['POST'])
        def delegate():
            """
            Delegate consciousness task

            Request Body:
            {
                "task": {FederationTask},
                "signature": "<base64_encoded_signature>"
            }

            Response:
            {
                "success": true/false,
                "proof": {ExecutionProof} or null,
                "error": "error message" or null
            }
            """
            try:
                # Parse request
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "proof": None,
                        "error": "No JSON data provided"
                    }), 400

                # Extract task
                task_data = data.get('task')
                if not task_data:
                    return jsonify({
                        "success": False,
                        "proof": None,
                        "error": "No task provided"
                    }), 400

                # Parse task
                try:
                    task = FederationTask.from_dict(task_data)
                except Exception as e:
                    return jsonify({
                        "success": False,
                        "proof": None,
                        "error": f"Invalid task format: {str(e)}"
                    }), 400

                # Extract signature (for future Ed25519 verification)
                signature = data.get('signature', b'')
                if isinstance(signature, str):
                    import base64
                    signature = base64.b64decode(signature)

                # Delegate task
                proof, error = self.api.delegate_consciousness_task(task, signature)

                if proof:
                    return jsonify({
                        "success": True,
                        "proof": proof.to_dict(),
                        "error": None
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "proof": None,
                        "error": error
                    }), 400

            except Exception as e:
                traceback.print_exc()
                return jsonify({
                    "success": False,
                    "proof": None,
                    "error": f"Internal server error: {str(e)}"
                }), 500

        @self.app.route('/api/v1/consciousness/status/<path:lct_id>', methods=['GET'])
        def status(lct_id: str):
            """
            Get consciousness status

            Parameters:
            -----------
            lct_id : str
                LCT identity (URL-encoded)

            Response:
            {
                "success": true/false,
                "status": {dict} or null,
                "error": "error message" or null
            }
            """
            try:
                # Decode LCT ID (replace %23 with #, etc.)
                from urllib.parse import unquote
                lct_id_decoded = unquote(lct_id)

                # Get status
                status_dict = self.api.get_status(lct_id_decoded)

                if status_dict:
                    return jsonify({
                        "success": True,
                        "status": status_dict,
                        "error": None
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "status": None,
                        "error": f"No consciousness found for {lct_id_decoded}"
                    }), 404

            except Exception as e:
                traceback.print_exc()
                return jsonify({
                    "success": False,
                    "status": None,
                    "error": f"Internal server error: {str(e)}"
                }), 500

        @self.app.route('/api/v1/consciousness/cancel/<task_id>', methods=['POST'])
        def cancel(task_id: str):
            """
            Cancel active task

            Parameters:
            -----------
            task_id : str
                Task ID to cancel

            Response:
            {
                "success": true/false,
                "cancelled": true/false,
                "atp_refunded": float,
                "error": "error message" or null
            }
            """
            try:
                # Cancel task
                cancelled, atp_refunded, reason = self.api.cancel_task(task_id)

                if cancelled:
                    return jsonify({
                        "success": True,
                        "cancelled": True,
                        "atp_refunded": atp_refunded,
                        "error": None
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "cancelled": False,
                        "atp_refunded": 0.0,
                        "error": reason
                    }), 400

            except Exception as e:
                traceback.print_exc()
                return jsonify({
                    "success": False,
                    "cancelled": False,
                    "atp_refunded": 0.0,
                    "error": f"Internal server error: {str(e)}"
                }), 500

    def run(self, debug: bool = False):
        """
        Run the federation server

        Parameters:
        -----------
        debug : bool
            Enable debug mode (default: False)
        """
        print(f"Starting Federation Server: {self.platform_name}")
        print(f"Listening on http://{self.host}:{self.port}")
        print(f"\nEndpoints:")
        print(f"  GET  /api/v1/health")
        print(f"  POST /api/v1/consciousness/delegate")
        print(f"  GET  /api/v1/consciousness/status/<lct_id>")
        print(f"  POST /api/v1/consciousness/cancel/<task_id>")
        print()

        self.app.run(
            host=self.host,
            port=self.port,
            debug=debug
        )


def create_federation_server(
    platform_name: str,
    host: str = "0.0.0.0",
    port: int = 8080
) -> FederationServer:
    """
    Factory function to create Federation Server

    Parameters:
    -----------
    platform_name : str
        Platform identifier
    host : str
        Server host
    port : int
        Server port

    Returns:
    --------
    FederationServer
        Configured server instance
    """
    return FederationServer(platform_name, host, port)
