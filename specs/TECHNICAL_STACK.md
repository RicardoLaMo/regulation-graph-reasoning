# Technical Stack: NLP Legal Violation Detection System

## Overview

This document specifies the complete technical stack for the automated legal violation detection system. The stack is designed to support local Python-first development with clear paths to production scaling, emphasizing open-source solutions and cost-effective deployment.

## Core Technology Stack

### Programming Languages & Frameworks

#### Primary Language: Python 3.9+
**Justification**: Extensive ML/NLP ecosystem, legal-domain libraries, rapid development

**Core Dependencies**:
```python
# ML/NLP Core
transformers==4.35.0          # Hugging Face transformer models
torch==2.1.0                  # PyTorch for model inference
spacy==3.7.0                  # NLP preprocessing and NER
sentence-transformers==2.2.2  # Semantic embeddings
scikit-learn==1.3.0          # Traditional ML utilities

# Legal Domain Specific
blackstone==0.1.15           # Legal NLP for spaCy
legal-bert                   # Via transformers library

# Web Framework
fastapi==0.104.1            # REST API framework
uvicorn==0.24.0             # ASGI server
pydantic==2.5.0             # Data validation

# Data Processing
pandas==2.1.3               # Data manipulation
numpy==1.24.0               # Numerical computing
networkx==3.2               # Graph operations (alternative to Neo4j)

# Database & Caching
sqlalchemy==2.0.23          # Database ORM
alembic==1.12.1             # Database migrations
redis==5.0.1                # Caching and sessions
psycopg2==2.9.9             # PostgreSQL adapter
```

#### Secondary Languages
- **JavaScript/TypeScript**: Web UI development (React/Vue.js)
- **Shell/Bash**: Deployment scripts and automation
- **SQL**: Database queries and analytics

### Machine Learning & NLP Stack

#### Hugging Face Ecosystem
**Primary Model Hub**: All models sourced from Hugging Face Hub for consistency

**Core Models**:
```yaml
Classification:
  - model: "Mahesh9/distil-bert-finetuned-cfpb-complaints"
    purpose: "CFPB complaint product/issue classification"
    performance: "~95% accuracy"
    inference_time: "~50ms"

Legal Domain:
  - model: "nlpaueb/legal-bert-base-uncased"
    purpose: "Legal text understanding and NER"
    domain: "Legal documents and case law"
    
  - model: "Stern5497/sbert-legal-xlm-roberta-base"
    purpose: "Legal text semantic embeddings"
    use_case: "Statute similarity and retrieval"

Legal Reasoning:
  - model: "SaulLM-7B"
    purpose: "Legal reasoning and analysis"
    license: "MIT (locally runnable)"
    requirements: "Single GPU deployment"
    inference_time: "~2000ms for complex reasoning"

Financial Domain:
  - model: "ProsusAI/finbert"
    purpose: "Financial sentiment and entity analysis"
    use_case: "Consumer harm assessment"

NLI Models:
  - model: "facebook/bart-large-mnli"
    purpose: "Natural Language Inference"
    use_case: "Legal hypothesis testing"
    
  - model: "microsoft/deberta-large-mnli"
    purpose: "Enhanced NLI for legal entailment"
    performance: "Higher accuracy, slower inference"
```

#### Model Optimization Stack
```yaml
Optimization:
  - onnx: "Model conversion for faster inference"
  - onnxruntime: "Optimized model serving"
  - torch.jit: "TorchScript compilation"
  - quantization: "8-bit model quantization"

Serving:
  - torchserve: "Production model serving"
  - ray-serve: "Distributed model serving (scaling)"
  - triton: "NVIDIA inference server (GPU clusters)"
```

### Data Storage & Processing

#### Primary Database: PostgreSQL 15+
**Justification**: ACID compliance, JSON support, full-text search, mature ecosystem

