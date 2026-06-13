#!/usr/bin/env python3
"""
Milvus Vector Database Setup for DevForge QA
Initializes vector collections for semantic search and similarity matching
"""

import os
import sys
from typing import List, Dict
import json

try:
    from pymilvus import (
        connections,
        Collection,
        FieldSchema,
        CollectionSchema,
        DataType,
        utility
    )
except ImportError:
    print("❌ pymilvus not installed. Install with: pip install pymilvus")
    sys.exit(1)


class VectorDBSetup:
    """Initialize and configure Milvus for QA system"""

    def __init__(self, host: str = None, port: int = None, db_name: str = 'default'):
        self.host = host or os.getenv('MILVUS_HOST', 'localhost')
        self.port = port or int(os.getenv('MILVUS_PORT', 19530))
        self.db_name = db_name
        self.connection_name = 'devforge'

    def connect(self) -> bool:
        """Connect to Milvus server"""
        try:
            connections.connect(
                alias=self.connection_name,
                host=self.host,
                port=self.port,
                pool_size=30,
                db_name=self.db_name
            )
            print(f"✓ Connected to Milvus at {self.host}:{self.port} (DB: {self.db_name})")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Milvus: {e}")
            return False

    def disconnect(self):
        """Disconnect from Milvus"""
        connections.disconnect(alias=self.connection_name)
        print("✓ Disconnected from Milvus")

    def create_test_embeddings_collection(self) -> bool:
        """Create collection for test case embeddings"""
        try:
            collection_name = "test_embeddings"

            # Check if collection exists
            if utility.has_collection(collection_name, using=self.connection_name):
                print(f"⚠ Collection '{collection_name}' already exists, skipping...")
                return True

            fields = [
                FieldSchema(name="test_id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
                FieldSchema(name="description_embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                FieldSchema(name="code_embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                FieldSchema(name="test_name", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="framework", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]

            schema = CollectionSchema(
                fields=fields,
                description="Test case embeddings for semantic search and similarity detection"
            )

            collection = Collection(
                name=collection_name,
                schema=schema,
                using=self.connection_name
            )

            # Create indices
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 100}
            }

            collection.create_index(
                field_name="description_embedding",
                index_params=index_params,
                index_name="idx_desc"
            )
            collection.create_index(
                field_name="code_embedding",
                index_params=index_params,
                index_name="idx_code"
            )

            collection.load()
            print(f"✓ Created collection: {collection_name}")
            return True

        except Exception as e:
            print(f"❌ Error creating test_embeddings collection: {e}")
            return False

    def create_error_embeddings_collection(self) -> bool:
        """Create collection for error/failure embeddings"""
        try:
            collection_name = "error_embeddings"

            if utility.has_collection(collection_name, using=self.connection_name):
                print(f"⚠ Collection '{collection_name}' already exists, skipping...")
                return True

            fields = [
                FieldSchema(name="failure_id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
                FieldSchema(name="error_embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                FieldSchema(name="error_type", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="severity", dtype=DataType.VARCHAR, max_length=20),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]

            schema = CollectionSchema(
                fields=fields,
                description="Error embeddings for similar failure detection and root cause analysis"
            )

            collection = Collection(
                name=collection_name,
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
                index_params=index_params,
                index_name="idx_error"
            )

            collection.load()
            print(f"✓ Created collection: {collection_name}")
            return True

        except Exception as e:
            print(f"❌ Error creating error_embeddings collection: {e}")
            return False

    def create_code_embeddings_collection(self) -> bool:
        """Create collection for code pattern embeddings"""
        try:
            collection_name = "code_embeddings"

            if utility.has_collection(collection_name, using=self.connection_name):
                print(f"⚠ Collection '{collection_name}' already exists, skipping...")
                return True

            fields = [
                FieldSchema(name="code_id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
                FieldSchema(name="code_embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                FieldSchema(name="pattern_type", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]

            schema = CollectionSchema(
                fields=fields,
                description="Code pattern embeddings from The Stack dataset"
            )

            collection = Collection(
                name=collection_name,
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
                index_params=index_params,
                index_name="idx_code"
            )

            collection.load()
            print(f"✓ Created collection: {collection_name}")
            return True

        except Exception as e:
            print(f"❌ Error creating code_embeddings collection: {e}")
            return False

    def create_ui_embeddings_collection(self) -> bool:
        """Create collection for UI component embeddings"""
        try:
            collection_name = "ui_embeddings"

            if utility.has_collection(collection_name, using=self.connection_name):
                print(f"⚠ Collection '{collection_name}' already exists, skipping...")
                return True

            fields = [
                FieldSchema(name="component_id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
                FieldSchema(name="visual_embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
                FieldSchema(name="component_type", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="accessibility_score", dtype=DataType.FLOAT),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]

            schema = CollectionSchema(
                fields=fields,
                description="UI component embeddings from RICO dataset for visual similarity matching"
            )

            collection = Collection(
                name=collection_name,
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
                index_params=index_params,
                index_name="idx_visual"
            )

            collection.load()
            print(f"✓ Created collection: {collection_name}")
            return True

        except Exception as e:
            print(f"❌ Error creating ui_embeddings collection: {e}")
            return False

    def setup_all(self) -> bool:
        """Initialize all collections"""
        print("\n" + "="*60)
        print("Setting up Milvus Vector Database for DevForge QA")
        print("="*60 + "\n")

        if not self.connect():
            return False

        results = []
        results.append(("Test Embeddings", self.create_test_embeddings_collection()))
        results.append(("Error Embeddings", self.create_error_embeddings_collection()))
        results.append(("Code Embeddings", self.create_code_embeddings_collection()))
        results.append(("UI Embeddings", self.create_ui_embeddings_collection()))

        self.disconnect()

        print("\n" + "="*60)
        print("Setup Summary:")
        print("="*60)
        for name, success in results:
            status = "✓" if success else "✗"
            print(f"{status} {name}")

        all_success = all(result[1] for result in results)
        if all_success:
            print("\n✓ Vector database setup complete!")
        else:
            print("\n⚠ Some setup steps failed. Please check errors above.")

        return all_success


if __name__ == "__main__":
    setup = VectorDBSetup()
    success = setup.setup_all()
    sys.exit(0 if success else 1)
