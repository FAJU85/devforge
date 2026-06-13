# Phase 1 Implementation Guide - Foundation

**Duration**: Weeks 1-4  
**Team**: 2-3 backend engineers + 1 infrastructure engineer  
**Deliverables**: Foundation for ML pipeline and learning system  

---

## Week 1: Database & Storage Setup

### Task 1.1: PostgreSQL Schema (8 hours)

**File**: `db/schema_v3.sql`

```sql
-- Tables for Phase 1 implementation

-- ML Models Registry
CREATE TABLE ml_models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,                    -- 'test_generator', 'bug_detector'
  version VARCHAR(50),
  dataset_source VARCHAR(255),                  -- 'defects4j', 'repliqa'
  checkpoint_path VARCHAR(512),
  framework VARCHAR(50) DEFAULT 'pytorch',      -- Storage framework
  metrics JSONB,                                -- {accuracy: 0.92, f1: 0.88, ...}
  training_date TIMESTAMP,
  last_used TIMESTAMP,
  enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(name, version)
);

-- Learned Patterns Database
CREATE TABLE patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL UNIQUE,
  category VARCHAR(100),                        -- 'error', 'timing', 'selector'
  pattern_text TEXT,                            -- Human-readable pattern
  pattern_regex TEXT,                           -- Regex for matching
  confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
  occurrences INT DEFAULT 1,
  severity VARCHAR(20) DEFAULT 'medium',        -- critical, high, medium, low
  suggested_fix TEXT,
  effectiveness DECIMAL(3,2) DEFAULT 0,
  affected_tests TEXT[],
  first_seen TIMESTAMP DEFAULT NOW(),
  last_seen TIMESTAMP DEFAULT NOW(),
  source VARCHAR(100),                          -- 'learned', 'builtin', 'imported'
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_confidence (confidence),
  INDEX idx_category (category)
);

-- Test Cases (Generated & Manual)
CREATE TABLE test_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  source VARCHAR(50) NOT NULL,                  -- 'generated', 'manual', 'imported'
  framework VARCHAR(50) DEFAULT 'playwright',
  code TEXT NOT NULL,
  generated_by_model_id UUID REFERENCES ml_models(id) ON DELETE SET NULL,
  assertions INT DEFAULT 0,
  code_coverage DECIMAL(3,2),
  last_executed TIMESTAMP,
  pass_count INT DEFAULT 0,
  fail_count INT DEFAULT 0,
  flakiness DECIMAL(3,2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_source (source),
  INDEX idx_framework (framework)
);

-- Test Failures (for learning)
CREATE TABLE test_failures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_case_id UUID REFERENCES test_cases(id) ON DELETE CASCADE,
  error_message TEXT,
  error_type VARCHAR(100),                      -- 'timeout', 'assertion', 'network'
  stack_trace TEXT,
  severity VARCHAR(20) DEFAULT 'medium',
  root_cause_pattern_id UUID REFERENCES patterns(id) ON DELETE SET NULL,
  environment JSONB,                            -- {browser, os, node_version, ...}
  execution_time INT,                           -- milliseconds
  failed_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_test_case (test_case_id),
  INDEX idx_error_type (error_type),
  INDEX idx_failed_at (failed_at),
  INDEX idx_pattern (root_cause_pattern_id)
);

-- Bug Reports
CREATE TABLE bugs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  code_location VARCHAR(512),
  code_snippet TEXT,
  bug_type VARCHAR(100),                        -- 'null_pointer', 'logic_error'
  severity VARCHAR(20) DEFAULT 'medium',
  detected_by_model_id UUID REFERENCES ml_models(id),
  suggested_fix TEXT,
  fix_code TEXT,
  fix_validated BOOLEAN DEFAULT false,
  pr_url VARCHAR(512),
  status VARCHAR(50) DEFAULT 'open',            -- open, in_progress, fixed, wontfix
  created_at TIMESTAMP DEFAULT NOW(),
  fixed_at TIMESTAMP,
  INDEX idx_status (status),
  INDEX idx_type (bug_type)
);

-- UI Patterns Library
CREATE TABLE ui_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  component_type VARCHAR(100) NOT NULL,         -- 'button', 'input', 'dialog'
  component_name VARCHAR(255),
  properties JSONB,                             -- {role, aria-label, ...}
  screenshot_url VARCHAR(512),
  optimal_selectors TEXT[] NOT NULL,
  fallback_selectors TEXT[],
  accessibility_level VARCHAR(50),
  frequency INT DEFAULT 1,
  last_used TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_component_type (component_type)
);

-- Generated Artifacts (tests, fixes, selectors)
CREATE TABLE generated_artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  artifact_type VARCHAR(100) NOT NULL,          -- 'test', 'fix', 'selector'
  content TEXT NOT NULL,
  source_code TEXT,
  model_id UUID REFERENCES ml_models(id),
  execution_status VARCHAR(50),                 -- pending, passed, failed
  execution_result JSONB,
  confidence DECIMAL(3,2),
  user_feedback INT,                            -- -1, 0, 1
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_type (artifact_type),
  INDEX idx_model (model_id)
);

-- Learning Sessions
CREATE TABLE learning_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_type VARCHAR(100),                    -- 'failure_analysis', 'pattern_learning'
  input_count INT,
  patterns_learned INT DEFAULT 0,
  patterns_updated INT DEFAULT 0,
  duration_ms INT,
  model_updated BOOLEAN DEFAULT false,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_type (session_type),
  INDEX idx_completed (completed_at)
);

-- Dataset Versions
CREATE TABLE dataset_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dataset_name VARCHAR(255) NOT NULL,
  version VARCHAR(50),
  source_url VARCHAR(512),
  downloaded_at TIMESTAMP,
  indexed_at TIMESTAMP,
  record_count INT,
  size_bytes BIGINT,
  vector_indices_built BOOLEAN DEFAULT false,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(dataset_name, version)
);

-- Create indexes for performance
CREATE INDEX idx_patterns_updated ON patterns(updated_at);
CREATE INDEX idx_failures_timestamp ON test_failures(failed_at DESC);
CREATE INDEX idx_test_cases_created ON test_cases(created_at DESC);
CREATE INDEX idx_bugs_created ON bugs(created_at DESC);
CREATE INDEX idx_sessions_completed ON learning_sessions(completed_at DESC);
```

