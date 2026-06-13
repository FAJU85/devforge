# Phase 1 Setup - DevForge QA Suite Foundation

## Overview

Phase 1 sets up the foundational infrastructure for the DevForge QA ML system. This includes:

- **PostgreSQL Database** - Schema for models, patterns, test cases, and failures
- **Milvus Vector Database** - Semantic search for test/error embeddings
- **MinIO Object Storage** - Dataset and model storage (S3-compatible)
- **Docker Infrastructure** - All services containerized and orchestrated

**Timeline**: 4 weeks (can be completed in 2-3 days with automation)

## Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 1.29+)
- **Python** 3.8+
- **Git**
- **Disk Space**: ~50GB minimum for containers and datasets
- **Memory**: 8GB+ recommended (containers need ~4GB)

## Quick Start

### 1. Clone and Navigate

```bash
cd /home/user/devforge
```

### 2. Run Phase 1 Setup Script

```bash
bash scripts/phase1-setup.sh
```

This automated script will:
- Check prerequisites
- Copy and configure .env file
- Start Docker containers (PostgreSQL, Milvus, MinIO)
- Initialize database schema
- Create vector indices
- Setup object storage buckets
- Verify all connections

**Expected Duration**: 5-10 minutes

### 3. Verify Setup

After the script completes, verify services are running:

```bash
# Check containers
docker ps | grep devforge

# View logs
docker-compose -f docker-compose.phase1.yml logs -f

# Access services
- PostgreSQL: psql -h localhost -U postgres -d devforge
- Milvus: python -c "from pymilvus import connections; connections.connect(host='localhost')"
- MinIO: http://localhost:9001 (admin/admin)
- PgAdmin: http://localhost:5050 (admin@devforge.local/admin)
```

## Manual Setup (If Needed)

### Step 1: Start Infrastructure

```bash
docker-compose -f docker-compose.phase1.yml up -d
```

Wait for all containers to be healthy:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Step 2: Initialize Database

```bash
# Copy schema
docker cp db/schema_v3.sql devforge-postgres:/

# Apply schema
docker exec devforge-postgres psql -U postgres -d devforge -f /schema_v3.sql

# Verify
docker exec devforge-postgres psql -U postgres -d devforge -c "\dt"
```

### Step 3: Setup Vector Database

```bash
# Install Python dependencies
pip install pymilvus>=2.3.0

# Run setup script
python ml/vector_db/setup.py
```

Expected output:
```
✓ Connected to Milvus at localhost:19530
✓ Created collection: test_embeddings
✓ Created collection: error_embeddings
✓ Created collection: code_embeddings
✓ Created collection: ui_embeddings
✓ Vector database setup complete!
```

### Step 4: Setup Object Storage

```bash
# Install Python dependencies
pip install boto3>=1.26.0

# Run setup script
python storage/setup_storage.py
```

Expected output:
```
✓ Connected to S3 storage at http://localhost:9000
✓ Created bucket 'devforge-datasets'
✓ Created bucket 'devforge-models'
✓ Created bucket 'devforge-artifacts'
✓ Created bucket 'devforge-reports'
✓ Storage setup complete!
```

## Configuration

### Environment Variables

Copy and customize `.env` file:

```bash
cp storage/config/.env.example .env
```

Key variables to customize:
- `POSTGRES_PASSWORD` - PostgreSQL password
- `MILVUS_HOST/PORT` - Vector DB connection
- `S3_*_ENDPOINT` - Storage endpoints

### Database Connection

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="devforge",
    user="postgres",
    password="postgres"
)
```

### Vector Database Connection

```python
from pymilvus import connections

connections.connect(
    alias="default",
    host="localhost",
    port=19530
)
```

### Object Storage Connection

```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)
```

## Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| PostgreSQL | `postgres://localhost:5432/devforge` | postgres/postgres |
| Milvus | `localhost:19530` | No auth |
| MinIO (Datasets) | `http://localhost:9000` | minioadmin/minioadmin |
| MinIO (Artifacts) | `http://localhost:9002` | minioadmin/minioadmin |
| MinIO Console (Datasets) | `http://localhost:9001` | minioadmin/minioadmin |
| MinIO Console (Artifacts) | `http://localhost:9003` | minioadmin/minioadmin |
| PgAdmin | `http://localhost:5050` | admin@devforge.local/admin |

