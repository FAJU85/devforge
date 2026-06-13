#!/usr/bin/env python3
"""
Phase 1: Python Clients for Database, Vector DB, and Storage
Unified interface for accessing all backend services
"""

import os
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from pymilvus import connections, Collection
import boto3
from botocore.client import Config


class PostgresClient:
    """PostgreSQL connection and query helper"""

    def __init__(self, host: str = None, port: int = None, db: str = None,
                 user: str = None, password: str = None):
        self.host = host or os.getenv('POSTGRES_HOST', 'localhost')
        self.port = port or int(os.getenv('POSTGRES_PORT', 5432))
        self.db = db or os.getenv('POSTGRES_DB', 'devforge')
        self.user = user or os.getenv('POSTGRES_USER', 'postgres')
        self.password = password or os.getenv('POSTGRES_PASSWORD', 'postgres')
        self.conn = None

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.db,
                user=self.user,
                password=self.password
            )
            print(f"✓ Connected to PostgreSQL")
            return True
        except Exception as e:
            print(f"✗ PostgreSQL connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Disconnected from PostgreSQL")

    def execute(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            self.conn.commit()
            return results
        except Exception as e:
            print(f"✗ Query error: {e}")
            self.conn.rollback()
            return []

    def insert_test_case(self, name: str, code: str, framework: str = 'playwright',
                        source: str = 'generated') -> Optional[str]:
        """Insert a test case"""
        query = """
            INSERT INTO test_cases (name, code, framework, source, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id
        """
        results = self.execute(query, (name, code, framework, source))
        return results[0]['id'] if results else None

    def get_patterns(self, category: str = None, min_confidence: float = 0.6) -> List[Dict]:
        """Get learned patterns"""
        query = "SELECT * FROM patterns WHERE confidence >= %s"
        params = [min_confidence]

        if category:
            query += " AND category = %s"
            params.append(category)

        query += " ORDER BY confidence DESC"
        return self.execute(query, tuple(params))

    def insert_failure(self, test_id: str, error_message: str, error_type: str,
                      stack_trace: str = None, severity: str = 'medium') -> Optional[str]:
        """Insert test failure"""
        query = """
            INSERT INTO test_failures
            (test_case_id, error_message, error_type, stack_trace, severity, failed_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING id
        """
        results = self.execute(query, (test_id, error_message, error_type, stack_trace, severity))
        return results[0]['id'] if results else None

    def get_bugs(self, status: str = 'open') -> List[Dict]:
        """Get reported bugs"""
        query = "SELECT * FROM bugs WHERE status = %s ORDER BY created_at DESC"
        return self.execute(query, (status,))

    def insert_bug(self, title: str, description: str, bug_type: str,
                  code_snippet: str = None, severity: str = 'medium') -> Optional[str]:
        """Insert a bug report"""
        query = """
            INSERT INTO bugs (title, description, code_snippet, bug_type, severity, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING id
        """
        results = self.execute(query, (title, description, code_snippet, bug_type, severity))
        return results[0]['id'] if results else None


class VectorDBClient:
    """Milvus vector database client"""

    def __init__(self, host: str = None, port: int = None, db: str = None):
        self.host = host or os.getenv('MILVUS_HOST', 'localhost')
        self.port = port or int(os.getenv('MILVUS_PORT', 19530))
        self.db = db or os.getenv('MILVUS_DB', 'default')
        self.alias = 'devforge_client'

    def connect(self) -> bool:
        """Connect to Milvus"""
        try:
            connections.connect(
                alias=self.alias,
                host=self.host,
                port=self.port,
                db_name=self.db
            )
            print(f"✓ Connected to Milvus")
            return True
        except Exception as e:
            print(f"✗ Milvus connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from Milvus"""
        connections.disconnect(alias=self.alias)
        print("✓ Disconnected from Milvus")

    def insert_test_embeddings(self, test_ids: List[str], descriptions: List[List[float]],
                              codes: List[List[float]], test_names: List[str],
                              frameworks: List[str]) -> bool:
        """Insert test case embeddings"""
        try:
            collection = Collection('test_embeddings', using=self.alias)

            data = [
                test_ids,
                descriptions,
                codes,
                test_names,
                frameworks,
                [{"index": i} for i in range(len(test_ids))]
            ]

            collection.insert(data)
            collection.flush()
            print(f"✓ Inserted {len(test_ids)} test embeddings")
            return True
        except Exception as e:
            print(f"✗ Insert failed: {e}")
            return False

    def search_similar_tests(self, embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Search for similar test cases"""
        try:
            collection = Collection('test_embeddings', using=self.alias)
            results = collection.search(
                [embedding],
                'description_embedding',
                {'nprobe': 10},
                limit=top_k,
                output_fields=['test_id', 'test_name', 'framework']
            )

            output = []
            for hits in results:
                for hit in hits:
                    output.append({
                        'test_id': hit.entity.get('test_id'),
                        'test_name': hit.entity.get('test_name'),
                        'framework': hit.entity.get('framework'),
                        'distance': hit.distance
                    })
            return output
        except Exception as e:
            print(f"✗ Search failed: {e}")
            return []

    def insert_error_embeddings(self, failure_ids: List[str], embeddings: List[List[float]],
                               error_types: List[str], severities: List[str]) -> bool:
        """Insert error embeddings"""
        try:
            collection = Collection('error_embeddings', using=self.alias)

            data = [
                failure_ids,
                embeddings,
                error_types,
                severities,
                [{"index": i} for i in range(len(failure_ids))]
            ]

            collection.insert(data)
            collection.flush()
            print(f"✓ Inserted {len(failure_ids)} error embeddings")
            return True
        except Exception as e:
            print(f"✗ Insert failed: {e}")
            return False

    def search_similar_errors(self, embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Find similar error patterns"""
        try:
            collection = Collection('error_embeddings', using=self.alias)
            results = collection.search(
                [embedding],
                'error_embedding',
                {'nprobe': 10},
                limit=top_k,
                output_fields=['failure_id', 'error_type', 'severity']
            )

            output = []
            for hits in results:
                for hit in hits:
                    output.append({
                        'failure_id': hit.entity.get('failure_id'),
                        'error_type': hit.entity.get('error_type'),
                        'severity': hit.entity.get('severity'),
                        'distance': hit.distance
                    })
            return output
        except Exception as e:
            print(f"✗ Search failed: {e}")
            return []


class StorageClient:
    """S3/MinIO object storage client"""

    def __init__(self, endpoint: str = None, access_key: str = None,
                 secret_key: str = None, bucket: str = 'devforge-datasets'):
        self.endpoint = endpoint or os.getenv('S3_DATASETS_ENDPOINT', 'http://localhost:9000')
        self.access_key = access_key or os.getenv('S3_DATASETS_ACCESS_KEY', 'minioadmin')
        self.secret_key = secret_key or os.getenv('S3_DATASETS_SECRET_KEY', 'minioadmin')
        self.bucket = bucket

        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version='s3v4')
            )
            print(f"✓ Connected to S3 storage")
        except Exception as e:
            print(f"✗ S3 connection failed: {e}")
            self.client = None

    def upload_file(self, local_path: str, s3_path: str) -> bool:
        """Upload file to S3"""
        try:
            self.client.upload_file(local_path, self.bucket, s3_path)
            print(f"✓ Uploaded {s3_path}")
            return True
        except Exception as e:
            print(f"✗ Upload failed: {e}")
            return False

    def download_file(self, s3_path: str, local_path: str) -> bool:
        """Download file from S3"""
        try:
            self.client.download_file(self.bucket, s3_path, local_path)
            print(f"✓ Downloaded {s3_path}")
            return True
        except Exception as e:
            print(f"✗ Download failed: {e}")
            return False

    def list_objects(self, prefix: str = '') -> List[str]:
        """List objects in bucket"""
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            print(f"✗ List failed: {e}")
            return []

    def upload_json(self, data: Dict, s3_path: str) -> bool:
        """Upload JSON object"""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_path,
                Body=json.dumps(data, indent=2),
                ContentType='application/json'
            )
            print(f"✓ Uploaded JSON {s3_path}")
            return True
        except Exception as e:
            print(f"✗ Upload failed: {e}")
            return False

    def download_json(self, s3_path: str) -> Optional[Dict]:
        """Download and parse JSON object"""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=s3_path)
            data = json.loads(response['Body'].read().decode('utf-8'))
            print(f"✓ Downloaded JSON {s3_path}")
            return data
        except Exception as e:
            print(f"✗ Download failed: {e}")
            return None