**Schema Design**:
```sql
-- Core complaint processing
complaints_processed(
  id SERIAL PRIMARY KEY,
  complaint_id VARCHAR UNIQUE,
  narrative TEXT,
  metadata JSONB,
  processing_status VARCHAR,
  created_at TIMESTAMP
);

-- Violation detection results
violation_detections(
  id SERIAL PRIMARY KEY,
  complaint_id VARCHAR REFERENCES complaints_processed(complaint_id),
  statute VARCHAR,
  violation_type VARCHAR,
  confidence FLOAT,
  evidence JSONB,
  reasoning_path TEXT,
  model_version VARCHAR,
  detected_at TIMESTAMP
);

-- Knowledge graph entities
legal_entities(
  id SERIAL PRIMARY KEY,
  complaint_id VARCHAR,
  entity_type VARCHAR,
  entity_value VARCHAR,
  confidence FLOAT,
  source_model VARCHAR
);
```

#### Graph Database: Neo4j Community Edition
**Use Case**: Knowledge graph storage and complex relationship queries
**Alternative**: NetworkX (for simpler deployments)

**Graph Schema**:
```cypher
// Core entity types
(Consumer)-[:FILED_COMPLAINT]->(Complaint)
(Company)-[:SUBJECT_OF]->(Complaint)
(Complaint)-[:INVOLVES]->(Product)
(Complaint)-[:VIOLATES]->(Statute)
(Statute)-[:PART_OF]->(Regulation)

// Relationship properties include confidence, evidence, detection_method
```

#### Caching: Redis 7+
**Use Cases**:
- Model prediction caching
- Frequent query result caching
- Session management
- Rate limiting

**Configuration**:
```redis
# Cache strategies
complaint_embeddings:* TTL=7days
model_predictions:* TTL=24hours
statute_similarities:* TTL=30days
```

#### Vector Database: FAISS (Facebook AI Similarity Search)
**Purpose**: Fast semantic similarity search for legal concepts
**Alternative**: Pinecone (cloud), Weaviate (self-hosted)

**Configuration**:
```python
# Index configuration
index_type = "IVF_PQ"  # Inverted file with product quantization
embedding_dimension = 768  # Legal-BERT output dimension
num_clusters = 1000  # For 100K+ legal concept embeddings
```

### Web Framework & API

#### API Framework: FastAPI
**Features**:
- Automatic OpenAPI documentation
- Request/response validation with Pydantic
- Async support for concurrent processing
- Built-in security features

**API Structure**:
```python
# Core endpoints
POST /api/v1/complaints/analyze      # Single complaint analysis
POST /api/v1/complaints/batch        # Batch processing
GET  /api/v1/complaints/{id}/result  # Retrieve analysis result
GET  /api/v1/statutes/search         # Legal statute search
GET  /api/v1/health                  # System health check

# Admin endpoints
POST /api/v1/models/update           # Model version updates
GET  /api/v1/metrics                 # System performance metrics
```

#### Web Server: Uvicorn + Nginx
- **Uvicorn**: ASGI server for FastAPI
- **Nginx**: Reverse proxy, load balancing, static files
- **Gunicorn**: Process manager for production deployment

### Infrastructure & DevOps

#### Containerization: Docker
**Multi-stage builds** for optimized production images:

```dockerfile
# Base image with Python and ML dependencies
FROM python:3.9-slim as base
RUN apt-get update && apt-get install -y gcc g++ && \
    pip install torch transformers[torch]

# Development image with additional tools
FROM base as development
RUN pip install pytest jupyter black flake8
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Production image optimized for size
FROM base as production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc g++ && apt-get autoremove -y
COPY src/ /app/
```

#### Orchestration: Docker Compose (Local) → Kubernetes (Production)

**Local Development**:
```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports: ["8000:8000"]
    depends_on: [db, redis]
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: legal_violations
  
  redis:
    image: redis:7-alpine
  
  neo4j:
    image: neo4j:community
    environment:
      NEO4J_AUTH: neo4j/password
```

**Production Scaling** (Kubernetes):
- Horizontal Pod Autoscaling
- GPU node pools for model inference
- Persistent volumes for databases
- ConfigMaps for environment-specific settings

#### Monitoring & Observability

**Metrics**: Prometheus + Grafana
```python
# Custom metrics
complaint_processing_duration = Histogram('complaint_processing_seconds')
violation_detection_accuracy = Gauge('violation_detection_accuracy')
model_inference_time = Histogram('model_inference_seconds')
```

**Logging**: Structured JSON logging with ELK Stack
```python
import structlog

logger = structlog.get_logger()
logger.info("violation_detected", 
           complaint_id=complaint_id,
           statute="FCRA",
           confidence=0.87,
           processing_time=1.2)
```

