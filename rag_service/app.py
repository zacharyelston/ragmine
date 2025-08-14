#!/usr/bin/env python3
"""
RAGmine Service - FastAPI Application

Basic RAG service for semantic search and document processing.
This is a minimal implementation for testing the Docker Compose deployment.
"""

import os
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger

# Initialize FastAPI app
app = FastAPI(
    title="RAGmine Service",
    description="Retrieval-Augmented Generation service for Redmine/RedMica",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    project: Optional[str] = Field(None, description="Project identifier")
    max_results: int = Field(20, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")

class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = {}

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_count: int
    response_time: float
    method: str = "rag"

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float
    services: Dict[str, str]

class IndexRequest(BaseModel):
    documents: List[Dict[str, Any]]
    project: Optional[str] = None

# Mock data for testing
MOCK_DOCUMENTS = [
    {
        "id": "issue-1001",
        "title": "API Authentication Timeout Issues",
        "content": "Users experiencing timeout errors when authenticating via API. Symptoms include 504 Gateway Timeout errors, authentication requests taking >30 seconds, intermittent failures during peak hours.",
        "source": "issue",
        "metadata": {"priority": "High", "status": "Resolved", "tags": ["api", "authentication", "timeout"]}
    },
    {
        "id": "issue-1002", 
        "title": "Database Query Performance Degradation",
        "content": "Search queries running significantly slower than expected. Performance metrics show simple searches taking 2-5 seconds, complex searches 10-15 seconds, database CPU usage 80-90%.",
        "source": "issue",
        "metadata": {"priority": "High", "status": "Open", "tags": ["database", "performance", "search"]}
    },
    {
        "id": "wiki-api-docs",
        "title": "API Documentation",
        "content": "Complete API documentation including authentication methods, common endpoints, error handling, and rate limiting information.",
        "source": "wiki",
        "metadata": {"category": "documentation", "tags": ["api", "authentication", "endpoints"]}
    },
    {
        "id": "wiki-troubleshooting",
        "title": "Troubleshooting Guide", 
        "content": "Common issues and solutions including authentication problems, performance issues, search not working, and getting help procedures.",
        "source": "wiki",
        "metadata": {"category": "support", "tags": ["troubleshooting", "authentication", "performance"]}
    }
]

def simple_search(query: str, max_results: int = 20) -> List[SearchResult]:
    """
    Simple keyword-based search for testing.
    In production, this would use vector embeddings and semantic search.
    """
    query_lower = query.lower()
    results = []
    
    for doc in MOCK_DOCUMENTS:
        # Simple scoring based on keyword matches
        score = 0.0
        title_lower = doc["title"].lower()
        content_lower = doc["content"].lower()
        
        # Title matches get higher score
        if query_lower in title_lower:
            score += 0.8
        
        # Content matches
        if query_lower in content_lower:
            score += 0.5
            
        # Individual word matches
        query_words = query_lower.split()
        for word in query_words:
            if word in title_lower:
                score += 0.3
            if word in content_lower:
                score += 0.1
        
        if score > 0:
            results.append(SearchResult(
                id=doc["id"],
                title=doc["title"],
                content=doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                score=score,
                source=doc["source"],
                metadata=doc["metadata"]
            ))
    
    # Sort by score and limit results
    results.sort(key=lambda x: x.score, reverse=True)
    return results[:max_results]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=time.time(),
        services={
            "redis": "connected" if os.getenv("REDIS_URL") else "not_configured",
            "vector_db": "connected" if os.getenv("VECTOR_DB_URL") else "not_configured",
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured"
        }
    )

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Semantic search endpoint
    """
    start_time = time.time()
    
    try:
        # Perform search (using simple keyword search for now)
        results = simple_search(request.query, request.max_results)
        
        response_time = time.time() - start_time
        
        logger.info(f"Search query: '{request.query}' returned {len(results)} results in {response_time:.3f}s")
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_count=len(results),
            response_time=response_time,
            method="rag"
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/index/rebuild")
async def rebuild_index():
    """
    Rebuild search index
    """
    try:
        # In production, this would rebuild vector embeddings
        logger.info("Index rebuild triggered (mock implementation)")
        
        return {
            "status": "success",
            "message": "Index rebuild completed",
            "documents_indexed": len(MOCK_DOCUMENTS),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Index rebuild error: {e}")
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")

@app.post("/index/add")
async def add_documents(request: IndexRequest):
    """
    Add documents to search index
    """
    try:
        # In production, this would process and embed documents
        logger.info(f"Adding {len(request.documents)} documents to index")
        
        return {
            "status": "success",
            "message": f"Added {len(request.documents)} documents to index",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Document indexing error: {e}")
        raise HTTPException(status_code=500, detail=f"Document indexing failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RAGmine Service",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    # Configure logging
    logger.add("logs/ragmine.log", rotation="1 day", retention="7 days")
    
    # Start server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )