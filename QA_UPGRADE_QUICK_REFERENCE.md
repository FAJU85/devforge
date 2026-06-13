# DevForge QA Upgrade - Quick Reference Guide

## Overview

DevForge is upgrading its QA suite from a basic test automation system to a sophisticated, ML-powered platform.

**Current State**: 
- Phase 1, 2, 4 implemented (Test generation, self-healing, test data)
- 44 unit tests covering basic scenarios
- Learning system for failure patterns

**Upgrade Target**:
- Integrate 5 major datasets (RepliQA, Defects4J, RICO, The Stack, ManyBugs)
- Deploy 5 ML models (test generation, bug detection, UI recognition, code analysis, fix suggestion)
- Self-healing tests with intelligent recovery
- Autonomous bug detection and fixing
- Continuous learning from failures
- UI-aware and code-aware testing

---

## Key Concepts

### **Datasets**

| Dataset | Size | Purpose | Integration |
|---------|------|---------|-------------|
| **RepliQA** | 10K specs | Test generation patterns | → Test Generator Model |
| **Defects4J** | 835 bugs | Bug detection & fixing | → Bug Detector Model |
| **RICO** | 66K+ screens | UI pattern recognition | → UI Recognizer Model |
| **The Stack** | 3.1B tokens | Code patterns & best practices | → Code Analyzer Model |
| **ManyBugs** | 3,900 versions | Debugging strategies | → Fix Suggester Model |

### **ML Models**

| Model | Input | Output | Training Data |
|-------|-------|--------|----------------|
| **Test Generator** | Test description + context | Playwright test code | RepliQA |
| **Bug Detector** | Code + test results | Bug type + location | Defects4J |
| **UI Recognizer** | Screenshot or DOM | UI components + properties | RICO |
| **Code Analyzer** | Code snippet | Pattern type + risk level | The Stack |
| **Fix Suggester** | Buggy code + error | Fixed code + explanation | ManyBugs |

### **System Components**

1. **Test Generation Engine** - Creates tests from descriptions
2. **Self-Healing Engine** - Adapts to UI changes automatically
3. **Bug Detection & Fix Engine** - Finds and fixes bugs autonomously
4. **Pattern Learning Engine** - Learns from failures continuously
5. **ML Model Server** - Runs inference for all models
6. **Data Pipeline** - Ingests and processes datasets
7. **Vector Database** - Semantic search across all data
8. **Knowledge Graphs** - Structured pattern storage

---

## Implementation Timeline

### **Phase 1: Foundation (Weeks 1-4)** - STARTING NOW
- PostgreSQL schema setup
- Vector database (Milvus) setup
- Object storage (S3/MinIO) setup
- Ingest all 5 datasets
- Build vector indices

**Deliverable**: Ready for ML model training

### **Phase 2: ML Models (Weeks 5-12)**
- Train test generation model
- Train bug detection model
- Train UI recognition model
- Train code analyzer model
- Train fix suggester model

**Deliverable**: All 5 models deployed and serving

### **Phase 3: Integration (Weeks 13-20)**
- Connect to Playwright
- Build unified API v3
- Create CLI commands
- Build web dashboard
- CI/CD integration

**Deliverable**: Fully integrated QA system

### **Phase 4: Learning (Weeks 21-26)**
- Failure collection system
- Pattern learning engine
- Confidence scoring
- Model retraining pipeline

**Deliverable**: Autonomous learning loop active

### **Phase 5: Advanced Features (Weeks 27+)**
- Predictive alerts
- Flakiness detection
- Visual regression testing
- Semantic code analysis
- Debugging agent

---

## Quick Start Guide

### For Phase 1 (Foundation)

1. **Database Setup**
   ```bash
   # PostgreSQL
   psql devforge < db/schema_v3.sql
   
   # Milvus (Docker)
   docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest
   
   # MinIO (Docker)
   docker run -d --name minio -p 9000:9000 minio/minio server /data
   ```

2. **Install Dependencies**
   ```bash
   pip install pymilvus boto3 sentence-transformers datasets
   ```

3. **Ingest Datasets**
   ```bash
   python data_pipeline/ingest_repliqa.py
   python data_pipeline/ingest_defects4j.py
   python data_pipeline/ingest_rico.py
   python data_pipeline/ingest_the_stack.py
   python data_pipeline/ingest_manybugs.py
   ```

4. **Build Vector Indices**
   ```bash
   python ml/vector_db/build_indices.py
   ```

5. **Test API**
   ```bash
   # Search patterns
   curl "http://localhost:8000/api/v3/patterns/search?query=timeout&limit=10"
   
   # Semantic search
   curl "http://localhost:8000/api/v3/patterns/semantic-search?query=selector+not+found"
   
   # Dataset stats
   curl "http://localhost:8000/api/v3/datasets/stats"
   ```

---

## API Endpoints (v3)

### **Test Generation**
```
POST /api/v3/qa/generate
POST /api/v3/qa/generate/batch
GET /api/v3/qa/templates
```

### **Test Healing**
```
POST /api/v3/qa/heal
POST /api/v3/qa/heal/locators
GET /api/v3/qa/heal/effectiveness
```

