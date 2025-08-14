#!/usr/bin/env python3
"""
RAGmine Test Data Loader

Loads structured test data into Redmica for integration testing.
Supports before/after comparison by creating consistent test scenarios.
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import click

console = Console()

class TestDataLoader:
    def __init__(self, redmica_url: str, redmica_api_key: str, rag_service_url: str, rag_api_key: str):
        self.redmica_url = redmica_url.rstrip('/')
        self.redmica_api_key = redmica_api_key
        self.rag_service_url = rag_service_url.rstrip('/')
        self.rag_api_key = rag_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-Redmine-API-Key': redmica_api_key,
            'Content-Type': 'application/json'
        })

    def wait_for_services(self):
        """Wait for Redmica and RAG service to be ready"""
        console.print("🔍 Waiting for services to be ready...")
        
        services = [
            (self.redmica_url, "Redmica"),
            (f"{self.rag_service_url}/health", "RAG Service")
        ]
        
        for url, name in services:
            while True:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        console.print(f"✅ {name} is ready")
                        break
                except requests.exceptions.RequestException:
                    console.print(f"⏳ Waiting for {name}...")
                    time.sleep(5)

    def create_test_project(self) -> Dict[str, Any]:
        """Create a test project for RAGmine testing"""
        project_data = {
            "project": {
                "name": "RAGmine Integration Test",
                "identifier": "ragmine-test",
                "description": "Test project for RAGmine search capabilities",
                "is_public": True,
                "enabled_module_names": ["issue_tracking", "wiki", "documents", "files"]
            }
        }
        
        response = self.session.post(f"{self.redmica_url}/projects.json", json=project_data)
        if response.status_code == 201:
            project = response.json()['project']
            console.print(f"✅ Created test project: {project['name']} (ID: {project['id']})")
            return project
        elif response.status_code == 422:
            # Project might already exist
            response = self.session.get(f"{self.redmica_url}/projects/ragmine-test.json")
            if response.status_code == 200:
                project = response.json()['project']
                console.print(f"📋 Using existing test project: {project['name']} (ID: {project['id']})")
                return project
        
        raise Exception(f"Failed to create/get test project: {response.status_code} - {response.text}")

    def load_test_issues(self, project_id: int) -> List[Dict[str, Any]]:
        """Load test issues from JSON files"""
        issues_dir = Path("data/issues")
        created_issues = []
        
        if not issues_dir.exists():
            console.print("⚠️ No issues directory found, creating sample issues...")
            return self.create_sample_issues(project_id)
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Loading test issues...", total=None)
            
            for issue_file in issues_dir.glob("*.json"):
                with open(issue_file) as f:
                    issue_data = json.load(f)
                
                # Adapt to Redmine API format
                redmine_issue = {
                    "issue": {
                        "project_id": project_id,
                        "subject": issue_data["subject"],
                        "description": issue_data["description"],
                        "priority_id": self.get_priority_id(issue_data.get("priority", "Normal")),
                        "status_id": 1,  # New
                        "tracker_id": 1  # Bug/Feature
                    }
                }
                
                response = self.session.post(f"{self.redmica_url}/issues.json", json=redmine_issue)
                if response.status_code == 201:
                    created_issue = response.json()['issue']
                    created_issues.append(created_issue)
                    progress.update(task, description=f"Created issue: {created_issue['subject'][:50]}...")
                else:
                    console.print(f"❌ Failed to create issue: {issue_data['subject']}")
        
        console.print(f"✅ Created {len(created_issues)} test issues")
        return created_issues

    def create_sample_issues(self, project_id: int) -> List[Dict[str, Any]]:
        """Create sample issues for testing"""
        sample_issues = [
            {
                "subject": "API Authentication Timeout Issues",
                "description": """Users are experiencing timeout errors when authenticating via API.
                
**Symptoms:**
- 504 Gateway Timeout errors
- Authentication requests taking >30 seconds
- Intermittent failures during peak hours

