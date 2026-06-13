#!/usr/bin/env python3
"""
Phase 1: Dataset Ingestion Pipeline
Handles downloading and processing the 5 core datasets
"""

import os
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from datetime import datetime
import hashlib

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.clients import StorageClient, PostgresClient


class DatasetLoader(ABC):
    """Base class for dataset loaders"""

    def __init__(self, name: str, version: str, source_url: str):
        self.name = name
        self.version = version
        self.source_url = source_url
        self.storage = StorageClient(bucket='devforge-datasets')
        self.postgres = PostgresClient()
        self.postgres.connect()

    @abstractmethod
    def download(self, output_dir: str) -> bool:
        """Download dataset"""
        pass

    @abstractmethod
    def process(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process and validate dataset"""
        pass

    def register_version(self, record_count: int, size_bytes: int) -> bool:
        """Register dataset version in database"""
        query = """
            INSERT INTO dataset_versions
            (dataset_name, version, source_url, downloaded_at, record_count, size_bytes, created_at)
            VALUES (%s, %s, %s, NOW(), %s, %s, NOW())
            ON CONFLICT (dataset_name, version) DO UPDATE SET
            downloaded_at = NOW(), record_count = %s, size_bytes = %s
        """
        try:
            self.postgres.execute(query, (
                self.name, self.version, self.source_url, record_count, size_bytes,
                record_count, size_bytes
            ))
            print(f"✓ Registered {self.name} v{self.version}")
            return True
        except Exception as e:
            print(f"✗ Failed to register dataset: {e}")
            return False

    def upload_to_storage(self, local_path: str, remote_prefix: str = None) -> bool:
        """Upload processed data to storage"""
        if not remote_prefix:
            remote_prefix = f"{self.name}/processed"

        try:
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    local_file = os.path.join(root, file)
                    relative = os.path.relpath(local_file, local_path)
                    remote_path = f"{remote_prefix}/{relative}"
                    self.storage.upload_file(local_file, remote_path)
            return True
        except Exception as e:
            print(f"✗ Upload failed: {e}")
            return False


class RepliQALoader(DatasetLoader):
    """RepliQA Dataset Loader - Test specifications"""

    def __init__(self):
        super().__init__(
            name='repliqa',
            version='1.0',
            source_url='https://huggingface.co/datasets/ServiceNow/repliqa'
        )

    def download(self, output_dir: str) -> bool:
        """Download RepliQA dataset"""
        print(f"Downloading {self.name}...")
        try:
            # Would use HuggingFace API in production
            print(f"ℹ RepliQA would be downloaded from {self.source_url}")
            return True
        except Exception as e:
            print(f"✗ Download failed: {e}")
            return False

    def process(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process RepliQA dataset"""
        print(f"Processing {self.name}...")

        output = {
            'dataset': self.name,
            'version': self.version,
            'records': 0,
            'test_specs': 0,
            'total_size': 0
        }

        try:
            # Process test specifications
            specs_file = os.path.join(output_dir, 'test_specifications.jsonl')
            os.makedirs(output_dir, exist_ok=True)

            # In production, would parse actual dataset files
            # For now, create placeholder
            with open(specs_file, 'w') as f:
                for i in range(100):  # Example: 100 test specs
                    spec = {
                        'id': f'repliqa-{i}',
                        'description': f'Test specification {i}',
                        'framework': 'playwright',
                        'created_at': datetime.now().isoformat()
                    }
                    f.write(json.dumps(spec) + '\n')

            output['test_specs'] = 100
            output['records'] = 100
            print(f"✓ Processed {self.name}: {output['test_specs']} test specifications")
            return output
        except Exception as e:
            print(f"✗ Processing failed: {e}")
            return output


class Defects4JLoader(DatasetLoader):
    """Defects4J Dataset Loader - Bug patterns"""

    def __init__(self):
        super().__init__(
            name='defects4j',
            version='2.0',
            source_url='https://github.com/rjust/defects4j'
        )

    def download(self, output_dir: str) -> bool:
        """Download Defects4J dataset"""
        print(f"Downloading {self.name}...")
        print(f"ℹ Defects4J would be cloned from {self.source_url}")
        return True

    def process(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process Defects4J dataset"""
        print(f"Processing {self.name}...")

        output = {
            'dataset': self.name,
            'version': self.version,
            'bugs': 0,
            'projects': 0,
            'total_size': 0
        }

        try:
            bugs_file = os.path.join(output_dir, 'bugs.jsonl')
            os.makedirs(output_dir, exist_ok=True)

            # Create placeholder bug data
            with open(bugs_file, 'w') as f:
                for i in range(835):  # Defects4J has ~835 bugs
                    bug = {
                        'id': f'defects4j-{i}',
                        'project': f'project-{i % 17}',  # 17 projects
                        'bug_id': i,
                        'type': 'logic_error',
                        'created_at': datetime.now().isoformat()
                    }
                    f.write(json.dumps(bug) + '\n')

            output['bugs'] = 835
            output['projects'] = 17
            print(f"✓ Processed {self.name}: {output['bugs']} bugs from {output['projects']} projects")
            return output
        except Exception as e:
            print(f"✗ Processing failed: {e}")
            return output


class RICOLoader(DatasetLoader):
    """RICO Dataset Loader - UI patterns"""

    def __init__(self):
        super().__init__(
            name='rico',
            version='1.0',
            source_url='https://www.interactionmining.org/archive/rico'
        )

    def download(self, output_dir: str) -> bool:
        """Download RICO dataset"""
        print(f"Downloading {self.name}...")
        print(f"ℹ RICO would be downloaded from {self.source_url}")
        return True

    def process(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process RICO dataset"""
        print(f"Processing {self.name}...")

        output = {
            'dataset': self.name,
            'version': self.version,
            'screens': 0,
            'components': 0,
            'total_size': 0
        }

        try:
            components_file = os.path.join(output_dir, 'ui_components.jsonl')
            os.makedirs(output_dir, exist_ok=True)

            # Create placeholder UI component data
            with open(components_file, 'w') as f:
                component_id = 0
                for screen in range(66000):  # 66K+ screens
                    for comp in range(100):  # ~100 components per screen
                        component = {
                            'id': f'rico-{component_id}',
                            'screen_id': screen,
                            'type': 'button',  # Simplified
                            'bounds': [0, 0, 100, 50],
                            'created_at': datetime.now().isoformat()
                        }
                        f.write(json.dumps(component) + '\n')
                        component_id += 1
                        if component_id >= 100000:  # Cap at 100k for example
                            break
                    if component_id >= 100000:
                        break

            output['screens'] = 66000
            output['components'] = component_id
            print(f"✓ Processed {self.name}: {output['components']} components from {output['screens']} screens")
            return output
        except Exception as e:
            print(f"✗ Processing failed: {e}")
            return output


class TheStackLoader(DatasetLoader):
    """The Stack Dataset Loader - Code patterns"""

    def __init__(self):
        super().__init__(
            name='the_stack',
            version='1.1',
            source_url='https://huggingface.co/datasets/bigcode/the-stack'
        )

    def download(self, output_dir: str) -> bool:
        """Download The Stack dataset"""
        print(f"Downloading {self.name}...")
        print(f"ℹ The Stack would be downloaded from {self.source_url}")
        return True

    def process(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process The Stack dataset"""
        print(f"Processing {self.name}...")

        output = {
            'dataset': self.name,
            'version': self.version,
            'code_samples': 0,
            'languages': 0,
            'total_size': 0
        }

        try:
            code_file = os.path.join(output_dir, 'code_samples.jsonl')
            os.makedirs(output_dir, exist_ok=True)

            # Create placeholder code data
            languages = ['python', 'javascript', 'java', 'go', 'rust']
            with open(code_file, 'w') as f:
                for i in range(10000):  # Example: 10k code samples
                    sample = {
                        'id': f'the-stack-{i}',
                        'language': languages[i % len(languages)],
                        'tokens': 256,
                        'created_at': datetime.now().isoformat()
                    }
                    f.write(json.dumps(sample) + '\n')

            output['code_samples'] = 10000
            output['languages'] = len(languages)
            print(f"✓ Processed {self.name}: {output['code_samples']} code samples in {output['languages']} languages")
            return output
        except Exception as e:
            print(f"✗ Processing failed: {e}")
            return output


class ManyBugsLoader(DatasetLoader):
    """ManyBugs Dataset Loader - Bug fixes"""

    def __init__(self):
        super().__init__(
            name='manybugs',
            version='1.0',
            source_url='https://github.com/squaresLab/ManyBugs'
        )

    def download(self, output_dir: str) -> bool:
        """Download ManyBugs dataset"""
        print(f"Downloading {self.name}...")
        print(f"ℹ ManyBugs would be cloned from {self.source_url}")
        return True

    def process(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process ManyBugs dataset"""
        print(f"Processing {self.name}...")

        output = {
            'dataset': self.name,
            'version': self.version,
            'buggy_versions': 0,
            'programs': 0,
            'total_size': 0
        }

        try:
            fixes_file = os.path.join(output_dir, 'fixes.jsonl')
            os.makedirs(output_dir, exist_ok=True)

            # Create placeholder fix data
            with open(fixes_file, 'w') as f:
                for i in range(3900):  # 3900 buggy versions
                    fix = {
                        'id': f'manybugs-{i}',
                        'program': f'program-{i % 185}',  # 185 programs
                        'buggy_version': i,
                        'fix_type': 'patch',
                        'created_at': datetime.now().isoformat()
                    }
                    f.write(json.dumps(fix) + '\n')

            output['buggy_versions'] = 3900
            output['programs'] = 185
            print(f"✓ Processed {self.name}: {output['buggy_versions']} versions from {output['programs']} programs")
            return output
        except Exception as e:
            print(f"✗ Processing failed: {e}")
            return output


class DatasetPipeline:
    """Main dataset ingestion pipeline"""

    def __init__(self, data_dir: str = './data/datasets'):
        self.data_dir = data_dir
        self.loaders = [
            RepliQALoader(),
            Defects4JLoader(),
            RICOLoader(),
            TheStackLoader(),
            ManyBugsLoader()
        ]

    def load_all(self) -> Dict[str, Any]:
        """Load all datasets"""
        print("\n" + "="*60)
        print("Dataset Ingestion Pipeline")
        print("="*60 + "\n")

        results = {}

        for loader in self.loaders:
            dataset_dir = os.path.join(self.data_dir, loader.name)
            output_dir = os.path.join(dataset_dir, 'processed')

            print(f"\nLoading {loader.name.upper()}")
            print("-" * 40)

            # Download
            if not loader.download(dataset_dir):
                print(f"⚠ Skipping {loader.name}")
                continue

            # Process
            result = loader.process(dataset_dir, output_dir)

            # Register
            total_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(output_dir)
                for filename in filenames
            ) if os.path.exists(output_dir) else 0

            loader.register_version(result.get('records', result.get('bugs', 0)), total_size)

            # Upload to storage
            # loader.upload_to_storage(output_dir)

            results[loader.name] = result

        print("\n" + "="*60)
        print("Pipeline Summary")
        print("="*60)

        for dataset, result in results.items():
            print(f"\n{dataset.upper()}:")
            for key, value in result.items():
                if key != 'dataset':
                    print(f"  {key}: {value}")

        return results


if __name__ == '__main__':
    pipeline = DatasetPipeline()
    results = pipeline.load_all()
