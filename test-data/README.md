# RAGmine Integration Test Data

This directory contains structured test data for validating RAGmine's search capabilities through before/after comparison testing.

## Data Structure

### Core Test Scenarios

1. **Technical Documentation Search**
   - API documentation with code examples
   - Configuration guides
   - Troubleshooting procedures

2. **Project Knowledge Base**
   - Meeting notes and decisions
   - Architecture documents
   - Process documentation

3. **Issue Resolution History**
   - Bug reports with solutions
   - Feature requests with implementation details
   - Support tickets with resolutions

## Test Data Categories

### `/documents/` - Structured Content
```
documents/
├── api/
│   ├── authentication.md
│   ├── endpoints.md
│   └── examples.md
├── guides/
│   ├── installation.md
│   ├── configuration.md
│   └── troubleshooting.md
├── architecture/
│   ├── system-overview.md
│   ├── database-schema.md
│   └── security-model.md
└── processes/
    ├── deployment.md
    ├── code-review.md
    └── incident-response.md
```

### `/issues/` - Redmine Issues (JSON format)
```json
{
  "id": 1001,
  "subject": "API Authentication Timeout Issues",
  "description": "Users experiencing timeout errors when authenticating via API...",
  "status": "Resolved",
  "priority": "High",
  "category": "Bug",
  "resolution": "Increased timeout values in nginx configuration...",
  "tags": ["api", "authentication", "timeout", "nginx"]
}
```

### `/wiki/` - Wiki Pages
```
wiki/
├── development/
│   ├── coding-standards.md
│   ├── testing-guidelines.md
│   └── deployment-process.md
├── operations/
│   ├── monitoring.md
│   ├── backup-procedures.md
│   └── disaster-recovery.md
└── user-guides/
    ├── getting-started.md
    ├── advanced-features.md
    └── faq.md
```

## Test Query Categories

### 1. **Exact Match Queries**
- "API authentication timeout"
- "nginx configuration"
- "deployment process"

### 2. **Semantic Queries**
- "How do I fix login problems?"
- "What's the best way to deploy changes?"
- "Why is the system running slowly?"

### 3. **Complex Multi-Context Queries**
- "Show me all authentication issues and their solutions"
- "What are the security considerations for API deployment?"
- "How do monitoring and backup procedures relate?"

## Before/After Test Structure

### Baseline Test (Without RAG)
```bash
# Standard Redmine search
curl -X GET "http://localhost:3000/search.json?q=authentication+timeout"
```

### RAG-Enhanced Test (With RAG)
```bash
# RAGmine semantic search
curl -X POST "http://localhost:3000/ragmine/search.json" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I fix authentication timeout issues?"}'
```

### Comparison Metrics
- **Relevance Score**: How well results match user intent
- **Response Time**: Query execution time
- **Result Quality**: Accuracy and completeness of answers
- **Context Awareness**: Understanding of relationships between documents

## Test Data Loading

### 1. **Automated Data Seeding**
```bash
# Load test data into Redmica
docker compose --profile testing up test-data-loader
```

### 2. **Manual Data Verification**
```bash
# Verify data loaded correctly
docker compose exec redmica rails runner "puts Issue.count"
docker compose exec redmica rails runner "puts WikiPage.count"
```

### 3. **RAG Index Building**
```bash
# Trigger initial indexing
curl -X POST "http://localhost:8000/index/rebuild"
```

## Integration Test Execution

### 1. **Run Baseline Tests**
```bash
docker compose --profile testing run integration-tests pytest tests/baseline/
```

### 2. **Run RAG-Enhanced Tests**
```bash
docker compose --profile testing run integration-tests pytest tests/rag-enhanced/
```

### 3. **Generate Comparison Report**
```bash
docker compose --profile testing run integration-tests python generate_report.py
```

## Expected Improvements

### Search Quality Metrics
- **Precision**: 85%+ (vs 60% baseline)
- **Recall**: 90%+ (vs 70% baseline)
- **User Satisfaction**: 4.5/5 (vs 3.2/5 baseline)

### Performance Metrics
- **Response Time**: <2 seconds
- **Cache Hit Rate**: 90%+
- **System Load**: <5% increase on Redmica

### Functional Improvements
- **Semantic Understanding**: Natural language queries
- **Context Awareness**: Cross-document relationships
- **Answer Generation**: Direct answers vs just document links
- **Multi-language Support**: Query translation and results