**Environment:**
- Production API server
- Nginx reverse proxy
- Redis session store

**Steps to Reproduce:**
1. Make API call to /auth/login
2. Wait for response
3. Timeout occurs after 30 seconds

**Expected:** Authentication should complete within 5 seconds
**Actual:** Request times out

**Additional Info:**
This seems to correlate with high Redis memory usage during peak hours.""",
                "priority": "High",
                "tags": ["api", "authentication", "timeout", "nginx", "redis"]
            },
            {
                "subject": "Database Query Performance Degradation",
                "description": """Search queries are running significantly slower than expected.
                
**Performance Metrics:**
- Simple searches: 2-5 seconds (was <1 second)
- Complex searches: 10-15 seconds (was 2-3 seconds)
- Database CPU usage: 80-90% (was 20-30%)

**Investigation:**
- Query execution plans show table scans
- Missing indexes on search columns
- Statistics need updating

**Proposed Solution:**
1. Add composite indexes on frequently searched columns
2. Update table statistics
3. Implement query result caching

**Impact:** All users experiencing slow search performance""",
                "priority": "High",
                "tags": ["database", "performance", "search", "indexing"]
            },
            {
                "subject": "Implement Advanced Search Filters",
                "description": """Add advanced filtering capabilities to the search interface.
                
**Requirements:**
- Date range filtering
- User/author filtering  
- Project-specific search
- Content type filtering (issues, wiki, documents)
- Tag-based filtering

**UI Mockup:**
Advanced search form with collapsible sections for each filter type.

**Technical Considerations:**
- Backend API changes needed
- Frontend JavaScript for dynamic filters
- Database query optimization
- Caching strategy for filtered results

**Acceptance Criteria:**
- [ ] Date range picker working
- [ ] User dropdown populated
- [ ] Project filter respects permissions
- [ ] Results update dynamically
- [ ] Performance remains acceptable (<2s)""",
                "priority": "Normal",
                "tags": ["feature", "search", "ui", "filters"]
            }
        ]
        
        created_issues = []
        for issue_data in sample_issues:
            redmine_issue = {
                "issue": {
                    "project_id": project_id,
                    "subject": issue_data["subject"],
                    "description": issue_data["description"],
                    "priority_id": self.get_priority_id(issue_data["priority"]),
                    "status_id": 1,
                    "tracker_id": 1
                }
            }
            
            response = self.session.post(f"{self.redmica_url}/issues.json", json=redmine_issue)
            if response.status_code == 201:
                created_issues.append(response.json()['issue'])
        
        console.print(f"✅ Created {len(created_issues)} sample issues")
        return created_issues

    def load_wiki_pages(self, project_id: int) -> List[Dict[str, Any]]:
        """Load test wiki pages"""
        wiki_pages = [
            {
                "title": "API_Documentation",
                "text": """# API Documentation

## Authentication

All API requests require authentication using an API key.

### Getting an API Key
1. Log into your account
2. Go to Account Settings
3. Click "Show API Key"
4. Copy the key for use in requests

### Using the API Key
Include the key in the `X-Redmine-API-Key` header:

```bash
curl -H "X-Redmine-API-Key: YOUR_KEY_HERE" \\
     https://api.example.com/issues.json
```

## Common Endpoints

### Issues
- `GET /issues.json` - List issues
- `POST /issues.json` - Create issue
- `GET /issues/{id}.json` - Get specific issue
- `PUT /issues/{id}.json` - Update issue

### Projects
- `GET /projects.json` - List projects
- `GET /projects/{id}.json` - Get project details

## Error Handling

The API returns standard HTTP status codes:
- 200: Success
- 401: Unauthorized (invalid API key)
- 404: Not found
- 422: Validation error
- 500: Server error

## Rate Limiting

API requests are limited to 100 requests per minute per API key."""
            },
            {
                "title": "Troubleshooting_Guide",
                "text": """# Troubleshooting Guide

## Common Issues

### Authentication Problems