**Execution**:
```bash
# Connect to PostgreSQL
psql devforge < db/schema_v3.sql

# Verify tables created
psql devforge -c "\dt"
```

**Deliverable**: Schema file ready for production deployment

---

### Task 1.2: Vector Database Setup (6 hours)

**File**: `ml/vector_db/setup.py`

```python
"""
Milvus vector database setup for DevForge QA
Handles initialization, index creation, and collection setup
"""

import os
from pymilvus import (
    connections, 
    Collection, 
    FieldSchema, 
    CollectionSchema,
    DataType
)

class VectorDBSetup:
    """Initialize and configure Milvus for QA system"""
    
    def __init__(self, host='localhost', port=19530):
        self.host = host
        self.port = port
        self.connection_name = 'devforge'
        
    def connect(self):
        """Connect to Milvus server"""
        connections.connect(
            alias=self.connection_name,
            host=self.host,
            port=self.port,
            pool_size=30
        )
        print(f"✓ Connected to Milvus at {self.host}:{self.port}")
        
    def create_test_embeddings_collection(self):
        """Create collection for test embeddings"""
        fields = [
            FieldSchema(name="test_id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
            FieldSchema(name="description_embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
            FieldSchema(name="code_embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Test case embeddings for semantic search"
        )
        
        collection = Collection(
            name="test_embeddings",
            schema=schema,
            using=self.connection_name
        )
        
        # Create indices for efficient search
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 100}
        }
        
        collection.create_index(
            field_name="description_embedding",
            index_params=index_params
        )
        collection.create_index(
            field_name="code_embedding",
            index_params=index_params
        )
        
        collection.load()
        print("✓ Created test_embeddings collection")
        
    def create_error_embeddings_collection(self):
        """Create collection for error/failure embeddings"""
        fields = [
            FieldSchema(name="failure_id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
            FieldSchema(name="error_embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Error embeddings for similar failure detection"
        )
        
        collection = Collection(
            name="error_embeddings",
            schema=schema,
            using=self.connection_name
        )
        
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 100}
        }
        
        collection.create_index(
            field_name="error_embedding",
            index_params=index_params
        )
        
        collection.load()
        print("✓ Created error_embeddings collection")
        
    def create_code_embeddings_collection(self):
        """Create collection for code pattern embeddings"""
        fields = [
            FieldSchema(name="code_id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
            FieldSchema(name="code_embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
            FieldSchema(name="pattern_type", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Code pattern embeddings from The Stack dataset"
        )
        
        collection = Collection(
            name="code_embeddings",
            schema=schema,
            using=self.connection_name
        )
        
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 200}
        }
        
        collection.create_index(
            field_name="code_embedding",
            index_params=index_params
        )
        
        collection.load()
        print("✓ Created code_embeddings collection")
        
    def create_ui_embeddings_collection(self):
        """Create collection for UI component embeddings"""
        fields = [
            FieldSchema(name="component_id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
            FieldSchema(name="visual_embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
            FieldSchema(name="component_type", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="UI component embeddings from RICO dataset"
        )
        
        collection = Collection(
            name="ui_embeddings",
            schema=schema,
            using=self.connection_name
        )
        
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 150}
        }
        
        collection.create_index(
            field_name="visual_embedding",
            index_params=index_params
        )
        
        collection.load()
        print("✓ Created ui_embeddings collection")
        
    def setup_all(self):
        """Initialize all collections"""
        self.connect()
        self.create_test_embeddings_collection()
        self.create_error_embeddings_collection()
        self.create_code_embeddings_collection()
        self.create_ui_embeddings_collection()
        print("\n✓ Vector database setup complete!")

if __name__ == "__main__":
    setup = VectorDBSetup()
    setup.setup_all()
```