### **Pattern Analysis**
```
GET /api/v3/patterns
GET /api/v3/patterns/{id}
POST /api/v3/patterns/match
POST /api/v3/patterns/learn
```

### **Bug Detection**
```
POST /api/v3/bugs/detect
POST /api/v3/bugs/fix
GET /api/v3/bugs/categories
```

### **UI Patterns**
```
POST /api/v3/ui-patterns/detect
POST /api/v3/ui-patterns/selector-gen
GET /api/v3/ui-patterns/library
```

### **Datasets**
```
GET /api/v3/datasets/repliqa
GET /api/v3/datasets/defects4j
GET /api/v3/datasets/rico
GET /api/v3/datasets/the-stack
GET /api/v3/datasets/manybugs
GET /api/v3/datasets/stats
```

---

## CLI Commands (Future)

```bash
# Test Generation
npm run qa:generate --description "user login flow"

# Test Healing
npm run qa:heal --test tests/failing.spec.ts

# Pattern Learning
npm run qa:learn
npm run qa:patterns

# Bug Detection
npm run qa:detect-bugs --dir src/

# UI Pattern Recognition
npm run qa:ui-patterns --screenshot screenshots/

# System Management
npm run qa:status
npm run qa:sync-datasets
npm run qa:train-models
```

---

## Database Schema Overview

### Core Tables

**ml_models**
- Tracks all ML models (versions, metrics, checkpoints)

**patterns**
- Stores learned patterns with confidence scores
- Used for code scanning and suggestions

**test_cases**
- All test cases (generated and manual)
- Tracks pass rate, flakiness, coverage

**test_failures**
- Historical failures for learning
- Links to root cause patterns

**bugs**
- Bug reports from detection engine
- Tracks fixes and PRs

**ui_patterns**
- UI component library
- Selectors and fallbacks

**generated_artifacts**
- Generated tests, fixes, selectors
- Tracks user feedback

**learning_sessions**
- Logs of learning operations
- Tracks improvements over time

---

## Vector Database Collections

**test_embeddings**
- Test descriptions and code vectors
- Semantic search for similar tests

**error_embeddings**
- Error message vectors
- Find similar failures

**code_embeddings**
- Code snippet vectors
- Find similar code patterns

**ui_embeddings**
- UI component vectors
- Find similar UI elements

---

## Storage Structure (S3/MinIO)

```
devforge-datasets/
├── repliqa/           # Test patterns
├── defects4j/         # Bug patterns
├── rico/              # UI components
├── the_stack/         # Code patterns
└── manybugs/          # Debug strategies

devforge-models/
├── test_generator/    # Checkpoints + config
├── bug_detector/
├── ui_recognizer/
├── code_analyzer/
└── fix_suggester/

devforge-artifacts/
├── generated_tests/
├── bug_reports/
└── failure_logs/
```

---

## Key Files & Locations

### Architecture & Planning
- `COMPREHENSIVE_QA_UPGRADE_PLAN.md` - Complete architecture
- `PHASE1_IMPLEMENTATION_GUIDE.md` - Week-by-week Phase 1 plan
- `QA_UPGRADE_QUICK_REFERENCE.md` - This file

### Existing Implementation
- `SELF_EVOLVING_QA.md` - Current test generation & self-healing
- `QA_LEARNING_SYSTEM.md` - Pattern learning system
- `IMPLEMENTATION_SUMMARY.md` - MVP completion status

### Code Directories
- `/qa/learning/` - Pattern learning engine (operational)
- `/autonomous/` - Auto-fix system
- `/control_plane/` - Orchestration
- `/scripts/` - Utilities (analyze-failures, dashboard)
- `/tests/generators/` - Test generation (operational)

### Configuration
- `.mcp.json` - MCP settings
- `api_v2.py` - Current API v2
- `alembic/` - Database migrations

---

## Success Metrics

### Phase 1
- ✅ All 5 datasets ingested and indexed
- ✅ Vector search <500ms per query
- ✅ API endpoints functional

### Phase 2
- ✅ Test generation >90% accuracy
- ✅ Bug detection F1 >0.85
- ✅ UI recognition >90% accuracy
- ✅ Code analysis >85% precision
- ✅ Fix suggestion >80% pass rate

### Phase 3
- ✅ 40+ API endpoints working
- ✅ 20+ CLI commands available
- ✅ Web dashboard operational
- ✅ CI/CD integration active

### Phase 4
- ✅ Automatic failure collection
- ✅ 10+ patterns learned
- ✅ Confidence improving over time
- ✅ Feedback loop operational

### Phase 5+
- ✅ Predictive alerts 70%+ accurate
- ✅ Flakiness detection active
- ✅ Visual regression testing
- ✅ Semantic code analysis
- ✅ Debugging agent MVP

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Model quality | Use curated subsets, validate carefully |
| False positives | High confidence thresholds, human review |
| Integration complexity | Phased approach, good abstractions |
| Dataset licensing | Use open datasets, verify licenses |
| Performance | Implement caching, batch processing |

---

## Team Structure

