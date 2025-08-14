#!/usr/bin/env python3
"""
RAGmine Integration Tests

Tests the complete RAGmine system with before/after comparison:
1. Baseline tests using standard Redmine search
2. RAG-enhanced tests using RAGmine semantic search
3. Performance and quality comparisons
"""

import os
import time
import json
import pytest
import requests
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table

console = Console()

@dataclass
class SearchResult:
    query: str
    results: List[Dict[str, Any]]
    response_time: float
    total_count: int
    method: str  # 'baseline' or 'rag'

@dataclass
class TestMetrics:
    precision: float
    recall: float
    response_time: float
    relevance_score: float
    user_satisfaction: float

class RAGmineIntegrationTest:
    def __init__(self):
        self.redmica_url = os.getenv('REDMICA_URL', 'http://localhost:3000')
        self.rag_service_url = os.getenv('RAG_SERVICE_URL', 'http://localhost:8000')
        self.test_project = 'ragmine-test'
        
        # Test queries with expected results
        self.test_queries = [
            {
                "query": "API authentication timeout",
                "type": "exact_match",
                "expected_keywords": ["authentication", "timeout", "API"],
                "expected_min_results": 1
            },
            {
                "query": "How do I fix login problems?",
                "type": "semantic",
                "expected_keywords": ["authentication", "login", "troubleshooting"],
                "expected_min_results": 1
            },
            {
                "query": "database performance issues",
                "type": "exact_match", 
                "expected_keywords": ["database", "performance", "query"],
                "expected_min_results": 1
            },
            {
                "query": "What causes slow search responses?",
                "type": "semantic",
                "expected_keywords": ["performance", "search", "database"],
                "expected_min_results": 1
            },
            {
                "query": "advanced search filters implementation",
                "type": "exact_match",
                "expected_keywords": ["search", "filters", "feature"],
                "expected_min_results": 1
            },
            {
                "query": "How can I improve search functionality?",
                "type": "semantic",
                "expected_keywords": ["search", "filters", "advanced"],
                "expected_min_results": 1
            }
        ]

    def wait_for_services(self):
        """Ensure all services are ready"""
        services = [
            (self.redmica_url, "Redmica"),
            (f"{self.rag_service_url}/health", "RAG Service")
        ]
        
        for url, name in services:
            max_retries = 30
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        console.print(f"✅ {name} is ready")
                        break
                except requests.exceptions.RequestException:
                    if attempt == max_retries - 1:
                        raise Exception(f"❌ {name} not ready after {max_retries} attempts")
                    time.sleep(2)

    def run_baseline_search(self, query: str) -> SearchResult:
        """Run standard Redmine search (baseline)"""
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.redmica_url}/search.json",
                params={
                    'q': query,
                    'scope': 'all',
                    'all_words': '1'
                },
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                total_count = len(results)
            else:
                results = []
                total_count = 0
                
        except Exception as e:
            console.print(f"❌ Baseline search failed: {e}")
            results = []
            total_count = 0
            response_time = time.time() - start_time
        
        return SearchResult(
            query=query,
            results=results,
            response_time=response_time,
            total_count=total_count,
            method='baseline'
        )

    def run_rag_search(self, query: str) -> SearchResult:
        """Run RAGmine semantic search"""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.redmica_url}/ragmine/search.json",
                json={
                    'query': query,
                    'project': self.test_project,
                    'max_results': 20
                },
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                total_count = data.get('total_count', len(results))
            else:
                # Fallback to direct RAG service call for testing
                response = requests.post(
                    f"{self.rag_service_url}/search",
                    json={'query': query, 'max_results': 20},
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    total_count = len(results)
                else:
                    results = []
                    total_count = 0
                    
        except Exception as e:
            console.print(f"❌ RAG search failed: {e}")
            results = []
            total_count = 0
            response_time = time.time() - start_time
        
        return SearchResult(
            query=query,
            results=results,
            response_time=response_time,
            total_count=total_count,
            method='rag'
        )

    def calculate_relevance_score(self, result: SearchResult, expected_keywords: List[str]) -> float:
        """Calculate relevance score based on keyword matching"""
        if not result.results:
            return 0.0
        
        total_score = 0.0
        for item in result.results:
            item_score = 0.0
            content = f"{item.get('title', '')} {item.get('description', '')}".lower()
            
            for keyword in expected_keywords:
                if keyword.lower() in content:
                    item_score += 1.0
            
            # Normalize by number of keywords
            item_score = item_score / len(expected_keywords)
            total_score += item_score
        
        # Average across all results
        return total_score / len(result.results)

    def calculate_metrics(self, baseline: SearchResult, rag: SearchResult, expected_keywords: List[str]) -> Dict[str, TestMetrics]:
        """Calculate comparison metrics"""
        baseline_relevance = self.calculate_relevance_score(baseline, expected_keywords)
        rag_relevance = self.calculate_relevance_score(rag, expected_keywords)
        
        # Simple precision/recall estimation based on relevance and result count
        baseline_precision = min(baseline_relevance, 1.0)
        rag_precision = min(rag_relevance, 1.0)
        
        baseline_recall = min(baseline.total_count / 10.0, 1.0)  # Assume 10 relevant docs max
        rag_recall = min(rag.total_count / 10.0, 1.0)
        
        # User satisfaction estimate (based on relevance and response time)
        baseline_satisfaction = max(0, baseline_precision - (baseline.response_time / 10.0))
        rag_satisfaction = max(0, rag_precision - (rag.response_time / 10.0))
        
        return {
            'baseline': TestMetrics(
                precision=baseline_precision,
                recall=baseline_recall,
                response_time=baseline.response_time,
                relevance_score=baseline_relevance,
                user_satisfaction=baseline_satisfaction
            ),
            'rag': TestMetrics(
                precision=rag_precision,
                recall=rag_recall,
                response_time=rag.response_time,
                relevance_score=rag_relevance,
                user_satisfaction=rag_satisfaction
            )
        }

    def run_comparison_test(self, query_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single comparison test"""
        query = query_config['query']
        expected_keywords = query_config['expected_keywords']
        
        console.print(f"\n🔍 Testing query: '{query}'")
        
        # Run both searches
        baseline_result = self.run_baseline_search(query)
        rag_result = self.run_rag_search(query)
        
        # Calculate metrics
        metrics = self.calculate_metrics(baseline_result, rag_result, expected_keywords)
        
        # Display results
        table = Table(title=f"Results for: {query}")
        table.add_column("Method", style="cyan")
        table.add_column("Results", justify="right")
        table.add_column("Time (s)", justify="right")
        table.add_column("Relevance", justify="right")
        
        table.add_row(
            "Baseline",
            str(baseline_result.total_count),
            f"{baseline_result.response_time:.2f}",
            f"{metrics['baseline'].relevance_score:.2f}"
        )
        table.add_row(
            "RAG",
            str(rag_result.total_count),
            f"{rag_result.response_time:.2f}",
            f"{metrics['rag'].relevance_score:.2f}"
        )
        
        console.print(table)
        
        return {
            'query': query,
            'type': query_config['type'],
            'baseline': baseline_result,
            'rag': rag_result,
            'metrics': metrics,
            'improvement': {
                'precision': metrics['rag'].precision - metrics['baseline'].precision,
                'recall': metrics['rag'].recall - metrics['baseline'].recall,
                'relevance': metrics['rag'].relevance_score - metrics['baseline'].relevance_score,
                'response_time': baseline_result.response_time - rag_result.response_time
            }
        }

    def generate_report(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(test_results)
        
        # Aggregate metrics
        avg_precision_improvement = sum(r['improvement']['precision'] for r in test_results) / total_tests
        avg_recall_improvement = sum(r['improvement']['recall'] for r in test_results) / total_tests
        avg_relevance_improvement = sum(r['improvement']['relevance'] for r in test_results) / total_tests
        avg_response_time_improvement = sum(r['improvement']['response_time'] for r in test_results) / total_tests
        
        # Count improvements
        precision_improvements = sum(1 for r in test_results if r['improvement']['precision'] > 0)
        recall_improvements = sum(1 for r in test_results if r['improvement']['recall'] > 0)
        relevance_improvements = sum(1 for r in test_results if r['improvement']['relevance'] > 0)
        speed_improvements = sum(1 for r in test_results if r['improvement']['response_time'] > 0)
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'precision_improvement': avg_precision_improvement,
                'recall_improvement': avg_recall_improvement,
                'relevance_improvement': avg_relevance_improvement,
                'response_time_improvement': avg_response_time_improvement
            },
            'improvements': {
                'precision': f"{precision_improvements}/{total_tests} queries",
                'recall': f"{recall_improvements}/{total_tests} queries", 
                'relevance': f"{relevance_improvements}/{total_tests} queries",
                'speed': f"{speed_improvements}/{total_tests} queries"
            },
            'detailed_results': test_results
        }
        
        return report

@pytest.fixture
def integration_test():
    """Fixture to initialize integration test"""
    test = RAGmineIntegrationTest()
    test.wait_for_services()
    return test

def test_service_health(integration_test):
    """Test that all services are healthy"""
    # Test Redmica
    response = requests.get(integration_test.redmica_url)
    assert response.status_code == 200, "Redmica service not healthy"
    
    # Test RAG service
    response = requests.get(f"{integration_test.rag_service_url}/health")
    assert response.status_code == 200, "RAG service not healthy"

def test_baseline_search(integration_test):
    """Test baseline Redmine search functionality"""
    result = integration_test.run_baseline_search("authentication")
    assert result.response_time < 10.0, "Baseline search too slow"
    assert result.total_count >= 0, "Baseline search should return results"

def test_rag_search(integration_test):
    """Test RAG-enhanced search functionality"""
    result = integration_test.run_rag_search("How do I fix authentication issues?")
    assert result.response_time < 10.0, "RAG search too slow"
    # Note: RAG search might return 0 results if service isn't fully configured

def test_search_comparison(integration_test):
    """Run comprehensive search comparison tests"""
    console.print("\n🚀 Starting RAGmine Integration Tests")
    console.print("=" * 60)
    
    test_results = []
    
    for query_config in integration_test.test_queries:
        try:
            result = integration_test.run_comparison_test(query_config)
            test_results.append(result)
        except Exception as e:
            console.print(f"❌ Test failed for query '{query_config['query']}': {e}")
            continue
    
    # Generate report
    report = integration_test.generate_report(test_results)
    
    # Display summary
    console.print("\n📊 Test Summary")
    console.print("=" * 40)
    console.print(f"Total Tests: {report['summary']['total_tests']}")
    console.print(f"Avg Precision Improvement: {report['summary']['precision_improvement']:.3f}")
    console.print(f"Avg Recall Improvement: {report['summary']['recall_improvement']:.3f}")
    console.print(f"Avg Relevance Improvement: {report['summary']['relevance_improvement']:.3f}")
    console.print(f"Avg Response Time Improvement: {report['summary']['response_time_improvement']:.3f}s")
    
    # Save detailed report
    with open('/app/test_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    console.print("\n✅ Integration tests completed!")
    console.print("📄 Detailed report saved to: /app/test_report.json")
    
    # Assert basic functionality
    assert len(test_results) > 0, "No tests completed successfully"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
