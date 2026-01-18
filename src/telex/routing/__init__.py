"""
Routing module for XXXY address-based message routing.

This module implements:
- XXXY format routing (XXX = Location Node, Y = Machine ID)
- Federated mesh routing algorithms
- Local failover logic (if target machine Y is offline, deliver to any XXX machine)
- Neighbor management and path finding
"""

__all__ = ["Router", "Address", "RoutingTable"]