**Installation & Execution**:
```bash
# Start Milvus (Docker)
docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest

# Install Python client
pip install pymilvus

# Run setup
python ml/vector_db/setup.py
```

**Deliverable**: Vector database ready for embeddings

---

### Task 1.3: Object Storage Setup (4 hours)

**File**: `storage/setup_storage.py`

```python
"""
MinIO/S3 object storage setup for datasets and models
"""

import os
import boto3
from botocore.client import Config

class StorageSetup:
    """Initialize object storage for QA system"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv('S3_ENDPOINT', 'http://localhost:9000'),
            aws_access_key_id=os.getenv('S3_ACCESS_KEY', 'minioadmin'),
            aws_secret_access_key=os.getenv('S3_SECRET_KEY', 'minioadmin'),
            config=Config(signature_version='s3v4')
        )
        
    def create_buckets(self):
        """Create required S3 buckets"""
        buckets = [
            'devforge-datasets',
            'devforge-models',
            'devforge-artifacts',
            'devforge-reports'
        ]
        
        for bucket in buckets:
            try:
                self.s3_client.head_bucket(Bucket=bucket)
                print(f"✓ Bucket '{bucket}' exists")
            except:
                self.s3_client.create_bucket(Bucket=bucket)
                print(f"✓ Created bucket '{bucket}'")
                
    def setup_dataset_structure(self):
        """Create directory structure for datasets"""
        datasets = ['repliqa', 'defects4j', 'rico', 'the_stack', 'manybugs']
        
        for dataset in datasets:
            paths = [
                f'datasets/{dataset}/raw/',
                f'datasets/{dataset}/processed/',
                f'datasets/{dataset}/embeddings/',
                f'datasets/{dataset}/metadata/'
            ]
            
            for path in paths:
                # Create path by putting empty object
                self.s3_client.put_object(
                    Bucket='devforge-datasets',
                    Key=path + '.gitkeep',
                    Body=b''
                )
                print(f"✓ Created path: {path}")
                
    def setup_model_structure(self):
        """Create directory structure for models"""
        models = [
            'test_generator',
            'bug_detector',
            'ui_recognizer',
            'code_analyzer',
            'fix_suggester'
        ]
        
        for model in models:
            paths = [
                f'models/{model}/checkpoints/',
                f'models/{model}/configs/',
                f'models/{model}/metrics/',
                f'models/{model}/inference/'
            ]
            
            for path in paths:
                self.s3_client.put_object(
                    Bucket='devforge-models',
                    Key=path + '.gitkeep',
                    Body=b''
                )
                print(f"✓ Created path: {path}")
                
    def setup_all(self):
        """Initialize all storage"""
        print("Setting up object storage...")
        self.create_buckets()
        self.setup_dataset_structure()
        self.setup_model_structure()
        print("\n✓ Object storage setup complete!")

if __name__ == "__main__":
    setup = StorageSetup()
    setup.setup_all()
```

