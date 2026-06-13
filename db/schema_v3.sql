-- Phase 1: QA Suite ML Foundation Database Schema
-- PostgreSQL schema for DevForge QA ML System
-- Supports test generation, bug detection, pattern learning

-- =====================================================
-- ML Models Registry
-- =====================================================
CREATE TABLE IF NOT EXISTS ml_models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  version VARCHAR(50),
  dataset_source VARCHAR(255),
  checkpoint_path VARCHAR(512),
  framework VARCHAR(50) DEFAULT 'pytorch',
  metrics JSONB,
  training_date TIMESTAMP,
  last_used TIMESTAMP,
  enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(name, version)
);

CREATE INDEX IF NOT EXISTS idx_ml_models_type ON ml_models(type);
CREATE INDEX IF NOT EXISTS idx_ml_models_enabled ON ml_models(enabled);

-- =====================================================
-- Learned Patterns Database
-- =====================================================
CREATE TABLE IF NOT EXISTS patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL UNIQUE,
  category VARCHAR(100),
  pattern_text TEXT,
  pattern_regex TEXT,
  confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
  occurrences INT DEFAULT 1,
  severity VARCHAR(20) DEFAULT 'medium',
  suggested_fix TEXT,
  effectiveness DECIMAL(3,2) DEFAULT 0,
  affected_tests TEXT[],
  first_seen TIMESTAMP DEFAULT NOW(),
  last_seen TIMESTAMP DEFAULT NOW(),
  source VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON patterns(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_category ON patterns(category);
CREATE INDEX IF NOT EXISTS idx_patterns_updated ON patterns(updated_at DESC);

-- =====================================================
-- Test Cases (Generated & Manual)
-- =====================================================
CREATE TABLE IF NOT EXISTS test_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  source VARCHAR(50) NOT NULL,
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
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_test_cases_source ON test_cases(source);
CREATE INDEX IF NOT EXISTS idx_test_cases_framework ON test_cases(framework);
CREATE INDEX IF NOT EXISTS idx_test_cases_created ON test_cases(created_at DESC);

-- =====================================================
-- Test Failures (for learning)
-- =====================================================
CREATE TABLE IF NOT EXISTS test_failures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_case_id UUID REFERENCES test_cases(id) ON DELETE CASCADE,
  error_message TEXT,
  error_type VARCHAR(100),
  stack_trace TEXT,
  severity VARCHAR(20) DEFAULT 'medium',
  root_cause_pattern_id UUID REFERENCES patterns(id) ON DELETE SET NULL,
  environment JSONB,
  execution_time INT,
  failed_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_test_failures_test_case ON test_failures(test_case_id);
CREATE INDEX IF NOT EXISTS idx_test_failures_error_type ON test_failures(error_type);
CREATE INDEX IF NOT EXISTS idx_test_failures_failed_at ON test_failures(failed_at DESC);
CREATE INDEX IF NOT EXISTS idx_test_failures_pattern ON test_failures(root_cause_pattern_id);

-- =====================================================
-- Bug Reports
-- =====================================================
CREATE TABLE IF NOT EXISTS bugs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  code_location VARCHAR(512),
  code_snippet TEXT,
  bug_type VARCHAR(100),
  severity VARCHAR(20) DEFAULT 'medium',
  detected_by_model_id UUID REFERENCES ml_models(id),
  suggested_fix TEXT,
  fix_code TEXT,
  fix_validated BOOLEAN DEFAULT false,
  pr_url VARCHAR(512),
  status VARCHAR(50) DEFAULT 'open',
  created_at TIMESTAMP DEFAULT NOW(),
  fixed_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bugs_status ON bugs(status);
CREATE INDEX IF NOT EXISTS idx_bugs_type ON bugs(bug_type);
CREATE INDEX IF NOT EXISTS idx_bugs_created ON bugs(created_at DESC);

-- =====================================================
-- UI Patterns Library
-- =====================================================
CREATE TABLE IF NOT EXISTS ui_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  component_type VARCHAR(100) NOT NULL,
  component_name VARCHAR(255),
  properties JSONB,
  screenshot_url VARCHAR(512),
  optimal_selectors TEXT[] NOT NULL,
  fallback_selectors TEXT[],
  accessibility_level VARCHAR(50),
  frequency INT DEFAULT 1,
  last_used TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ui_patterns_component ON ui_patterns(component_type);

-- =====================================================
-- Generated Artifacts (tests, fixes, selectors)
-- =====================================================
CREATE TABLE IF NOT EXISTS generated_artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  artifact_type VARCHAR(100) NOT NULL,
  content TEXT NOT NULL,
  source_code TEXT,
  model_id UUID REFERENCES ml_models(id),
  execution_status VARCHAR(50),
  execution_result JSONB,
  confidence DECIMAL(3,2),
  user_feedback INT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_artifacts_type ON generated_artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_model ON generated_artifacts(model_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_status ON generated_artifacts(execution_status);

-- =====================================================
-- Learning Sessions
-- =====================================================
CREATE TABLE IF NOT EXISTS learning_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_type VARCHAR(100),
  input_count INT,
  patterns_learned INT DEFAULT 0,
  patterns_updated INT DEFAULT 0,
  duration_ms INT,
  model_updated BOOLEAN DEFAULT false,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_learning_sessions_type ON learning_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_learning_sessions_completed ON learning_sessions(completed_at DESC);

-- =====================================================
-- Dataset Versions
-- =====================================================
CREATE TABLE IF NOT EXISTS dataset_versions (
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
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(dataset_name, version)
);

CREATE INDEX IF NOT EXISTS idx_dataset_versions_name ON dataset_versions(dataset_name);
CREATE INDEX IF NOT EXISTS idx_dataset_versions_created ON dataset_versions(created_at DESC);

-- =====================================================
-- Vector Index Metadata
-- =====================================================
CREATE TABLE IF NOT EXISTS vector_indices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_name VARCHAR(255) NOT NULL,
  index_type VARCHAR(100),
  dimension INT,
  metric_type VARCHAR(50),
  record_count INT DEFAULT 0,
  indexed_at TIMESTAMP,
  last_updated TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(collection_name)
);

CREATE INDEX IF NOT EXISTS idx_vector_indices_collection ON vector_indices(collection_name);

-- =====================================================
-- API Usage & Metrics
-- =====================================================
CREATE TABLE IF NOT EXISTS api_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint VARCHAR(255),
  method VARCHAR(10),
  status_code INT,
  response_time_ms INT,
  model_id UUID REFERENCES ml_models(id),
  user_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_created ON api_usage(created_at DESC);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO postgres;
