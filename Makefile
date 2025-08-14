# Ragmine Development Makefile

.PHONY: help setup install test clean docker-up docker-down index lint format

# Default target
help:
	@echo "Ragmine Development Commands:"
	@echo "  make setup       - Initial setup of development environment"
	@echo "  make install     - Install all dependencies"
	@echo "  make test        - Run RAG service unit tests"
	@echo "  make test-rag    - Run RAG-only stack integration tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make docker-up   - Start full Docker services"
	@echo "  make docker-down - Stop Docker services"
	@echo "  make rag-up      - Start RAG-only stack"
	@echo "  make rag-down    - Stop RAG-only stack"
	@echo "  make index       - Run full indexing"
	@echo "  make clean       - Clean temporary files"
	@echo "  make release     - Build release package"

# Setup development environment
setup:
	@echo "Setting up Ragmine development environment..."
	./setup.sh
	make install
	make docker-up
	@echo "Setup complete! 🎉"

# Install dependencies
install:
	@echo "Installing Ruby dependencies..."
	bundle install
	@echo "Installing Python dependencies..."
	cd rag_service && pip install -r requirements.txt
	@echo "Dependencies installed!"

# Run tests
test:
	@echo "Running RAG service unit tests..."
	cd rag_service && pip install -r requirements-test.txt && pytest tests/ -v --cov=.
	@echo "All tests completed!"

# Run RAG-only stack tests
test-rag:
	@echo "Starting RAG-only stack for testing..."
	docker compose -f docker-compose.rag-only.yml up -d
	@echo "Waiting for services to be ready..."
	@timeout 120s bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done'
	@echo "Running integration tests..."
	@curl -f http://localhost:8000/health
	@curl -X POST "http://localhost:8000/search" -H "Content-Type: application/json" -d '{"query": "API authentication timeout"}' | jq '.results | length'
	@curl -X POST "http://localhost:8000/index/rebuild" | jq '.status'
	@echo "RAG stack tests completed!"
	docker compose -f docker-compose.rag-only.yml down

# Run linters
lint:
	@echo "Running Ruby linter..."
	bundle exec rubocop
	@echo "Running Python linter..."
	cd rag_service && flake8 .
	@echo "Linting complete!"

# Format code
format:
	@echo "Formatting Ruby code..."
	bundle exec rubocop -a
	@echo "Formatting Python code..."
	cd rag_service && black .
	@echo "Formatting complete!"

# Start Docker services
docker-up:
	@echo "Starting Docker services..."
	docker compose up -d
	@echo "Services started!"

# Stop Docker services
docker-down:
	@echo "Stopping Docker services..."
	docker compose down
	@echo "Services stopped!"

# Start RAG-only stack
rag-up:
	@echo "Starting RAG-only stack..."
	docker compose -f docker-compose.rag-only.yml up -d
	@echo "RAG stack started!"
	@echo "Services available at:"
	@echo "  - RAG Service: http://localhost:8000"
	@echo "  - Qdrant: http://localhost:6333"
	@echo "  - Redis: localhost:6379"

# Stop RAG-only stack
rag-down:
	@echo "Stopping RAG-only stack..."
	docker compose -f docker-compose.rag-only.yml down
	@echo "RAG stack stopped!"

docker-logs:
	docker compose logs -f

docker-restart:
	make docker-down
	make docker-up

# Indexing
index:
	@echo "Running full document indexing..."
	bundle exec rake ragmine:index_all
	@echo "Indexing complete!"

reindex:
	@echo "Clearing index..."
	bundle exec rake ragmine:clear_index
	@echo "Running full reindex..."
	bundle exec rake ragmine:index_all
	@echo "Reindexing complete!"

# Database operations
migrate:
	bundle exec rake redmine:plugins:migrate NAME=ragmine

rollback:
	bundle exec rake redmine:plugins:migrate NAME=ragmine VERSION=0

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	rm -rf tmp/*
	rm -rf log/*.log
	rm -rf rag_service/__pycache__
	rm -rf rag_service/.pytest_cache
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete
	@echo "Cleanup complete!"

# Development server
dev:
	@echo "Starting development servers..."
	@echo "Starting Redmine..."
	bundle exec rails server -p 3000 &
	@echo "Starting RAG service..."
	cd rag_service && uvicorn app:app --reload --port 8000 &
	@echo "Development servers running!"
	@echo "Press Ctrl+C to stop"
	wait

# Build release package
release:
	@echo "Building release package..."
	@echo "Running tests..."
	make test
	@echo "Creating archive..."
	tar -czf ragmine-$(shell grep version init.rb | cut -d"'" -f2).tar.gz \
		--exclude='.git' \
		--exclude='*.log' \
		--exclude='tmp/*' \
		--exclude='__pycache__' \
		--exclude='.pytest_cache' \
		--exclude='venv' \
		--exclude='node_modules' \
		.
	@echo "Release package created!"

# Check service health
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "RAG service not responding"
	@curl -s http://localhost:6333/collections | jq . || echo "Qdrant not responding"
	@redis-cli ping || echo "Redis not responding"

# Show current status
status:
	@echo "=== Ragmine Status ==="
	@echo "Plugin Version: $(shell grep version init.rb | cut -d"'" -f2)"
	@echo "Services:"
	@docker-compose ps
	@echo ""
	@echo "Recent Searches:"
	@bundle exec rails runner "puts RagQuery.order(created_at: :desc).limit(5).pluck(:query)"

# Development console
console:
	bundle exec rails console

# Python shell with service context
shell:
	cd rag_service && python -i -c "from app import *; print('RAG Service shell loaded')"

# Watch for file changes and restart
watch:
	@echo "Watching for changes..."
	fswatch -o . | xargs -n1 -I{} make docker-restart

# Generate documentation
docs:
	@echo "Generating documentation..."
	yard doc
	cd rag_service && pdoc --html --output-dir docs .
	@echo "Documentation generated!"

# Update dependencies
update:
	@echo "Updating Ruby dependencies..."
	bundle update
	@echo "Updating Python dependencies..."
	cd rag_service && pip install --upgrade -r requirements.txt
	@echo "Dependencies updated!"
