# Phase 1 Quick Start Guide

## Overview

Phase 1 provides a complete foundation for the DevForge QA ML system with:
- PostgreSQL database with 30+ tables
- Milvus vector database for semantic search
- MinIO object storage for datasets and models
- REST API for all operations
- Dataset ingestion pipeline
- Python clients for programmatic access

## Prerequisites

- Docker & Docker Compose
- Python 3.8+
- 8GB+ RAM
- 50GB+ disk space

## Quick Start (5 minutes)

### 1. Run Automated Setup

```bash
bash scripts/phase1-setup.sh
```

This script will:
- Check prerequisites
- Start all Docker containers
- Initialize database schema
- Create vector collections
- Setup storage buckets
- Verify all connections

### 2. Verify Installation

```bash
# Check service health
make -f Makefile.phase1 phase1-health

# Run connection tests
make -f Makefile.phase1 phase1-test

# View service status
make -f Makefile.phase1 phase1-status
```

### 3. Start API Server

```bash
# Install dependencies
pip install -r requirements-phase1.txt

# Start the API
python api/phase1_server.py

# API will be available at http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 4. Load Datasets

```bash
# Install dataset requirements
pip install -r requirements-phase1.txt

# Run dataset ingestion pipeline
python ml/dataset_loader.py

# Datasets are loaded to storage and registered in database
```

## Using Python Clients

### Connect to All Services

```python
from ml.clients import DevForgeClient

client = DevForgeClient()
client.connect_all()

# Check health
health = client.health_check()
print(health)
# Output: {'postgres': True, 'milvus': True, 'storage': True}
```

### Work with Test Cases

```python
# Insert test case
test_id = client.postgres.insert_test_case(
    name="test_login_flow",
    code="const { test } = require('@playwright/test');...",
    framework="playwright",
    source="generated"
)

# Get test case
result = client.postgres.execute(
    "SELECT * FROM test_cases WHERE id = %s",
    (test_id,)
)
```

### Work with Failures

```python
# Report failure
failure_id = client.postgres.insert_failure(
    test_id="test-123",
    error_message="Timeout waiting for element",
    error_type="timeout",
    severity="critical"
)

# Search similar errors
similar = client.vector_db.search_similar_errors(
    embedding=[0.1, 0.2, 0.3, ...],  # 1536-dim
    top_k=5
)
```

### Work with Patterns

```python
# Get learned patterns
patterns = client.postgres.get_patterns(
    category="assertion",
    min_confidence=0.8
)

for pattern in patterns:
    print(f"Pattern: {pattern['name']}")
    print(f"Confidence: {pattern['confidence']}")
    print(f"Occurrences: {pattern['occurrences']}")
```

### Work with Storage

```python
# Upload file
client.storage.upload_file(
    local_path="/path/to/dataset.json",
    s3_path="datasets/repliqa/raw/dataset.json"
)

# Download file
client.storage.download_file(
    s3_path="datasets/repliqa/raw/dataset.json",
    local_path="/path/to/local/dataset.json"
)

# List objects
objects = client.storage.list_objects(prefix="datasets/")
```

## REST API Examples

### Start API Server

```bash
python api/phase1_server.py
```

API will be available at `http://localhost:8000`

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "postgres": true,
    "milvus": true,
    "storage": true
  },
  "timestamp": "2024-06-13T12:00:00"
}
```

### Create Test Case

```bash
curl -X POST http://localhost:8000/api/test-cases \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_login",
    "code": "...",
    "framework": "playwright",
    "source": "generated"
  }'
```

### Report Failure

```bash
curl -X POST http://localhost:8000/api/failures \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "test-123",
    "error_message": "Element not found",
    "error_type": "selector",
    "severity": "high"
  }'
```

### Get Patterns

```bash
curl "http://localhost:8000/api/patterns?category=assertion&min_confidence=0.8"
```

### Search Similar Tests

```bash
curl -X POST http://localhost:8000/api/search/similar-tests \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.1, 0.2, 0.3, ...],
    "top_k": 5
  }'
```

### Upload to Storage

```bash
curl -X POST http://localhost:8000/api/storage/upload \
  -H "Content-Type: application/json" \
  -d '{
    "local_path": "/path/to/file.json",
    "remote_path": "datasets/repliqa/file.json"
  }'
```

### Get Statistics

```bash
curl http://localhost:8000/api/stats/overview
```

Response:
```json
{
  "stats": {
    "total_test_cases": 1250,
    "total_failures": 342,
    "learned_patterns": 89,
    "open_bugs": 15
  },
  "timestamp": "2024-06-13T12:00:00"
}
```

## Database Tables

### Core Tables

- **ml_models** - ML model registry
- **patterns** - Learned failure patterns
- **test_cases** - Generated and manual tests
- **test_failures** - Test execution failures
- **bugs** - Detected bugs with fixes
- **ui_patterns** - UI component patterns
- **generated_artifacts** - Generated tests/fixes
- **learning_sessions** - Pattern learning tracking
- **dataset_versions** - Dataset version control

### Querying Examples

```python
from ml.clients import PostgresClient

