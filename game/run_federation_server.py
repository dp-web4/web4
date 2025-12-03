#!/usr/bin/env python3
"""
Run Federation Server

Start HTTP server for SAGE consciousness federation.
Enables cross-platform task delegation with ATP tracking.

Usage:
    python3 game/run_federation_server.py [--platform PLATFORM] [--port PORT]

Examples:
    python3 game/run_federation_server.py
    python3 game/run_federation_server.py --platform Legion --port 8080
    python3 game/run_federation_server.py --platform Thor --port 8082

Author: Legion Autonomous Session #54
Date: 2025-12-03
"""

import sys
from pathlib import Path
import argparse

# Add web4 root to path
_web4_root = Path(__file__).parent.parent
if str(_web4_root) not in sys.path:
    sys.path.insert(0, str(_web4_root))

from game.server.federation_server import create_federation_server


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Federation Server for SAGE Consciousness Delegation"
    )

    parser.add_argument(
        '--platform',
        type=str,
        default='Legion',
        help='Platform name (default: Legion)'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Server host (default: 0.0.0.0)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Server port (default: 8080)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    args = parser.parse_args()

    print(f"""
{'='*80}
  SAGE Federation Server
{'='*80}

Platform: {args.platform}
Host:     {args.host}
Port:     {args.port}
Debug:    {args.debug}

Press Ctrl+C to stop the server
{'='*80}
""")

    try:
        server = create_federation_server(
            platform_name=args.platform,
            host=args.host,
            port=args.port
        )

        server.run(debug=args.debug)

    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
