# Docker Mesh Simulation

This directory contains the Docker configuration for running a 3-node Telex mesh simulation.

## Quick Start

Start all three nodes with a single command:

```bash
docker compose up --build
```

This will create and start:
- **telex-node-a** (DUN-A) - Duncan, exposed on port 8023
- **telex-node-b** (LON-B) - London, exposed on port 8024
- **telex-node-c** (NYC-C) - New York, exposed on port 8025

## Network Topology

The nodes form a mesh network on a custom Docker bridge network (`telex-net`):

```
     Node A (DUN-A)
          |
          |
     Node B (LON-B)
          |
          |
     Node C (NYC-C)
```

- **Node A** connects to Node B
- **Node B** connects to Node A and Node C (acts as hub)
- **Node C** connects to Node B

## Configuration

Each node has its own configuration file in `scripts/sim_configs/`:

- `node_a.json` - Configuration for Node A (DUN-A)
- `node_b.json` - Configuration for Node B (LON-B)
- `node_c.json` - Configuration for Node C (NYC-C)

These configuration files are mounted into the containers at `/etc/telex/config.json`.

## Docker Compose Commands

```bash
# Start all nodes in the background
docker compose up -d

# Build and start
docker compose up --build

# View logs from all nodes
docker compose logs -f

# View logs from a specific node
docker compose logs -f telex-node-a

# Stop all nodes
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# Restart a specific node
docker compose restart telex-node-b
```

## Accessing the Nodes

Each node exposes its Telex port to the host:

- Node A: `localhost:8023`
- Node B: `localhost:8024`
- Node C: `localhost:8025`

Within the Docker network, nodes can reach each other using their service names:
- `telex-node-a:8023`
- `telex-node-b:8023`
- `telex-node-c:8023`

## Troubleshooting

### Viewing Node Status

```bash
# Check which containers are running
docker compose ps

# Inspect a specific container
docker compose exec telex-node-a ps aux
```

### Accessing a Node's Shell

```bash
docker compose exec telex-node-a /bin/bash
```

### Network Connectivity

Test connectivity between nodes:

```bash
# From node A, ping node B
docker compose exec telex-node-a ping telex-node-b

# Check network
docker network inspect telex-net
```

### Rebuilding

If you make changes to the code or Dockerfile:

```bash
docker compose build --no-cache
docker compose up
```

## Data Persistence

Each node has its own Docker volume for persistent data:
- `telex-node-a-data`
- `telex-node-b-data`
- `telex-node-c-data`

These volumes persist message queues and databases between container restarts.

## Architecture

### Dockerfile

The Dockerfile uses a multi-stage build pattern:
1. **Builder stage**: Compiles dependencies with build tools
2. **Runtime stage**: Minimal image with only runtime dependencies

Security features:
- Runs as non-root user (`telex`)
- Minimal base image (python:3.10-slim)
- No build tools in final image

### Network Isolation

All nodes run on an isolated Docker bridge network (`telex-net`) with no access to the host network except through explicitly mapped ports.
