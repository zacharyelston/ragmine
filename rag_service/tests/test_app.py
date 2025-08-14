#!/usr/bin/env python3
"""
Unit tests for RAGmine Service

Tests the core functionality of the RAG service including:
- Health checks
- Search functionality
- Index management
- Error handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import time

from app import app, simple_search, MOCK_DOCUMENTS


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check functionality"""
    
    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data
        assert "services" in data
        
    def test_health_check_services_status(self, client):
        """Test health check includes service status"""
        response = client.get("/health")
        data = response.json()
        
        services = data["services"]
        assert "redis" in services
        assert "vector_db" in services
        assert "openai" in services


class TestSearchFunctionality:
    """Test search functionality"""
    
    def test_simple_search_exact_match(self):
        """Test simple search with exact keyword match"""
        results = simple_search("API authentication timeout", max_results=10)
        
        assert len(results) > 0
        # Should find the authentication timeout issue
        top_result = results[0]
        assert "authentication" in top_result.title.lower()
        assert "timeout" in top_result.title.lower()
        assert top_result.score > 0
        
    def test_simple_search_partial_match(self):
        """Test simple search with partial keyword match"""
        results = simple_search("database performance", max_results=10)
        
        assert len(results) > 0
        # Should find database-related content
        found_database = any("database" in result.title.lower() or 
                           "database" in result.content.lower() 
                           for result in results)
        assert found_database
        
    def test_simple_search_no_results(self):
        """Test simple search with no matching results"""
        results = simple_search("nonexistent query xyz123", max_results=10)
        assert len(results) == 0
        
    def test_simple_search_max_results_limit(self):
        """Test simple search respects max_results parameter"""
        results = simple_search("test", max_results=2)
        assert len(results) <= 2
        
    def test_simple_search_scoring(self):
        """Test that search results are properly scored and sorted"""
        results = simple_search("API authentication", max_results=10)
        
        if len(results) > 1:
            # Results should be sorted by score (descending)
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score


class TestSearchEndpoint:
    """Test search API endpoint"""
    
    def test_search_endpoint_success(self, client):
        """Test successful search request"""
        payload = {
            "query": "API authentication timeout",
            "max_results": 5
        }
        
        response = client.post("/search", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query"] == payload["query"]
        assert "results" in data
        assert "total_count" in data
        assert "response_time" in data
        assert data["method"] == "rag"
        assert data["response_time"] > 0
        
    def test_search_endpoint_with_filters(self, client):
        """Test search with additional filters"""
        payload = {
            "query": "authentication",
            "project": "test-project",
            "max_results": 10,
            "filters": {"priority": "high"}
        }
        
        response = client.post("/search", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query"] == payload["query"]
        
    def test_search_endpoint_invalid_request(self, client):
        """Test search with invalid request data"""
        # Missing required query field
        payload = {"max_results": 5}
        
        response = client.post("/search", json=payload)
        assert response.status_code == 422  # Validation error
        
    def test_search_endpoint_empty_query(self, client):
        """Test search with empty query"""
        payload = {"query": "", "max_results": 5}
        
        response = client.post("/search", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query"] == ""
        assert len(data["results"]) == 0


class TestIndexManagement:
    """Test index management functionality"""
    
    def test_rebuild_index_success(self, client):
        """Test successful index rebuild"""
        response = client.post("/index/rebuild")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data
        assert "documents_indexed" in data
        assert "timestamp" in data
        assert data["documents_indexed"] == len(MOCK_DOCUMENTS)
        
    def test_add_documents_success(self, client):
        """Test successful document addition"""
        payload = {
            "documents": [
                {
                    "id": "test-doc-1",
                    "title": "Test Document",
                    "content": "This is a test document for indexing",
                    "metadata": {"type": "test"}
                }
            ],
            "project": "test-project"
        }
        
        response = client.post("/index/add", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data
        assert "timestamp" in data
        
    def test_add_documents_empty_list(self, client):
        """Test adding empty document list"""
        payload = {"documents": []}
        
        response = client.post("/index/add", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service info"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "RAGmine Service"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"
        assert data["docs"] == "/docs"


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @patch('app.simple_search')
    def test_search_internal_error(self, mock_search, client):
        """Test search endpoint handles internal errors"""
        mock_search.side_effect = Exception("Simulated error")
        
        payload = {"query": "test query", "max_results": 5}
        response = client.post("/search", json=payload)
        
        assert response.status_code == 500
        data = response.json()
        assert "Search failed" in data["detail"]
        
    @patch('app.logger')
    def test_index_rebuild_error(self, mock_logger, client):
        """Test index rebuild handles errors gracefully"""
        with patch('app.MOCK_DOCUMENTS', side_effect=Exception("Simulated error")):
            response = client.post("/index/rebuild")
            assert response.status_code == 500


class TestPerformance:
    """Test performance characteristics"""
    
    def test_search_response_time(self, client):
        """Test that search responses are reasonably fast"""
        payload = {"query": "API authentication", "max_results": 5}
        
        start_time = time.time()
        response = client.post("/search", json=payload)
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Response should be fast (under 1 second for mock data)
        response_time = end_time - start_time
        assert response_time < 1.0
        
        # Check reported response time is reasonable
        data = response.json()
        assert data["response_time"] < 1.0
        
    def test_concurrent_searches(self, client):
        """Test handling multiple concurrent search requests"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        payload = {"query": "test query", "max_results": 5}
        
        def make_request():
            response = client.post("/search", json=payload)
            results_queue.put(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all requests succeeded
        while not results_queue.empty():
            status_code = results_queue.get()
            assert status_code == 200


class TestDataValidation:
    """Test data validation and edge cases"""
    
    def test_mock_documents_structure(self):
        """Test that mock documents have required structure"""
        for doc in MOCK_DOCUMENTS:
            assert "id" in doc
            assert "title" in doc
            assert "content" in doc
            assert "source" in doc
            assert "metadata" in doc
            
            # Check data types
            assert isinstance(doc["id"], str)
            assert isinstance(doc["title"], str)
            assert isinstance(doc["content"], str)
            assert isinstance(doc["source"], str)
            assert isinstance(doc["metadata"], dict)
            
    def test_search_result_structure(self):
        """Test that search results have proper structure"""
        results = simple_search("API", max_results=5)
        
        for result in results:
            assert hasattr(result, 'id')
            assert hasattr(result, 'title')
            assert hasattr(result, 'content')
            assert hasattr(result, 'score')
            assert hasattr(result, 'source')
            assert hasattr(result, 'metadata')
            
            # Check data types
            assert isinstance(result.id, str)
            assert isinstance(result.title, str)
            assert isinstance(result.content, str)
            assert isinstance(result.score, (int, float))
            assert isinstance(result.source, str)
            assert isinstance(result.metadata, dict)
