# RAG Ecosystem Tooling Pairing List

## Core Components & Their Tool Pairings

### 1. **Document Loading & Ingestion**
- **Web Content**: `WebBaseLoader` (LangChain) + `BeautifulSoup4` (HTML parsing)
- **YouTube**: `YoutubeLoader` (LangChain Community)
- **Wikipedia**: Native `requests` library + Wikipedia API
- **General Purpose**: LangChain document loaders ecosystem

### 2. **Text Processing & Chunking**
- **Primary Splitter**: `RecursiveCharacterTextSplitter` (LangChain)
- **Token-aware Splitting**: `from_tiktoken_encoder` method
- **Chunk Size Management**: 
  - Small chunks (300-500 tokens) for precision retrieval
  - Large chunks (1000+ tokens) for context-rich generation
  - Overlap management (50-200 tokens typical)

### 3. **Embedding Models**
- **OpenAI Embeddings**: `OpenAIEmbeddings` (primary choice)
- **Token-Level Embeddings**: ColBERT via `RAGatouille`
- **Alternative Models**: Can swap with Cohere, HuggingFace embeddings

### 4. **Vector Storage & Indexing**
- **Primary Vector Store**: `Chroma` (in-memory or persistent)
- **Multi-Vector Storage**: 
  - `MultiVectorRetriever` (LangChain)
  - `InMemoryByteStore` for parent documents
- **Specialized Indexing**:
  - ColBERT indexing via `RAGatouille`
  - RAPTOR (Hierarchical indexing) - conceptual implementation

### 5. **Query Transformation Techniques**

#### A. **Multi-Query Generation**
- **LLM**: `ChatOpenAI` for query generation
- **Chain**: Custom prompt + LLM + output parser
- **Aggregation**: Union of results or RRF

#### B. **RAG-Fusion**
- **Query Generation**: Same as multi-query
- **Re-ranking**: Reciprocal Rank Fusion (RRF) algorithm
- **Implementation**: Custom Python function

#### C. **Query Decomposition**
- **LLM**: `ChatOpenAI` for breaking down complex queries
- **Chain**: Iterative Q&A generation and synthesis

#### D. **Step-Back Prompting**
- **Few-Shot Learning**: `FewShotChatMessagePromptTemplate`
- **Chain**: Custom prompt engineering

#### E. **HyDE (Hypothetical Document Embeddings)**
- **Document Generation**: `ChatOpenAI` for hypothetical answers
- **Embedding**: Standard embedding model for similarity search

### 6. **Routing & Query Construction**

#### A. **Logical Routing**
- **Schema Definition**: `Pydantic` models
- **LLM with Structure**: `.with_structured_output()` method
- **Routing Logic**: `RunnableLambda` for branching

#### B. **Semantic Routing**
- **Similarity Calculation**: `cosine_similarity` (LangChain utils)
- **Embedding Model**: `OpenAIEmbeddings`
- **Dynamic Prompt Selection**: Custom routing function

#### C. **Query Structuring**
- **Metadata Extraction**: Pydantic models for structured queries
- **Date/Time Handling**: Python `datetime`
- **Filter Construction**: Custom schema per data source

### 7. **Advanced Retrieval**

#### A. **Re-ranking**
- **Cohere Re-ranker**: `CohereRerank` via `ContextualCompressionRetriever`
- **RRF**: Custom implementation for multi-query fusion
- **Score-based filtering**: Relevance score thresholds

#### B. **Self-Correction**
- **CRAG**: LangGraph implementation (referenced)
- **Self-RAG**: LangGraph + reflection tokens
- **Grading**: LLM-as-judge pattern

### 8. **LLM Models**
- **Primary Generation**: `ChatOpenAI` (gpt-3.5-turbo, gpt-4)
- **Evaluation**: `gpt-4o` for judge tasks
- **Temperature Settings**: 
  - 0 for consistency/evaluation
  - Variable for creative tasks

### 9. **Prompt Management**
- **Template System**: `ChatPromptTemplate`, `PromptTemplate`
- **Hub Integration**: `langchain.hub` for pre-made prompts
- **Few-Shot**: `FewShotChatMessagePromptTemplate`

