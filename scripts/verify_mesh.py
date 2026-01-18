#!/usr/bin/env python3
"""
Verification script for testing Docker mesh network connectivity.

This script attempts to connect to each of the three Telex nodes
to verify TCP/IP connectivity before implementing complex routing logic.
"""
import socket
import sys
from typing import List, Tuple


# Container configuration - internal port is always 8023
CONTAINERS = [
    ("telex-node-a", 8023),
    ("telex-node-b", 8023),
    ("telex-node-c", 8023),
]

CONNECTION_TIMEOUT = 5  # seconds


def test_connection(host: str, port: int) -> Tuple[bool, str]:
    """
    Attempt to connect to a host on a specific port.
    
    Args:
        host: Hostname or IP address
        port: Port number
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(CONNECTION_TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return True, f"✓ Connected to {host}:{port}"
        else:
            return False, f"✗ Failed to connect to {host}:{port} (error code: {result})"
    except socket.gaierror as e:
        return False, f"✗ DNS resolution failed for {host}: {e}"
    except socket.timeout:
        return False, f"✗ Connection to {host}:{port} timed out after {CONNECTION_TIMEOUT}s"
    except Exception as e:
        return False, f"✗ Error connecting to {host}:{port}: {e}"


def verify_mesh() -> bool:
    """
    Verify connectivity to all nodes in the mesh network.
    
    Returns:
        True if all connections succeeded, False otherwise
    """
    print("=" * 60)
    print("Telex Mesh Network Connectivity Test")
    print("=" * 60)
    print()
    
    results: List[Tuple[bool, str]] = []
    
    for host, port in CONTAINERS:
        print(f"Testing connection to {host}:{port}...", end=" ")
        success, message = test_connection(host, port)
        results.append((success, message))
        print(message)
    
    print()
    print("=" * 60)
    
    # Check if all connections succeeded
    all_success = all(success for success, _ in results)
    
    if all_success:
        print("✓ GREEN: Mesh Network Active")
        print("All nodes are reachable and accepting connections.")
        return True
    else:
        print("✗ RED: Connection Failed")
        failed_count = sum(1 for success, _ in results if not success)
        print(f"{failed_count} out of {len(CONTAINERS)} nodes failed connectivity test.")
        return False


def main():
    """Main entry point."""
    try:
        success = verify_mesh()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