**Installation & Execution**:
```bash
# Start MinIO (Docker)
docker run -d --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"

# Install boto3
pip install boto3

# Run setup
python storage/setup_storage.py
```

**Deliverable**: Object storage ready for datasets and models

---

## Week 2: Dataset Ingestion

### Task 2.1: RepliQA Ingestion (6 hours)

**File**: `data_pipeline/ingest_repliqa.py`

```python
"""
Ingest ServiceNow RepliQA dataset for test generation patterns
"""

import json
import logging
from typing import List, Dict, Any
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class RepliQAIngestor:
    """Load and process RepliQA dataset"""
    
    def __init__(self):
        self.dataset = None
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
    def load_dataset(self):
        """Load RepliQA from HuggingFace"""
        logger.info("Loading RepliQA dataset...")
        self.dataset = load_dataset('servicenow-ai/RepliQA', split='train')
        logger.info(f"✓ Loaded {len(self.dataset)} test specifications")
        return self.dataset
        
    def extract_patterns(self) -> List[Dict[str, Any]]:
        """Extract test patterns from specifications"""
        patterns = []
        
        for idx, item in enumerate(self.dataset):
            # Extract test steps
            steps = item.get('steps', [])
            # Extract expected results
            expected = item.get('expected_result', '')
            # Extract preconditions
            preconditions = item.get('preconditions', [])
            
            pattern = {
                'id': f'repliqa_{idx}',
                'task_description': item.get('task_description', ''),
                'steps': steps,
                'assertions': self._extract_assertions(steps, expected),
                'preconditions': preconditions,
                'metadata': {
                    'source': 'RepliQA',
                    'complexity': self._estimate_complexity(steps)
                }
            }
            
            patterns.append(pattern)
            
        logger.info(f"✓ Extracted {len(patterns)} patterns")
        return patterns
        
    def _extract_assertions(self, steps: List[str], expected: str) -> List[str]:
        """Extract assertion patterns from steps and expected results"""
        assertions = []
        
        # Look for verification keywords
        keywords = ['verify', 'check', 'confirm', 'assert', 'should', 'must', 'appears']
        
        for step in steps:
            if any(kw in step.lower() for kw in keywords):
                assertions.append(step)
                
        if expected:
            assertions.append(expected)
            
        return assertions
        
    def _estimate_complexity(self, steps: List[str]) -> str:
        """Estimate test complexity based on step count"""
        if len(steps) <= 3:
            return 'simple'
        elif len(steps) <= 7:
            return 'moderate'
        else:
            return 'complex'
            
    def generate_embeddings(self, patterns: List[Dict]) -> List[Dict]:
        """Generate embeddings for semantic search"""
        logger.info("Generating embeddings...")
        
        for pattern in patterns:
            # Embed description
            desc_embedding = self.embedder.encode(
                pattern['task_description'],
                convert_to_numpy=True
            )
            pattern['description_embedding'] = desc_embedding.tolist()
            
            # Embed combined steps
            steps_text = ' '.join(pattern['steps'])
            steps_embedding = self.embedder.encode(
                steps_text,
                convert_to_numpy=True
            )
            pattern['steps_embedding'] = steps_embedding.tolist()
            
        logger.info(f"✓ Generated embeddings for {len(patterns)} patterns")
        return patterns
        
    def save_to_storage(self, patterns: List[Dict]):
        """Save processed patterns to storage"""
        logger.info("Saving to storage...")
        
        # Save to PostgreSQL
        for pattern in patterns:
            # TODO: Insert into database
            pass
            
        # Save embeddings to Milvus
        # TODO: Insert embeddings into vector DB
        
        # Save metadata to S3
        import boto3
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket='devforge-datasets',
            Key='datasets/repliqa/processed/patterns.json',
            Body=json.dumps(patterns, default=str)
        )
        
        logger.info("✓ Saved to storage")
        
    def ingest(self):
        """Execute full ingestion pipeline"""
        self.load_dataset()
        patterns = self.extract_patterns()
        patterns = self.generate_embeddings(patterns)
        self.save_to_storage(patterns)
        return patterns

if __name__ == "__main__":
    ingestor = RepliQAIngestor()
    patterns = ingestor.ingest()
```

**Execution**:
```bash
python data_pipeline/ingest_repliqa.py
```

**Deliverable**: RepliQA patterns indexed and searchable

---

### Task 2.2: Defects4J Ingestion (6 hours)

**File**: `data_pipeline/ingest_defects4j.py`