class DevForgeClient:
    """Unified client for all DevForge services"""

    def __init__(self):
        self.postgres = PostgresClient()
        self.vector_db = VectorDBClient()
        self.storage = StorageClient()

    def connect_all(self) -> bool:
        """Connect to all services"""
        results = [
            self.postgres.connect(),
            self.vector_db.connect(),
        ]
        return all(results)

    def disconnect_all(self):
        """Disconnect from all services"""
        self.postgres.disconnect()
        self.vector_db.disconnect()

    def health_check(self) -> Dict[str, bool]:
        """Check health of all services"""
        return {
            'postgres': self.postgres.conn is not None,
            'milvus': self.vector_db.alias in connections._conn_pool.connections,
            'storage': self.storage.client is not None
        }


# Example usage
if __name__ == '__main__':
    # Initialize client
    client = DevForgeClient()

    # Connect to all services
    if not client.connect_all():
        print("Connection failed")
        exit(1)

    # Check health
    health = client.health_check()
    print("\nService Health:")
    for service, status in health.items():
        symbol = "✓" if status else "✗"
        print(f"  {symbol} {service}")

    # Get patterns
    print("\nLearned Patterns:")
    patterns = client.postgres.get_patterns()
    for pattern in patterns[:5]:
        print(f"  - {pattern['name']} (confidence: {pattern['confidence']})")

    # Disconnect
    client.disconnect_all()