db = PostgresClient()
db.connect()

# Get all test cases
results = db.execute("SELECT * FROM test_cases LIMIT 10")

# Get failure statistics
results = db.execute("""
    SELECT error_type, COUNT(*) as count
    FROM test_failures
    GROUP BY error_type
    ORDER BY count DESC
""")

# Get high-confidence patterns
results = db.execute("""
    SELECT * FROM patterns
    WHERE confidence >= 0.8
    ORDER BY occurrences DESC
""")

db.disconnect()
```

## Vector Database

### Collections

1. **test_embeddings** (1536-dim)
   - Test case semantic embeddings
   - For finding similar test cases

2. **error_embeddings** (1536-dim)
   - Error/failure semantic embeddings
   - For finding similar error patterns

3. **code_embeddings** (1536-dim)
   - Code pattern embeddings
   - For finding similar code

4. **ui_embeddings** (1024-dim)
   - UI component visual embeddings
   - For finding similar UI components

### Search Examples

```python
from ml.clients import VectorDBClient

vec_db = VectorDBClient()
vec_db.connect()

# Search similar test cases
embedding = [0.1, 0.2, 0.3, ...]  # 1536-dim
results = vec_db.search_similar_tests(embedding, top_k=5)

# Search similar errors
results = vec_db.search_similar_errors(embedding, top_k=5)

vec_db.disconnect()
```

## Storage Structure

```
devforge-datasets/
├── repliqa/
│   ├── raw/
│   ├── processed/
│   └── metadata/
├── defects4j/
├── rico/
├── the_stack/
└── manybugs/

devforge-models/
├── test_generator/
├── bug_detector/
├── ui_recognizer/
├── code_analyzer/
└── fix_suggester/

devforge-artifacts/
├── tests/
├── fixes/
└── selectors/
```

## Dataset Ingestion

### Load All Datasets

```bash
python ml/dataset_loader.py
```

This will:
- Download 5 core datasets (in production)
- Process and validate data
- Register versions in database
- Upload to object storage

### Datasets Supported

1. **RepliQA** - Test specifications (10K+ specs)
2. **Defects4J** - Bug patterns (835 bugs, 17 projects)
3. **RICO** - UI patterns (66K+ screens, 6.3M components)
4. **The Stack** - Code patterns (3.1B tokens)
5. **ManyBugs** - Bug fixes (3900 versions, 185 programs)

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | postgres://localhost:5432/devforge |
| Milvus | 19530 | localhost:19530 |
| MinIO (Datasets) | 9000 | http://localhost:9000 |
| MinIO (Artifacts) | 9002 | http://localhost:9002 |
| MinIO Console (Datasets) | 9001 | http://localhost:9001 |
| MinIO Console (Artifacts) | 9003 | http://localhost:9003 |
| PgAdmin | 5050 | http://localhost:5050 |
| API Server | 8000 | http://localhost:8000 |

## Useful Commands

```bash
# Start infrastructure
make -f Makefile.phase1 phase1-start

# Stop infrastructure
make -f Makefile.phase1 phase1-stop

# View logs
make -f Makefile.phase1 phase1-logs

# Test connections
make -f Makefile.phase1 phase1-test

# View service status
make -f Makefile.phase1 phase1-status

# Connect to database
make -f Makefile.phase1 phase1-db-connect

# Access MinIO consoles
make -f Makefile.phase1 phase1-ui

# Clean up everything
make -f Makefile.phase1 phase1-clean
```

## Troubleshooting

### Container Connection Issues

```bash
# Check container status
docker ps | grep devforge

# View logs
docker logs devforge-postgres
docker logs devforge-milvus
docker logs devforge-minio
```

### Database Connection Failed

```bash
# Test connection manually
psql -h localhost -U postgres -d devforge -c "SELECT 1;"

# Check PostgreSQL health
make -f Makefile.phase1 phase1-db-status
```

### Milvus Connection Failed

```bash
# Test Milvus
python -c "
from pymilvus import connections
connections.connect(alias='default', host='localhost', port=19530)
print('✓ Milvus OK')
"
```

### S3 Connection Failed

```bash
# Test S3
curl http://localhost:9000/minio/health/live
curl http://localhost:9002/minio/health/live
```

## Next Steps

1. **Review Documentation** - Read PHASE1_SETUP_README.md
2. **Explore API** - Visit http://localhost:8000/docs
3. **Load Datasets** - Run `python ml/dataset_loader.py`
4. **Start Phase 2** - Begin ML model training
5. **Build Applications** - Use clients/API for your use cases

## Support

- PostgreSQL Docs: https://www.postgresql.org/docs/
- Milvus Docs: https://milvus.io/docs/
- MinIO Docs: https://docs.min.io/
- FastAPI Docs: https://fastapi.tiangolo.com/
- Docker Docs: https://docs.docker.com/

## Additional Resources

- Main Plan: `COMPREHENSIVE_QA_UPGRADE_PLAN.md`
- Setup Guide: `PHASE1_SETUP_README.md`
- Implementation: `PHASE1_IMPLEMENTATION_GUIDE.md`