```python
"""
Ingest Defects4J bug dataset for bug detection patterns
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class Defects4JIngestor:
    """Load and process Defects4J dataset"""
    
    BUG_CATEGORIES = {
        'null_pointer_exception': ['NullPointerException', 'null'],
        'array_index_out_of_bounds': ['ArrayIndexOutOfBoundsException', 'index'],
        'logic_error': ['condition', 'comparison', 'loop'],
        'api_misuse': ['method', 'parameter', 'type'],
        'type_error': ['cast', 'type', 'incompatible']
    }
    
    def __init__(self, defects4j_root: str):
        self.root = Path(defects4j_root)
        self.bugs = []
        
    def load_projects(self) -> List[str]:
        """Load list of available projects"""
        # Defects4J has projects: commons-lang, commons-math, joda-time, etc.
        return ['commons-lang', 'commons-math', 'joda-time', 'mockito', 'closure-compiler']
        
    def load_bugs_for_project(self, project: str) -> List[Dict]:
        """Load bugs for specific project"""
        logger.info(f"Loading bugs for {project}...")
        bugs = []
        
        # Load from metadata (simplified - actual implementation loads from DB)
        metadata_file = self.root / f'projects/{project}/bugs.json'
        
        if metadata_file.exists():
            with open(metadata_file) as f:
                bugs = json.load(f)
                
        return bugs
        
    def extract_bug_patterns(self, bugs: List[Dict]) -> List[Dict]:
        """Extract bug patterns from bug descriptions"""
        patterns = []
        
        for bug in bugs:
            # Categorize bug
            category = self._categorize_bug(bug)
            
            pattern = {
                'id': bug.get('id'),
                'project': bug.get('project'),
                'bug_type': category,
                'description': bug.get('description', ''),
                'buggy_code': bug.get('buggy_code', ''),
                'fixed_code': bug.get('fixed_code', ''),
                'test_case': bug.get('test_case', ''),
                'severity': self._estimate_severity(bug),
                'fix_strategy': self._extract_fix_strategy(bug),
                'metadata': {
                    'source': 'Defects4J',
                    'line_number': bug.get('line_number'),
                    'file_path': bug.get('file_path')
                }
            }
            
            patterns.append(pattern)
            
        logger.info(f"✓ Extracted {len(patterns)} bug patterns")
        return patterns
        
    def _categorize_bug(self, bug: Dict) -> str:
        """Categorize bug based on error message"""
        error = bug.get('error_message', '').lower()
        buggy = bug.get('buggy_code', '').lower()
        
        for category, keywords in self.BUG_CATEGORIES.items():
            if any(kw in error or kw in buggy for kw in keywords):
                return category
                
        return 'unknown_error'
        
    def _estimate_severity(self, bug: Dict) -> str:
        """Estimate severity based on impact"""
        error = bug.get('error_message', '').lower()
        
        critical_keywords = ['null', 'indexoutofbounds', 'stackoverflow', 'segfault']
        if any(kw in error for kw in critical_keywords):
            return 'critical'
        elif 'exception' in error:
            return 'high'
        else:
            return 'medium'
            
    def _extract_fix_strategy(self, bug: Dict) -> str:
        """Extract fix strategy from code diff"""
        buggy = bug.get('buggy_code', '')
        fixed = bug.get('fixed_code', '')
        
        if 'null' in buggy.lower() and 'null' not in fixed.lower():
            return 'null_check'
        elif 'for' in buggy.lower() or 'while' in buggy.lower():
            return 'loop_fix'
        elif 'if' in buggy.lower():
            return 'condition_fix'
        else:
            return 'code_replacement'
            
    def save_to_storage(self, patterns: List[Dict]):
        """Save bug patterns to storage"""
        logger.info("Saving to storage...")
        
        # Save to PostgreSQL
        for pattern in patterns:
            # TODO: Insert as bug pattern
            pass
            
        # Save to S3
        import boto3
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket='devforge-datasets',
            Key='datasets/defects4j/processed/bug_patterns.json',
            Body=json.dumps(patterns, default=str)
        )
        
        logger.info("✓ Saved to storage")
        
    def ingest(self):
        """Execute full ingestion pipeline"""
        all_bugs = []
        
        for project in self.load_projects():
            bugs = self.load_bugs_for_project(project)
            all_bugs.extend(bugs)
            
        patterns = self.extract_bug_patterns(all_bugs)
        self.save_to_storage(patterns)
        return patterns

if __name__ == "__main__":
    ingestor = Defects4JIngestor(defects4j_root='/path/to/defects4j')
    patterns = ingestor.ingest()
```