### Phase 1 (Weeks 1-4)
- **2-3 Backend Engineers** - DB, APIs, data pipelines
- **1 Infrastructure Engineer** - Docker, Kubernetes, monitoring

### Phase 2 (Weeks 5-12)
- **2-3 ML Engineers** - Model training, fine-tuning
- **1 Infrastructure Engineer** - Model serving, optimization

### Phase 3 (Weeks 13-20)
- **2-3 Full-Stack Engineers** - Integration, UI, APIs
- **1 DevOps Engineer** - Deployment, monitoring

### Phase 4+ (Weeks 21+)
- **2 Backend Engineers** - Learning pipeline
- **1 ML Engineer** - Feedback loop
- **1 Data Engineer** - Data quality

---

## Getting Started Checklist

### Prerequisites
- [ ] PostgreSQL 13+ running
- [ ] Docker installed
- [ ] Python 3.9+ with venv
- [ ] Node.js 18+ with npm
- [ ] 100GB+ free disk space (for datasets)
- [ ] NVIDIA GPU recommended (for model training)

### Phase 1 Setup (4 weeks)
- [ ] Database schema created
- [ ] Milvus running
- [ ] MinIO running
- [ ] Python dependencies installed
- [ ] All 5 datasets ingested
- [ ] Vector indices built
- [ ] API endpoints tested

### Next Steps
1. **Review** COMPREHENSIVE_QA_UPGRADE_PLAN.md
2. **Plan** Phase 1 tasks and assign team
3. **Setup** databases and storage
4. **Ingest** datasets
5. **Validate** all systems working
6. **Document** any issues/learnings
7. **Plan** Phase 2 model training

---

## Documentation

### For Developers
- API Reference: `docs/api_v3_reference.md` (to create)
- CLI Guide: `docs/cli_commands.md` (to create)
- Integration Guide: `docs/integration_guide.md` (to create)

### For Operations
- Setup Guide: `docs/setup_guide.md` (to create)
- Troubleshooting: `docs/troubleshooting.md` (to create)
- Runbooks: `docs/runbooks/` (to create)

### For Data Scientists
- Training Guide: `ml/docs/training_guide.md` (to create)
- Evaluation: `ml/docs/evaluation.md` (to create)
- Inference: `ml/docs/inference.md` (to create)

---

## Contact & Support

### Questions?
- Review the main `COMPREHENSIVE_QA_UPGRADE_PLAN.md`
- Check `PHASE1_IMPLEMENTATION_GUIDE.md` for step-by-step instructions
- See existing implementations in `/qa/learning/` and `/tests/generators/`

### Issues?
- Check database connections
- Verify Docker containers running
- Confirm dataset files downloaded
- Review vector DB status

### Next Phase?
- Phase 1 complete → Start Phase 2 (Model Training)
- Phase 2 complete → Start Phase 3 (Integration)
- Continue through Phase 5+ for advanced features

---

## Key References

### Datasets
- **RepliQA**: https://huggingface.co/datasets/servicenow-ai/RepliQA
- **Defects4J**: https://defects4j.github.io/
- **RICO**: https://www.ics.uci.edu/~jutman/public_html/rico/
- **The Stack**: https://huggingface.co/datasets/bigcode/the-stack
- **ManyBugs**: http://manybugs.cs.umass.edu/

### Technologies
- **Playwright**: https://playwright.dev
- **Claude API**: https://docs.anthropic.com
- **Milvus**: https://milvus.io/
- **FastAPI**: https://fastapi.tiangolo.com/
- **PostgreSQL**: https://www.postgresql.org/

### Papers
- arXiv 2406.11811v1 - RepliQA Research
- arXiv 2502.12922v2 - Latest AI Testing

---

## Timeline Summary

```
Week 1-4   (Jun 13 - Jul 10)   Phase 1: Foundation
  ├─ Database & Storage Setup
  ├─ Dataset Ingestion
  └─ Vector Index Building

Week 5-12  (Jul 11 - Aug 28)   Phase 2: ML Models
  ├─ Train Test Generator
  ├─ Train Bug Detector
  ├─ Train UI Recognizer
  ├─ Train Code Analyzer
  └─ Train Fix Suggester

Week 13-20 (Aug 29 - Oct 16)  Phase 3: Integration
  ├─ Unified API v3
  ├─ CLI Commands
  ├─ Web Dashboard
  └─ CI/CD Integration

Week 21-26 (Oct 17 - Nov 27)  Phase 4: Learning
  ├─ Failure Collection
  ├─ Pattern Learning
  ├─ Confidence Scoring
  └─ Auto-Retraining

Week 27+   (Nov 28 - ∞)        Phase 5: Advanced
  ├─ Predictive Alerts
  ├─ Flakiness Detection
  ├─ Visual Regression
  ├─ Code Semantics
  └─ Debugging Agent
```

---

**Status**: Ready for Implementation  
**Current Phase**: Phase 1 (Foundation)  
**Start Date**: 2026-06-13  
**Projected Completion**: Phase 4 by 2026-11-27, Phase 5+ ongoing  

**Next Action**: Begin Phase 1 implementation following PHASE1_IMPLEMENTATION_GUIDE.md
