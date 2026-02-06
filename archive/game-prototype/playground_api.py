#!/usr/bin/env python3
"""Playground API - JSON Interface for Interactive Simulation

Provides a JSON-in, JSON-out interface for the playground simulation,
suitable for calling from web API endpoints.

Session #12: Interactive Parameter Playground
"""

import json
import sys
from dataclasses import asdict
from playground_simulation import PlaygroundConfig, run_playground_simulation


def run_from_json(config_json: str) -> str:
    """
    Run simulation with JSON config, return JSON result.

    Args:
        config_json: JSON string with configuration parameters

    Returns:
        JSON string with simulation results
    """
    # Parse config
    config_dict = json.loads(config_json)

    # Create config object
    config = PlaygroundConfig(**config_dict)

    # Run simulation
    result = run_playground_simulation(config)

    # Convert to JSON-serializable dict
    result_dict = {
        "config": asdict(config),
        "lives": [
            {
                **asdict(life),
                "actions": [asdict(action) for action in life.actions]
            }
            for life in result.lives
        ],
        "total_ticks": result.total_ticks,
        "insights": result.insights
    }

    return json.dumps(result_dict, indent=2)


def main():
    """CLI interface: read JSON from stdin, write JSON to stdout"""
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Demo mode: use default config
        config_json = json.dumps({})
    else:
        # Read config from stdin
        config_json = sys.stdin.read()

    result_json = run_from_json(config_json)
    print(result_json)


if __name__ == "__main__":
    main()
