# Neighbor Configuration for Telex Mesh Network

This file documents the neighbor relationships for the 3-node mesh simulation.
When the routing and neighbor management features are implemented, these 
relationships can be configured in the application.

## Network Topology

```
     Node A (DUN-A)
          |
          |
     Node B (LON-B)
          |
          |
     Node C (NYC-C)
```

## Neighbor Mappings

### Node A (DUN-A)
- **Neighbors**: Node B (LON-B)
- **Connection**: telex-node-b:8023

### Node B (LON-B)
- **Neighbors**: Node A (DUN-A), Node C (NYC-C)
- **Connections**: 
  - telex-node-a:8023
  - telex-node-c:8023

### Node C (NYC-C)
- **Neighbors**: Node B (LON-B)
- **Connection**: telex-node-b:8023

## Future Implementation

When neighbor management is implemented, you can configure neighbors by:

1. Adding a `neighbors` field to the TelexConfig model:
```python
from typing import List
from pydantic import BaseModel

class NeighborConfig(BaseModel):
    node_id: str
    host: str
    port: int

class TelexConfig(BaseSettings):
    # ... existing fields ...
    neighbors: List[NeighborConfig] = Field(default_factory=list)
```

2. Or by using environment variables:
```bash
TELEX_NEIGHBORS='[{"node_id":"LON-B","host":"telex-node-b","port":8023}]'
```

3. Or by implementing a separate neighbors configuration file that the 
   routing module loads independently.