## Database Schema

### Key Tables

- **ml_models** - ML model registry and metadata
- **patterns** - Learned failure patterns
- **test_cases** - Generated and manual test cases
- **test_failures** - Failed test execution records
- **bugs** - Detected bugs with suggested fixes
- **ui_patterns** - UI component patterns from RICO
- **generated_artifacts** - Tests, fixes, selectors
- **learning_sessions** - Pattern learning sessions
- **dataset_versions** - Dataset version tracking

### Vector Collections

- **test_embeddings** - Test case semantic vectors (1536-dim)
- **error_embeddings** - Error/failure semantic vectors (1536-dim)
- **code_embeddings** - Code pattern vectors (1536-dim)
- **ui_embeddings** - UI component visual vectors (1024-dim)

## Storage Structure

```
devforge-datasets/
├── repliqa/
│   ├── raw/
│   ├── processed/
│   ├── embeddings/
│   └── metadata/
├── defects4j/
├── rico/
├── the_stack/
└── manybugs/

devforge-models/
├── test_generator/
│   ├── checkpoints/
│   ├── configs/
│   ├── metrics/
│   └── inference/
├── bug_detector/
├── ui_recognizer/
├── code_analyzer/
└── fix_suggester/

devforge-artifacts/
├── tests/
│   ├── generated/
│   ├── executed/
│   └── validated/
├── fixes/
├── selectors/
└── reports/
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.phase1.yml logs postgres

# Restart services
docker-compose -f docker-compose.phase1.yml down
docker-compose -f docker-compose.phase1.yml up -d
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec devforge-postgres psql -U postgres -d devforge -c "SELECT 1;"
```

### Milvus Connection Failed

```bash
# Check Milvus is running
docker ps | grep milvus

# Check logs
docker logs devforge-milvus

# Restart Milvus
docker-compose -f docker-compose.phase1.yml restart milvus
```

### S3 Connection Failed

```bash
# Check MinIO is running
docker ps | grep minio

# Test S3 endpoint
curl http://localhost:9000/minio/health/live

# Check MinIO logs
docker logs devforge-minio
```

### Port Already in Use

Change port mappings in `docker-compose.phase1.yml`:

```yaml
services:
  postgres:
    ports:
      - "5432:5432"  # Change left side to different port
```

## Next Steps

After Phase 1 is complete:

1. **Review Database** - Browse tables and verify schema
2. **Test Connections** - Run test scripts to verify all services
3. **Setup Datasets** - Begin Phase 2 (dataset ingestion)
4. **Train Models** - Phase 2 (ML model training)
5. **Build APIs** - Phase 3 (REST API development)

## Useful Commands

```bash
# Start all services
docker-compose -f docker-compose.phase1.yml up -d

# Stop all services
docker-compose -f docker-compose.phase1.yml down

# View logs
docker-compose -f docker-compose.phase1.yml logs -f

# Access PostgreSQL
psql -h localhost -U postgres -d devforge

# Access MinIO console
# Open browser: http://localhost:9001 or http://localhost:9003

# Check service health
docker exec devforge-postgres pg_isready -U postgres
docker exec devforge-milvus curl -f http://localhost:9091/healthz
curl http://localhost:9000/minio/health/live
```

## Performance Tuning

### PostgreSQL

For larger deployments, adjust in `docker-compose.phase1.yml`:

```yaml
services:
  postgres:
    environment:
      POSTGRES_INITDB_ARGS: "-c shared_buffers=1GB -c max_connections=500"
```

### Milvus

For more data, increase memory allocation in docker-compose:

```yaml
services:
  milvus:
    deploy:
      resources:
        limits:
          memory: 4G
```

## Cleanup

To remove Phase 1 infrastructure:

```bash
# Stop containers
docker-compose -f docker-compose.phase1.yml down

# Remove volumes (WARNING: deletes data)
docker-compose -f docker-compose.phase1.yml down -v

# Remove Docker images
docker rmi milvusdb/milvus minio/minio postgres:15-alpine dpage/pgadmin4
```

## Support & Documentation

- PostgreSQL: https://www.postgresql.org/docs/
- Milvus: https://milvus.io/docs/
- MinIO: https://docs.min.io/
- Docker: https://docs.docker.com/

See `PHASE1_IMPLEMENTATION_GUIDE.md` for detailed technical documentation.