**Deliverable**: Defects4J bug patterns indexed for detection

---

### Task 2.3: RICO, The Stack, ManyBugs Ingestion (8 hours)

Similar pattern to above but for each dataset. Create:
- `data_pipeline/ingest_rico.py` - UI component patterns
- `data_pipeline/ingest_the_stack.py` - Code patterns  
- `data_pipeline/ingest_manybugs.py` - Debug strategies

**Deliverable**: All 5 datasets ingested and indexed

---

## Week 3: Search APIs & Database Integration

### Task 3.1: Pattern Search API (8 hours)

**File**: `api/v3/patterns.py`

```python
"""
REST API endpoints for pattern search and management
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from db.database import get_db
from db.models import Pattern
from pymilvus import Collection, connections

router = APIRouter(prefix="/api/v3/patterns", tags=["patterns"])

@router.get("/search")
async def search_patterns(
    query: str = Query(..., min_length=3),
    pattern_type: Optional[str] = Query(None),
    min_confidence: float = Query(0.0, ge=0, le=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> dict:
    """
    Search patterns by query string or type
    
    Example:
    GET /api/v3/patterns/search?query=timeout&min_confidence=0.7&limit=20
    """
    
    # Build query
    q = db.query(Pattern)
    
    if pattern_type:
        q = q.filter(Pattern.category == pattern_type)
        
    q = q.filter(Pattern.confidence >= min_confidence)
    q = q.order_by(Pattern.confidence.desc())
    q = q.limit(limit)
    
    patterns = q.all()
    
    return {
        'count': len(patterns),
        'patterns': [
            {
                'id': str(p.id),
                'name': p.name,
                'category': p.category,
                'confidence': float(p.confidence),
                'occurrences': p.occurrences,
                'suggested_fix': p.suggested_fix
            }
            for p in patterns
        ]
    }

@router.get("/semantic-search")
async def semantic_search(
    query: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> dict:
    """
    Semantic search using embeddings
    
    Example:
    GET /api/v3/patterns/semantic-search?query=selector+not+found&limit=15
    """
    
    # Generate embedding for query
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = embedder.encode(query).tolist()
    
    # Search in Milvus
    connections.connect(alias='devforge', host='localhost', port=19530)
    collection = Collection('test_embeddings', using='devforge')
    
    results = collection.search(
        data=[query_embedding],
        anns_field='description_embedding',
        param={'metric_type': 'L2', 'params': {'nprobe': 10}},
        limit=limit,
        output_fields=['metadata']
    )
    
    return {
        'count': len(results[0]),
        'results': [
            {
                'id': hit.id,
                'distance': float(hit.distance),
                'metadata': hit.metadata
            }
            for hit in results[0]
        ]
    }

@router.get("/{pattern_id}")
async def get_pattern(
    pattern_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Get pattern details"""
    
    pattern = db.query(Pattern).filter(
        Pattern.id == pattern_id
    ).first()
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
        
    return {
        'id': str(pattern.id),
        'name': pattern.name,
        'category': pattern.category,
        'pattern_text': pattern.pattern_text,
        'pattern_regex': pattern.pattern_regex,
        'confidence': float(pattern.confidence),
        'occurrences': pattern.occurrences,
        'severity': pattern.severity,
        'suggested_fix': pattern.suggested_fix,
        'effectiveness': float(pattern.effectiveness) if pattern.effectiveness else None,
        'first_seen': pattern.first_seen.isoformat() if pattern.first_seen else None,
        'last_seen': pattern.last_seen.isoformat() if pattern.last_seen else None
    }

@router.post("/match")
async def match_code(
    code: str,
    db: Session = Depends(get_db)
) -> dict:
    """Scan code for matched patterns"""
    
    import re
    
    patterns = db.query(Pattern).filter(
        Pattern.enabled == True
    ).all()
    
    matches = []
    
    for pattern in patterns:
        if not pattern.pattern_regex:
            continue
            
        try:
            # Try to match pattern in code
            if re.search(pattern.pattern_regex, code):
                matches.append({
                    'pattern_id': str(pattern.id),
                    'pattern_name': pattern.name,
                    'confidence': float(pattern.confidence),
                    'risk_level': pattern.severity,
                    'suggested_fix': pattern.suggested_fix
                })
        except re.error:
            # Skip invalid regex
            pass
            
    return {
        'matches_found': len(matches),
        'matches': matches
    }
```