**Tracing**: OpenTelemetry for distributed tracing
- Track request flows through microservices
- Monitor model inference performance
- Debug complex legal reasoning chains

### Development Tools & Workflow

#### Code Quality
```yaml
Formatting: black, isort
Linting: flake8, pylint
Type Checking: mypy
Testing: pytest, pytest-cov
Security: bandit, safety
```

#### Development Environment
```yaml
IDE: VS Code with Python extension
Notebooks: Jupyter Lab for experimentation
Version Control: Git with pre-commit hooks
Package Management: pip-tools for dependency locking
```

#### CI/CD Pipeline (GitHub Actions)
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=src/
      - name: Type checking
        run: mypy src/
```

### Security Stack

#### Application Security
- **Input Validation**: Pydantic models for all API inputs
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Content Security Policy headers
- **Rate Limiting**: Redis-based rate limiting per API key
- **Authentication**: JWT tokens with refresh mechanism

#### Data Security
- **Encryption at Rest**: Database-level encryption (PostgreSQL TDE)
- **Encryption in Transit**: TLS 1.3 for all communications
- **PII Detection**: Automatic detection and masking of sensitive information
- **Audit Logging**: Complete audit trail of all data access

#### Model Security
- **Model Integrity**: SHA-256 checksums for all model files
- **Input Sanitization**: Strict input validation before model inference
- **Output Filtering**: Content filtering for generated legal text
- **Model Versioning**: Cryptographically signed model updates

### Performance & Scaling Configuration

#### Local Development Setup
```yaml
Hardware Requirements:
  CPU: 8+ cores (Intel i7/AMD Ryzen 7)
  GPU: RTX 4070 or better (12GB+ VRAM)
  RAM: 32GB minimum
  Storage: 1TB NVMe SSD

Performance Targets:
  - Single complaint: <3 seconds
  - Batch processing: 100-500 complaints/hour
  - Concurrent users: 10-20 developers
```

#### Production Scaling Configuration
```yaml
API Tier:
  - Horizontal scaling: 3-10 FastAPI instances
  - Load balancer: Nginx with upstream pools
  - Auto-scaling: Based on CPU/memory usage

Model Inference:
  - GPU nodes: 2-4 nodes with Tesla T4/V100
  - Model serving: TorchServe with batch inference
  - Caching: Redis cluster for prediction caching

Database:
  - Primary: PostgreSQL 15 with read replicas
  - Graph: Neo4j cluster with 3 nodes
  - Caching: Redis Cluster with 6 nodes

Performance Targets:
  - Throughput: 10,000+ complaints/hour
  - Latency: <2 seconds average processing
  - Availability: 99.9% uptime SLA
```

### Cost Optimization Strategies

#### Development Phase
- **Local-first approach**: Minimize cloud costs during development
- **Open-source models**: Use MIT/Apache licensed models (SaulLM-7B)
- **Efficient models**: Prioritize smaller models where accuracy allows
- **Caching**: Aggressive caching to reduce repeated computations

#### Production Optimization
- **Spot instances**: Use preemptible GPU instances for batch processing
- **Auto-scaling**: Scale down during low-usage periods
- **Model optimization**: ONNX conversion and quantization
- **CDN**: Cache static assets and frequent API responses

### Technology Alternatives & Migration Paths

#### Alternative Stacks
```yaml
Lighter Stack (for smaller deployments):
  Database: SQLite → PostgreSQL
  Graph: NetworkX → Neo4j
  Caching: In-memory → Redis
  
Enterprise Stack (for large-scale deployments):
  Orchestration: Kubernetes
  Service Mesh: Istio
  Message Queue: Apache Kafka
  Storage: Distributed PostgreSQL (Citus)
```

#### Migration Strategy
1. **Phase 1**: Local development with SQLite + NetworkX
2. **Phase 2**: Add PostgreSQL + Redis for multi-user development
3. **Phase 3**: Production deployment with full stack
4. **Phase 4**: Enterprise scaling with Kubernetes and distributed systems

This technical stack provides a comprehensive foundation for building, deploying, and scaling the legal violation detection system while maintaining flexibility for different deployment scenarios and organizational requirements.