### 10. **Chain Construction (LCEL)**
- **Basic Chains**: Pipe operator (`|`) for composition
- **Parallel Processing**: Dictionary syntax for parallel operations
- **Conditional Logic**: `RunnableLambda` for custom logic
- **Pass-through**: `RunnablePassthrough` for data forwarding

### 11. **Evaluation Frameworks**

#### A. **Manual Evaluation**
- **LLM-as-Judge**: Custom chains with structured output
- **Metrics**:
  - Faithfulness
  - Correctness
  - Contextual Relevancy

#### B. **DeepEval Framework**
```python
pip install deepeval
```
- **Metrics**: `GEval`, `FaithfulnessMetric`, `ContextualRelevancyMetric`
- **Test Cases**: `LLMTestCase`

#### C. **Grouse Framework**
```python
pip install grouse-eval
```
- Alternative evaluation framework

#### D. **RAGAS Framework**
```python
pip install ragas
```
- **Metrics**: Answer relevancy, context precision, faithfulness
- **Dataset Management**: Built-in test dataset support

### 12. **Monitoring & Tracing**
- **LangSmith**: Via environment variables
  - `LANGCHAIN_ENDPOINT`
  - `LANGCHAIN_API_KEY`
- **Tracing**: Automatic with LangChain integration

### 13. **Utility Libraries**
- **JSON Handling**: `json` (standard library)
- **UUID Generation**: `uuid` for unique identifiers
- **Math Utils**: `langchain.utils.math` for cosine similarity
- **Type Hints**: `typing` for better code structure

## Tool Pairing Strategies

### For Basic RAG:
1. `WebBaseLoader` → `RecursiveCharacterTextSplitter` → `Chroma` → `OpenAIEmbeddings` → `ChatOpenAI`

### For Advanced Query Understanding:
1. **Multi-Query**: Custom prompt → Multiple retrievals → Union/RRF
2. **HyDE**: Generate hypothetical → Embed → Retrieve real

### For Production Systems:
1. **Indexing**: Multi-representation with `MultiVectorRetriever`
2. **Retrieval**: Base retriever → Cohere re-ranking → Top-k selection
3. **Generation**: Retrieved context → Prompt template → LLM → Output parsing
4. **Evaluation**: DeepEval/RAGAS for comprehensive metrics

### For Specialized Use Cases:
1. **Token-level search**: RAGatouille with ColBERT
2. **Hierarchical knowledge**: RAPTOR-style clustering and summarization
3. **Multi-source routing**: Pydantic schemas + structured LLM output

## Dependencies Summary

### Core Dependencies:
```bash
pip install langchain langchain_community langchain-openai langchainhub chromadb tiktoken
```

### Advanced Features:
```bash
pip install ragatouille  # For ColBERT
pip install cohere       # For re-ranking
```

### Evaluation:
```bash
pip install deepeval     # Evaluation framework
pip install grouse-eval  # Alternative evaluation
pip install ragas        # RAGAS framework
```

## Key Design Patterns

1. **Separation of Concerns**: Retrieval representation vs. generation context
2. **Multi-stage Processing**: Query → Transform → Route → Retrieve → Re-rank → Generate
3. **Graceful Degradation**: Fallback strategies when primary methods fail
4. **Iterative Refinement**: Self-correction and reflection loops
5. **Structured Output**: Pydantic models for reliable parsing
6. **Composability**: LCEL for building complex chains from simple components

## Performance Considerations

1. **Batch Processing**: Use `.batch()` for parallel operations
2. **Caching**: Vector store persistence for avoiding re-embedding
3. **Lazy Loading**: Stream processing where possible
4. **Resource Management**: In-memory vs. persistent storage trade-offs
5. **API Rate Limits**: Especially for OpenAI and Cohere services

## Best Practices

1. **Start Simple**: Basic RAG → Add complexity incrementally
2. **Measure Everything**: Implement evaluation from day one
3. **Version Control**: Track prompts, chunks sizes, and model choices
4. **Test Coverage**: Unit tests for each component
5. **Documentation**: Clear documentation of each pipeline stage
6. **Error Handling**: Graceful failures at each step
7. **Monitoring**: Production metrics and alerting