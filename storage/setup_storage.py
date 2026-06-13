#!/usr/bin/env python3
"""
MinIO/S3 Object Storage Setup for DevForge QA
Sets up storage for datasets, models, and artifacts
"""

import os
import sys
from typing import List, Dict

try:
    import boto3
    from botocore.client import Config
except ImportError:
    print("❌ boto3 not installed. Install with: pip install boto3")
    sys.exit(1)


class StorageSetup:
    """Initialize object storage for QA system"""

    def __init__(self):
        self.endpoint_url = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
        self.access_key = os.getenv('S3_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('S3_SECRET_KEY', 'minioadmin')

        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version='s3v4')
            )
            print(f"✓ Connected to S3 storage at {self.endpoint_url}")
        except Exception as e:
            print(f"❌ Failed to connect to S3: {e}")
            raise

    def create_buckets(self) -> Dict[str, bool]:
        """Create required S3 buckets"""
        buckets = [
            'devforge-datasets',
            'devforge-models',
            'devforge-artifacts',
            'devforge-reports'
        ]

        results = {}
        for bucket in buckets:
            try:
                self.s3_client.head_bucket(Bucket=bucket)
                print(f"⚠ Bucket '{bucket}' already exists")
                results[bucket] = True
            except self.s3_client.exceptions.NoSuchBucket:
                try:
                    self.s3_client.create_bucket(Bucket=bucket)
                    print(f"✓ Created bucket '{bucket}'")
                    results[bucket] = True
                except Exception as e:
                    print(f"❌ Failed to create bucket '{bucket}': {e}")
                    results[bucket] = False
            except Exception as e:
                print(f"❌ Error checking bucket '{bucket}': {e}")
                results[bucket] = False

        return results

    def setup_dataset_structure(self) -> bool:
        """Create directory structure for datasets"""
        datasets = ['repliqa', 'defects4j', 'rico', 'the_stack', 'manybugs']

        try:
            for dataset in datasets:
                paths = [
                    f'datasets/{dataset}/raw/',
                    f'datasets/{dataset}/processed/',
                    f'datasets/{dataset}/embeddings/',
                    f'datasets/{dataset}/metadata/',
                    f'datasets/{dataset}/splits/'
                ]

                for path in paths:
                    self.s3_client.put_object(
                        Bucket='devforge-datasets',
                        Key=path + '.gitkeep',
                        Body=b''
                    )
                    print(f"✓ Created path: {path}")

            return True
        except Exception as e:
            print(f"❌ Error setting up dataset structure: {e}")
            return False

    def setup_model_structure(self) -> bool:
        """Create directory structure for ML models"""
        models = [
            'test_generator',
            'bug_detector',
            'ui_recognizer',
            'code_analyzer',
            'fix_suggester'
        ]

        try:
            for model in models:
                paths = [
                    f'models/{model}/checkpoints/',
                    f'models/{model}/configs/',
                    f'models/{model}/metrics/',
                    f'models/{model}/inference/',
                    f'models/{model}/training_logs/'
                ]

                for path in paths:
                    self.s3_client.put_object(
                        Bucket='devforge-models',
                        Key=path + '.gitkeep',
                        Body=b''
                    )
                    print(f"✓ Created path: {path}")

            return True
        except Exception as e:
            print(f"❌ Error setting up model structure: {e}")
            return False

    def setup_artifacts_structure(self) -> bool:
        """Create directory structure for generated artifacts"""
        artifact_types = [
            'tests',
            'fixes',
            'selectors',
            'reports'
        ]

        try:
            for artifact_type in artifact_types:
                paths = [
                    f'artifacts/{artifact_type}/generated/',
                    f'artifacts/{artifact_type}/executed/',
                    f'artifacts/{artifact_type}/validated/'
                ]

                for path in paths:
                    self.s3_client.put_object(
                        Bucket='devforge-artifacts',
                        Key=path + '.gitkeep',
                        Body=b''
                    )
                    print(f"✓ Created path: {path}")

            return True
        except Exception as e:
            print(f"❌ Error setting up artifacts structure: {e}")
            return False

    def setup_reports_structure(self) -> bool:
        """Create directory structure for test reports"""
        report_types = [
            'learning_sessions',
            'pattern_analysis',
            'model_metrics',
            'test_results',
            'bug_reports'
        ]

        try:
            for report_type in report_types:
                path = f'reports/{report_type}/'
                self.s3_client.put_object(
                    Bucket='devforge-reports',
                    Key=path + '.gitkeep',
                    Body=b''
                )
                print(f"✓ Created path: {path}")

            return True
        except Exception as e:
            print(f"❌ Error setting up reports structure: {e}")
            return False

    def setup_all(self) -> bool:
        """Initialize all storage"""
        print("\n" + "="*60)
        print("Setting up S3 Object Storage for DevForge QA")
        print("="*60 + "\n")

        # Create buckets
        print("Creating buckets...")
        bucket_results = self.create_buckets()
        all_buckets_ok = all(bucket_results.values())

        if not all_buckets_ok:
            print("\n⚠ Some buckets failed to create")
            return False

        # Setup directory structures
        print("\nSetting up dataset structure...")
        dataset_ok = self.setup_dataset_structure()

        print("\nSetting up model structure...")
        models_ok = self.setup_model_structure()

        print("\nSetting up artifacts structure...")
        artifacts_ok = self.setup_artifacts_structure()

        print("\nSetting up reports structure...")
        reports_ok = self.setup_reports_structure()

        print("\n" + "="*60)
        print("Storage Setup Summary:")
        print("="*60)
        print(f"{'Buckets':<30} {'✓' if all_buckets_ok else '✗'}")
        print(f"{'Dataset Structure':<30} {'✓' if dataset_ok else '✗'}")
        print(f"{'Model Structure':<30} {'✓' if models_ok else '✗'}")
        print(f"{'Artifacts Structure':<30} {'✓' if artifacts_ok else '✗'}")
        print(f"{'Reports Structure':<30} {'✓' if reports_ok else '✗'}")

        all_ok = all_buckets_ok and dataset_ok and models_ok and artifacts_ok and reports_ok
        if all_ok:
            print("\n✓ Storage setup complete!")
        else:
            print("\n⚠ Some setup steps failed. Please check errors above.")

        return all_ok


if __name__ == "__main__":
    setup = StorageSetup()
    success = setup.setup_all()
    sys.exit(0 if success else 1)