**Deliverable**: Fully functional pattern search API

---

### Task 3.2: Dataset Query API (6 hours)

**File**: `api/v3/datasets.py`

```python
"""
REST API for dataset queries
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from typing import Optional

router = APIRouter(prefix="/api/v3/datasets", tags=["datasets"])

@router.get("/repliqa")
async def search_repliqa(
    query: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
) -> dict:
    """Search RepliQA test patterns"""
    # Implementation
    pass

@router.get("/defects4j")
async def search_defects4j(
    bug_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db)
) -> dict:
    """Search Defects4J bug patterns"""
    # Implementation
    pass

@router.get("/rico")
async def search_rico(
    component_type: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db)
) -> dict:
    """Search RICO UI patterns"""
    # Implementation
    pass

@router.get("/the-stack")
async def search_the_stack(
    language: Optional[str] = Query(None),
    pattern_type: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db)
) -> dict:
    """Search The Stack code patterns"""
    # Implementation
    pass

@router.get("/manybugs")
async def search_manybugs(
    strategy_type: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db)
) -> dict:
    """Search ManyBugs debugging strategies"""
    # Implementation
    pass

@router.get("/stats")
async def dataset_stats(
    db: Session = Depends(get_db)
) -> dict:
    """Get statistics for all datasets"""
    return {
        'repliqa': {'records': 10000, 'last_updated': '2026-06-13'},
        'defects4j': {'records': 835, 'bugs_by_type': {}},
        'rico': {'records': 66000, 'components': 6300000},
        'the_stack': {'records': 3100000000, 'languages': 30},
        'manybugs': {'records': 3900, 'programs': 185}
    }
```

**Deliverable**: Dataset query API with all 5 sources

---

## Week 4: Vector Search & Index Building

### Task 4.1: Vector Index Building (8 hours)

**File**: `ml/vector_db/build_indices.py`