**Symptom:** 401 Unauthorized errors
**Causes:**
- Invalid API key
- Expired session
- Insufficient permissions

**Solutions:**
1. Verify API key is correct
2. Check user permissions
3. Try regenerating API key

### Performance Issues

**Symptom:** Slow response times
**Causes:**
- Database performance
- Network latency
- Server overload

**Solutions:**
1. Check database query performance
2. Monitor server resources
3. Implement caching
4. Optimize database indexes

### Search Not Working

**Symptom:** No search results or errors
**Causes:**
- Index corruption
- Database issues
- Permission problems

**Solutions:**
1. Rebuild search index
2. Check database connectivity
3. Verify user permissions
4. Clear application cache

## Getting Help

1. Check the logs for error messages
2. Search the knowledge base
3. Contact support with:
   - Error message
   - Steps to reproduce
   - System information"""
            }
        ]
        
        created_pages = []
        project_identifier = "ragmine-test"
        
        for page_data in wiki_pages:
            wiki_data = {
                "wiki_page": {
                    "text": page_data["text"]
                }
            }
            
            url = f"{self.redmica_url}/projects/{project_identifier}/wiki/{page_data['title']}.json"
            response = self.session.put(url, json=wiki_data)
            
            if response.status_code in [200, 201]:
                created_pages.append(page_data)
                console.print(f"✅ Created wiki page: {page_data['title']}")
            else:
                console.print(f"❌ Failed to create wiki page: {page_data['title']}")
        
        return created_pages

    def get_priority_id(self, priority_name: str) -> int:
        """Map priority names to IDs"""
        priority_map = {
            "Low": 1,
            "Normal": 2,
            "High": 3,
            "Urgent": 4,
            "Immediate": 5
        }
        return priority_map.get(priority_name, 2)

    def trigger_rag_indexing(self):
        """Trigger RAG service to index the loaded content"""
        try:
            headers = {"Authorization": f"Bearer {self.rag_api_key}"}
            response = requests.post(
                f"{self.rag_service_url}/index/rebuild",
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                console.print("✅ RAG indexing triggered successfully")
            else:
                console.print(f"⚠️ RAG indexing failed: {response.status_code}")
        except Exception as e:
            console.print(f"⚠️ Could not trigger RAG indexing: {e}")

@click.command()
@click.option('--redmica-url', default=lambda: os.getenv('REDMICA_URL', 'http://localhost:3000'))
@click.option('--redmica-api-key', default=lambda: os.getenv('REDMICA_API_KEY', 'admin_api_key'))
@click.option('--rag-service-url', default=lambda: os.getenv('RAG_SERVICE_URL', 'http://localhost:8000'))
@click.option('--rag-api-key', default=lambda: os.getenv('RAG_API_KEY', 'dev-test-key-12345'))
def main(redmica_url, redmica_api_key, rag_service_url, rag_api_key):
    """Load test data for RAGmine integration testing"""
    console.print("🚀 Starting RAGmine test data loading...")
    
    loader = TestDataLoader(redmica_url, redmica_api_key, rag_service_url, rag_api_key)
    
    try:
        # Wait for services
        loader.wait_for_services()
        
        # Create test project
        project = loader.create_test_project()
        
        # Load test data
        issues = loader.load_test_issues(project['id'])
        wiki_pages = loader.load_wiki_pages(project['id'])
        
        # Trigger RAG indexing
        time.sleep(5)  # Give Redmica time to process
        loader.trigger_rag_indexing()
        
        console.print("\n✅ Test data loading completed successfully!")
        console.print(f"📊 Summary:")
        console.print(f"   - Project: {project['name']} (ID: {project['id']})")
        console.print(f"   - Issues: {len(issues)}")
        console.print(f"   - Wiki Pages: {len(wiki_pages)}")
        console.print(f"\n🔗 Access the test project at: {redmica_url}/projects/ragmine-test")
        
    except Exception as e:
        console.print(f"❌ Error loading test data: {e}")
        raise

if __name__ == "__main__":
    main()
