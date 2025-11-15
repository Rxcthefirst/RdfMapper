#!/usr/bin/env python3
"""Demo script for the configuration wizard."""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rdfmap.cli.wizard import run_wizard

if __name__ == "__main__":
    print("="*60)
    print("Configuration Wizard Demo")
    print("="*60)
    print()
    print("This will guide you through creating a mapping configuration.")
    print("Press Ctrl+C at any time to cancel.")
    print()

    try:
        config = run_wizard("demo_config.yaml")
        print("\n" + "="*60)
        print("Success! Configuration saved to demo_config.yaml")
        print("="*60)
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