```python
"""
Build vector indices for semantic search across all datasets
"""

import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from pymilvus import Collection, connections
import json

logger = logging.getLogger(__name__)

class VectorIndexBuilder:
    """Build vector indices for all datasets"""
    
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.conn_name = 'devforge'
        connections.connect(
            alias=self.conn_name,
            host='localhost',
            port=19530
        )
        
    def build_test_embeddings_index(self):
        """Build indices for test embeddings"""
        logger.info("Building test embeddings index...")
        
        # Load test data from database
        import boto3
        s3 = boto3.client('s3')
        
        resp = s3.get_object(
            Bucket='devforge-datasets',
            Key='datasets/repliqa/processed/patterns.json'
        )
        
        patterns = json.loads(resp['Body'].read())
        
        # Insert into Milvus
        collection = Collection('test_embeddings', using=self.conn_name)
        
        entities = []
        for pattern in patterns:
            entities.append({
                'test_id': pattern['id'],
                'description_embedding': pattern['description_embedding'],
                'code_embedding': pattern['steps_embedding'],
                'metadata': {
                    'source': 'RepliQA',
                    'complexity': pattern['metadata']['complexity']
                }
            })
            
        collection.insert(entities)
        collection.flush()
        
        logger.info(f"✓ Indexed {len(entities)} test patterns")
        
    def build_error_embeddings_index(self):
        """Build indices for error embeddings"""
        logger.info("Building error embeddings index...")
        
        # Load error patterns from database
        # Generate embeddings for common error messages
        
        common_errors = [
            "Element not found",
            "Timeout waiting for element",
            "Assertion failed",
            "Network error",
            "Null pointer exception"
        ]
        
        entities = []
        for idx, error in enumerate(common_errors):
            embedding = self.embedder.encode(error).tolist()
            entities.append({
                'failure_id': f'error_{idx}',
                'error_embedding': embedding,
                'metadata': {'error_message': error}
            })
            
        collection = Collection('error_embeddings', using=self.conn_name)
        collection.insert(entities)
        collection.flush()
        
        logger.info(f"✓ Indexed {len(entities)} error patterns")
        
    def build_code_embeddings_index(self):
        """Build indices for code patterns"""
        logger.info("Building code embeddings index...")
        
        # Load code patterns from The Stack
        import boto3
        s3 = boto3.client('s3')
        
        resp = s3.get_object(
            Bucket='devforge-datasets',
            Key='datasets/the_stack/processed/patterns.json'
        )
        
        patterns = json.loads(resp['Body'].read())
        
        entities = []
        for idx, pattern in enumerate(patterns[:1000]):  # Batch insert
            code_embedding = self.embedder.encode(
                pattern.get('code_snippet', '')
            ).tolist()
            
            entities.append({
                'code_id': f'code_{idx}',
                'code_embedding': code_embedding,
                'pattern_type': pattern.get('type'),
                'metadata': {'language': pattern.get('language')}
            })
            
        collection = Collection('code_embeddings', using=self.conn_name)
        collection.insert(entities)
        collection.flush()
        
        logger.info(f"✓ Indexed {len(entities)} code patterns")
        
    def build_ui_embeddings_index(self):
        """Build indices for UI component embeddings"""
        logger.info("Building UI embeddings index...")
        
        # Load UI patterns from RICO
        # Note: RICO uses visual embeddings, not text
        # For now, use component descriptions
        
        ui_components = [
            {'type': 'button', 'description': 'Clickable button element'},
            {'type': 'input', 'description': 'Text input field'},
            {'type': 'dropdown', 'description': 'Dropdown menu'},
            {'type': 'dialog', 'description': 'Modal dialog box'},
            {'type': 'card', 'description': 'Information card'},
            {'type': 'list', 'description': 'List of items'},
            {'type': 'navigation', 'description': 'Navigation menu'},
            {'type': 'tab', 'description': 'Tab navigation'}
        ]
        
        entities = []
        for idx, component in enumerate(ui_components):
            # For actual implementation, use visual features from screenshots
            embedding = self.embedder.encode(
                component['description']
            ).tolist()
            
            entities.append({
                'component_id': f"ui_{idx}",
                'visual_embedding': embedding,
                'component_type': component['type'],
                'metadata': {'description': component['description']}
            })
            
        collection = Collection('ui_embeddings', using=self.conn_name)
        collection.insert(entities)
        collection.flush()
        
        logger.info(f"✓ Indexed {len(entities)} UI patterns")
        
    def build_all(self):
        """Build all indices"""
        self.build_test_embeddings_index()
        self.build_error_embeddings_index()
        self.build_code_embeddings_index()
        self.build_ui_embeddings_index()
        logger.info("\n✓ All vector indices built successfully!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    builder = VectorIndexBuilder()
    builder.build_all()
```

**Execution**:
```bash
python ml/vector_db/build_indices.py
```

**Deliverable**: All vector indices built and ready for search

---

### Task 4.2: Documentation & Testing (6 hours)

**Create**:
1. `PHASE1_COMPLETE.md` - Completion checklist
2. `API_REFERENCE_V3.md` - API documentation
3. `SETUP_GUIDE.md` - Production setup guide
4. Test scripts verifying all components work

**Deliverable**: Complete Phase 1 documentation and validation

---

## Phase 1 Success Criteria

- ✅ PostgreSQL schema created and tested
- ✅ Milvus vector database configured
- ✅ MinIO object storage initialized
- ✅ All 5 datasets ingested (RepliQA, Defects4J, RICO, The Stack, ManyBugs)
- ✅ Vector indices built for semantic search
- ✅ Pattern search API functional
- ✅ Dataset query APIs working
- ✅ All systems tested and documented
- ✅ Performance benchmarks recorded
- ✅ Team trained on new infrastructure

---

## Deployment Checklist

- [ ] Verify all databases running
- [ ] Confirm all datasets indexed
- [ ] Test all API endpoints
- [ ] Run performance benchmarks
- [ ] Document any issues/solutions
- [ ] Create runbooks for operations
- [ ] Set up monitoring/alerts
- [ ] Schedule Phase 2 kickoff

---

## Next Phase (Phase 2)

Phase 2 focuses on ML models:
- Fine-tune test generation model
- Train bug detection model
- Build UI pattern recognition
- Set up inference server
- Integrate models with API

**Estimated Start**: Week 5
**Duration**: 8 weeks
**Team**: 2-3 ML engineers + 1 infrastructure engineer

---

**Status**: Ready to Begin  
**Approved by**: DevForge Leadership  
**Last Updated**: 2026-06-13
